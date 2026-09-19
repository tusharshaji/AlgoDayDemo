"""Shared helpers used by the reference strategies (organiser demos)."""
import numpy as np

GROSS = 1_000_000.0


def zscore(x):
    x = np.asarray(x, dtype=float)
    sd = x.std()
    return (x - x.mean()) / (sd + 1e-12)


def sector_neutralise(signal, sectors):
    """Subtract the sector mean, so we are not making a sector bet."""
    out = np.asarray(signal, dtype=float).copy()
    for s in np.unique(sectors):
        m = sectors == s
        out[m] -= out[m].mean()
    return out - out.mean()


def to_dollars(signal, gross=GROSS):
    """Scale a signal to use the full gross budget, dollar neutral."""
    s = np.asarray(signal, dtype=float)
    s = s - s.mean()
    denom = np.abs(s).sum()
    if denom < 1e-12:
        return np.zeros_like(s)
    return s / denom * gross


def smooth(new, old, alpha=0.35):
    """Blend toward the new target to cut turnover (and commission)."""
    return alpha * new + (1.0 - alpha) * old


def top_bottom(signal, frac=0.25):
    """
    Keep only the strongest longs and shorts, zero the middle.

    Spreading a $1M book evenly over 50 names when only 20 of them carry any
    signal wastes most of the risk budget. Concentrating raises the return per
    dollar traded, which is what makes a fast signal survive commission.
    """
    s = np.asarray(signal, dtype=float)
    n = len(s)
    k = max(1, int(round(n * frac)))
    order = np.argsort(s)
    out = np.zeros_like(s)
    out[order[:k]] = s[order[:k]]        # strongest shorts
    out[order[-k:]] = s[order[-k:]]      # strongest longs
    return out


def find_pairs(close, sectors, n_pairs=6, fit_days=400, min_corr=0.80):
    """
    Find cointegrated pairs. Two screens, in this order:
      1. return correlation - genuinely linked names move together day to day
      2. spread half-life   - the spread must actually pull back, fast enough
         to trade but not so fast that it is just noise

    Ranking on half-life alone finds hundreds of spurious pairs. The
    correlation screen is what separates a real link from a coincidence.
    """
    logp = np.log(close[:fit_days])
    rets = np.diff(logp, axis=0)
    corr = np.corrcoef(rets.T)

    cands = []
    for s in np.unique(sectors):
        idx = np.where(sectors == s)[0]
        for i_pos, a in enumerate(idx):
            for b in idx[i_pos + 1:]:
                if corr[a, b] < min_corr:
                    continue
                spread = logp[:, a] - logp[:, b]
                spread = spread - spread.mean()
                x, y = spread[:-1], spread[1:]
                rho = float(x @ y / (x @ x + 1e-12))
                if not (0.0 < rho < 0.999):
                    continue
                hl = -np.log(2) / np.log(rho)
                if 3 < hl < 45:
                    cands.append((corr[a, b], int(a), int(b)))
    cands.sort(key=lambda c: -c[0])
    return [(a, b) for _, a, b in cands[:n_pairs]]


def pair_signal(close, pairs, n_inst, lookback=90):
    """Z-score of each pair spread, as a per-instrument signal."""
    logp = np.log(close[-lookback:])
    sig = np.zeros(n_inst)
    for a, b in pairs:
        spread = logp[:, a] - logp[:, b]
        z = np.clip((spread[-1] - spread.mean()) / (spread.std() + 1e-9), -3, 3)
        sig[a] -= z
        sig[b] += z
    return sig
