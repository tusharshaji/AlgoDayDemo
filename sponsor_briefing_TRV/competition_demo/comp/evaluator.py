"""
PUBLIC. The evaluator.

This is the organiser's scoring engine. Local and organiser runs match when
given the same data and deterministic strategy.

Usage
-----
    python -m comp.evaluator strategies/baseline_reversal.py
    python -m comp.evaluator my_strategy.py --start 500

How the backtest works
----------------------
For each day t we hand your function a Context holding every price up to and
including the close of day t, and nothing after it. You return the dollar
position you want to hold in each instrument. We then:

    1. uniformly scale your request to the position limits
    2. charge commission on the dollars you traded to get there
    3. hold that book overnight and earn the day t -> t+1 return

The key convention: you decide using data through the close of day t, and you
earn the move from t to t+1. You never trade on a price you have already been
paid for.
"""
from __future__ import annotations

import argparse
import importlib.util
import operator
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import config as C


# --------------------------------------------------------------------------
# What your strategy sees
# --------------------------------------------------------------------------
@dataclass
class Context:
    """
    Everything you are allowed to know on day `day`.

    close     (day+1, n_inst)  prices through today's close
    volume    (day+1, n_inst)  share volume through today
    sectors   (n_inst,)        integer sector id, same ids as metadata.csv
    positions (n_inst,)        the dollar book you are currently holding
    day       int              index of today within the full price history
    n_inst    int
    """
    close: np.ndarray
    volume: np.ndarray
    sectors: np.ndarray
    positions: np.ndarray
    day: int
    n_inst: int

    # ---- convenience helpers, so teams do not burn their afternoon on numpy
    def _lookback(self, lookback):
        if lookback is None:
            return self.close
        lookback = _integer(lookback, "lookback")
        if not 1 <= lookback < len(self.close):
            raise ValueError(f"lookback must be between 1 and {len(self.close) - 1}")
        return self.close[-(lookback + 1):]

    def returns(self, lookback: int | None = None) -> np.ndarray:
        """Simple daily returns, shape (days-1, n_inst)."""
        px = self._lookback(lookback)
        return px[1:] / px[:-1] - 1.0

    def log_returns(self, lookback: int | None = None) -> np.ndarray:
        px = self._lookback(lookback)
        return np.diff(np.log(px), axis=0)

    def trailing_return(self, lookback: int) -> np.ndarray:
        """Total return over the last `lookback` days, shape (n_inst,)."""
        px = self._lookback(lookback)
        return px[-1] / px[0] - 1.0

    def volatility(self, lookback: int = 60) -> np.ndarray:
        """Daily return stdev over the last `lookback` days, shape (n_inst,)."""
        return self.returns(lookback).std(axis=0) + 1e-12


# --------------------------------------------------------------------------
# Position limits
# --------------------------------------------------------------------------
def _integer(value, name):
    try:
        if isinstance(value, (bool, np.bool_)):
            raise TypeError
        return operator.index(value)
    except TypeError:
        raise ValueError(f"{name} must be an integer") from None


def validate_market(close, volume, sectors):
    """Validate the shared array contract before calling participant code."""
    close = np.asarray(close, dtype=float)
    volume = np.asarray(volume, dtype=float)
    sectors = np.asarray(sectors)
    if close.ndim != 2 or close.shape[0] < 3 or close.shape[1] < 1:
        raise ValueError("prices must have shape (at least 3 days, instruments)")
    if volume.shape != close.shape:
        raise ValueError("volume must have the same shape as prices")
    if not np.isfinite(close).all() or (close <= 0).any():
        raise ValueError("prices must be finite and strictly positive")
    if not np.isfinite(volume).all() or (volume < 0).any():
        raise ValueError("volume must be finite and non-negative")
    if (sectors.shape != (close.shape[1],) or sectors.dtype.kind not in "iu"
            or (sectors < 0).any()):
        raise ValueError("sectors must contain one non-negative integer per instrument")
    return close, volume, sectors


def apply_limits(target: np.ndarray) -> tuple[np.ndarray, dict]:
    """
    Force a requested book inside the limits.

    Use one common scale factor, preserving signs, zeros and relative weights.
    Non-finite entries become zero and are reported. Malformed shapes are errors.
    Normalise before summing so even near-float-max requests cannot overflow.
    """
    raw = np.asarray(target, dtype=float)
    if raw.ndim != 1 or not raw.size:
        raise ValueError("positions must be a non-empty one-dimensional array")
    invalid = int((~np.isfinite(raw)).sum())
    x = np.nan_to_num(raw, nan=0.0,
                      posinf=0.0, neginf=0.0)
    with np.errstate(over="ignore"):
        requested_gross = float(np.abs(x).sum())
    largest = float(np.abs(x).max())
    scaled = False
    if largest:
        unit = x / largest
        unit_net = abs(float(unit.sum()))
        allowed = min(C.CONCENTRATION_LIMIT, C.GROSS_LIMIT / np.abs(unit).sum(),
                      C.NET_LIMIT / unit_net if unit_net else float("inf"))
        if largest > allowed:
            x = unit * allowed
            scaled = True

    info = dict(
        requested_gross=requested_gross,
        final_gross=float(np.abs(x).sum()),
        final_net=float(x.sum()),
        scaled=scaled,
        invalid_entries=invalid,
    )
    return x, info


# --------------------------------------------------------------------------
# The backtest
# --------------------------------------------------------------------------
def run_backtest(strategy_fn, close: np.ndarray, volume: np.ndarray,
                 sectors: np.ndarray, start: int | None = None,
                 end: int | None = None, collect_book: bool = False,
                 time_limit: float | None = None) -> dict:
    """
    Replay the market day by day.

    close/volume : (n_days, n_inst)
    start        : first day the strategy is called (default C.WARMUP_DAYS)
    end          : last day the strategy is called (default n_days - 2)

    Starts flat. Positions drift with prices overnight; turnover is measured
    against those marked-to-market holdings. Limits apply after each rebalance.
    The final book is marked to market, not liquidated. History before start is
    available, but strategy_fn is not called on it. This in-process helper's
    deadline is cooperative; the final runner enforces a process deadline.
    """
    close, volume, sectors = validate_market(close, volume, sectors)
    n_days, n_inst = close.shape
    start = C.WARMUP_DAYS if start is None else _integer(start, "start")
    end = (n_days - 2) if end is None else _integer(end, "end")
    if not 1 <= start <= end <= n_days - 2:
        raise ValueError(f"require 1 <= start <= end <= {n_days - 2}")
    if time_limit is not None and (not np.isfinite(time_limit) or time_limit <= 0):
        raise ValueError("time_limit must be finite and positive")

    rets = close[1:] / close[:-1] - 1.0          # rets[t] is the t -> t+1 move
    if not np.isfinite(rets).all():
        raise ValueError("prices produce non-finite returns")

    held = np.zeros(n_inst)
    n_steps = end - start + 1
    pnl = np.zeros(n_steps)
    costs = np.zeros(n_steps)
    gross = np.zeros(n_steps)
    net = np.zeros(n_steps)
    turnover = np.zeros(n_steps)
    n_scaled = 0
    n_invalid = 0
    books = [] if collect_book else None

    t0 = time.perf_counter()
    for k, t in enumerate(range(start, end + 1)):
        ctx = Context(
            close=close[:t + 1].copy(),
            volume=volume[:t + 1].copy(),
            sectors=sectors.copy(),
            positions=held.copy(),
            day=t,
            n_inst=n_inst,
        )
        raw = strategy_fn(ctx)
        raw = np.asarray(raw, dtype=float)
        if raw.shape != (n_inst,):
            raise ValueError(
                f"day {t}: strategy returned shape {raw.shape}, expected ({n_inst},)")

        target, info = apply_limits(raw)
        n_scaled += int(info["scaled"])
        n_invalid += info["invalid_entries"]

        traded = np.abs(target - held).sum()
        cost = traded * C.COMMISSION_BPS * 1e-4
        held = target

        pnl[k] = float(held @ rets[t]) - cost
        costs[k] = cost
        turnover[k] = traded
        gross[k] = info["final_gross"]
        net[k] = info["final_net"]
        if collect_book:
            books.append(held.copy())
        # Same shares, new prices. Keeping target dollars tomorrow is a trade.
        held = target * (1.0 + rets[t])

        if time_limit is not None and (time.perf_counter() - t0) > time_limit:
            raise TimeoutError(
                f"backtest exceeded {time_limit:.0f}s at day {t}")

    elapsed = time.perf_counter() - t0
    out = dict(
        pnl=pnl, costs=costs, gross=gross, net=net, turnover=turnover,
        equity=np.cumsum(pnl), days=np.arange(start, end + 1),
        n_scaled=n_scaled, n_invalid=n_invalid, elapsed=elapsed,
    )
    if collect_book:
        out["book"] = np.array(books)
    out.update(metrics(pnl, costs, turnover, gross))
    return out


# --------------------------------------------------------------------------
# Metrics and score
# --------------------------------------------------------------------------
def metrics(pnl: np.ndarray, costs: np.ndarray | None = None,
            turnover: np.ndarray | None = None,
            gross: np.ndarray | None = None) -> dict:
    pnl = np.asarray(pnl, dtype=float)
    if pnl.ndim != 1 or not len(pnl) or not np.isfinite(pnl).all():
        raise ValueError("pnl must be a non-empty finite one-dimensional array")
    optional = []
    for name, values in (("costs", costs), ("turnover", turnover), ("gross", gross)):
        if values is not None:
            values = np.asarray(values, dtype=float)
            if (values.shape != pnl.shape or not np.isfinite(values).all()
                    or (values < 0).any()):
                raise ValueError(f"{name} must match pnl and be finite and non-negative")
        optional.append(values)
    costs, turnover, gross = optional
    n = len(pnl)
    mean_d = float(pnl.mean())
    sd_d = float(pnl.std(ddof=1)) if n > 1 else 0.0

    ann_pnl = mean_d * C.TRADING_DAYS_PER_YEAR
    ann_vol = sd_d * np.sqrt(C.TRADING_DAYS_PER_YEAR)
    # A fixed dollar volatility floor avoids both undefined constant-P&L
    # ratios and unbounded scores from numerical near-zero variation.
    sharpe = float(mean_d / max(sd_d, C.SHARPE_DAILY_VOL_FLOOR)
                   * np.sqrt(C.TRADING_DAYS_PER_YEAR)) if n > 1 else 0.0

    equity = np.cumsum(pnl)
    peak = np.maximum.accumulate(np.concatenate([[0.0], equity]))[1:]
    dd = peak - equity
    max_dd = float(dd.max()) if n else 0.0
    dd_frac = max_dd / C.GROSS_LIMIT

    # Score: Sharpe, knocked down by two things.
    #   1. drawdown  - how deep the worst peak-to-trough loss went
    #   2. utilisation - Sharpe is scale free, so a team trading $50k of the
    #      $1M budget would otherwise score the same as one running the full
    #      book while taking a twentieth of the risk. Deploy the budget.
    # Neither penalty applies to a losing strategy: we do not reward a bad
    # strategy for also being timid.
    dd_penalty = 1.0 - min(1.0, dd_frac / C.DRAWDOWN_CAP)
    util = 1.0
    if gross is not None and len(gross):
        util = min(1.0, float(gross.mean()) / C.MIN_AVG_GROSS)
    score = sharpe * dd_penalty * util if sharpe > 0 else sharpe

    out = dict(
        total_pnl=float(equity[-1]) if n else 0.0,
        ann_pnl=float(ann_pnl),
        ann_vol=float(ann_vol),
        sharpe=sharpe,
        max_drawdown=max_dd,
        dd_frac=float(dd_frac),
        calmar=float(ann_pnl / max_dd) if max_dd > 0 else float("inf"),
        hit_rate=float((pnl > 0).mean()) if n else 0.0,
        dd_penalty=float(dd_penalty),
        utilisation=float(util),
        score=float(score),
        n_days=n,
    )
    if costs is not None:
        out["total_costs"] = float(costs.sum())
    if turnover is not None:
        out["ann_turnover"] = float(
            turnover.mean() * C.TRADING_DAYS_PER_YEAR / C.GROSS_LIMIT)
    if gross is not None and len(gross):
        out["avg_gross"] = float(gross.mean())
    return out


# --------------------------------------------------------------------------
# Loading data and strategies
# --------------------------------------------------------------------------
def load_data(data_dir: str | Path = "data"):
    import pandas as pd
    d = Path(data_dir)
    prices = pd.read_csv(d / "prices.csv")
    volumes = pd.read_csv(d / "volumes.csv")
    meta = pd.read_csv(d / "metadata.csv")
    if not {"instrument", "sector_id"}.issubset(meta.columns):
        raise ValueError("metadata must contain instrument and sector_id columns")
    if (list(prices.columns) != list(volumes.columns)
            or list(prices.columns) != meta["instrument"].tolist()
            or meta["instrument"].duplicated().any()):
        raise ValueError("price, volume and metadata instruments must match in order")
    close, volume, sectors = validate_market(
        prices.to_numpy(dtype=float), volumes.to_numpy(dtype=float),
        meta["sector_id"].to_numpy())
    return close, volume, sectors, meta


def load_strategy(path: str | Path):
    """Import a .py file and return its get_positions function."""
    path = Path(path).resolve()
    # Put the strategy's own folder on the path so teams can split their code
    # across several files and still `import my_helpers`.
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    if not callable(getattr(mod, "get_positions", None)):
        raise AttributeError(f"{path} has no get_positions(ctx) function")
    return mod.get_positions


def format_report(res: dict, title: str = "") -> str:
    L = []
    L.append("=" * 62)
    L.append(f"  {title}" if title else "  BACKTEST REPORT")
    L.append("=" * 62)
    L.append(f"  days simulated       {res['n_days']:>14,}")
    L.append(f"  total P&L            {res['total_pnl']:>14,.0f}")
    L.append(f"  annualised P&L       {res['ann_pnl']:>14,.0f}")
    L.append(f"  annualised vol       {res['ann_vol']:>14,.0f}")
    L.append("-" * 62)
    L.append(f"  SHARPE               {res['sharpe']:>14.2f}")
    L.append(f"  max drawdown         {res['max_drawdown']:>14,.0f}"
             f"   ({res['dd_frac'] * 100:.1f}% of gross limit)")
    L.append(f"  calmar               {res['calmar']:>14.2f}")
    L.append(f"  hit rate             {res['hit_rate'] * 100:>13.1f}%")
    L.append("-" * 62)
    L.append(f"  avg gross exposure   {res.get('avg_gross', 0):>14,.0f}"
             f"   (limit {C.GROSS_LIMIT:,.0f})")
    L.append(f"  capital utilisation  {res.get('utilisation', 1) * 100:>13.0f}%"
             f"   (full credit at {C.MIN_AVG_GROSS:,.0f})")
    L.append(f"  ann. turnover        {res.get('ann_turnover', 0):>14.1f}x")
    L.append(f"  total commission     {res.get('total_costs', 0):>14,.0f}")
    L.append(f"  days scaled to fit   {res.get('n_scaled', 0):>14,}")
    L.append(f"  invalid values reset {res.get('n_invalid', 0):>14,}")
    L.append("-" * 62)
    L.append(f"  SCORE                {res['score']:>14.3f}")
    L.append(f"  = {res['sharpe']:.2f} sharpe"
             f"  x {res.get('dd_penalty', 1):.2f} drawdown"
             f"  x {res.get('utilisation', 1):.2f} utilisation"
             if res['sharpe'] > 0 else "  = non-positive Sharpe (penalties do not improve losses)")
    L.append(f"  Final rank uses the {C.SCORE_PERCENTILE}th percentile of this"
             f" score across {C.N_PATHS} futures.")
    L.append(f"  runtime              {res['elapsed']:>14.1f}s"
             f"   (limit {C.MAX_SECONDS_PER_BACKTEST:.0f}s)")
    if "wall_elapsed" in res:
        L.append(f"  process wall time    {res['wall_elapsed']:>14.1f}s")
    L.append("=" * 62)
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Algo Day 26 evaluator")
    ap.add_argument("strategy", help="path to your strategy .py file")
    ap.add_argument("--data", default="data", help="data directory")
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--end", type=int, default=None)
    args = ap.parse_args(argv)

    close, volume, sectors, _ = load_data(args.data)
    from .execution import run_strategy
    res = run_strategy(args.strategy, close, volume, sectors,
                       start=args.start, end=args.end,
                       time_limit=C.MAX_SECONDS_PER_BACKTEST)
    print(format_report(res, Path(args.strategy).name))
    return res


if __name__ == "__main__":
    main()
