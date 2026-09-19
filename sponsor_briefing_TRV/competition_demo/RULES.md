# Algo Day 26 — Rules

You have four hours. Read this page first; it takes three minutes and will save
you one of those hours.

---

## What you're doing

You are running a market-neutral book across 50 instruments. Every day you say
how many dollars you want to hold in each one. We replay history, charge you
for trading, and measure how well you did.

You edit **one function** in **one file**.

```bash
python -m comp.evaluator strategy.py
```

That runs the same scoring engine the organisers use. With the same data and
a deterministic strategy, the scores match. The visualiser is an organiser tool.

---

## What you're given

| File | What's in it |
|---|---|
| `data/prices.csv` | 750 days × 50 instruments of daily closing prices |
| `data/volumes.csv` | matching daily share volume |
| `data/metadata.csv` | which sector each instrument belongs to |
| `comp/evaluator.py` | the scorer — read it, it is the spec |
| `strategy.py` | your file |
| `examples/baseline_*.py` | four worked examples to steal from |

The market is **synthetic**. There is no real ticker behind `INS17`, so there
is nothing to look up. There *are* real, deliberately planted, tradeable
patterns in it. Finding them is the competition.

---

## The function you write

```python
def get_positions(ctx):
    return np.zeros(ctx.n_inst)     # 50 dollar amounts
```

Return **dollars**, not share counts. Positive is long, negative is short.

What `ctx` gives you:

| | |
|---|---|
| `ctx.close` | `(days, 50)` prices up to and including today |
| `ctx.volume` | `(days, 50)` share volume |
| `ctx.sectors` | `(50,)` sector id per instrument |
| `ctx.positions` | `(50,)` the book you're holding right now |
| `ctx.day` | today's index |
| `ctx.returns(n)` | last `n` daily returns, `(n, 50)` |
| `ctx.trailing_return(n)` | total return over the last `n` days, `(50,)` |
| `ctx.volatility(n)` | daily vol over the last `n` days, `(50,)` |

The context contains independent copies of history through today. Changing
them does not change the market. Helpers require a positive integer lookback
with enough available history; otherwise they raise a clear error.

Each backtest starts with no positions. Local tests normally begin on day 60.
Final paths begin at the last close of the sample plus validation history,
then score all 250 future returns. Your function receives the earlier history,
but is not called on those earlier days. Initialise any model or cache on your
first call, even if `ctx.day` is already large.

---

## The limits

| Limit | Value | Meaning |
|---|---|---|
| **Gross** | `sum(abs(positions)) ≤ $1,000,000` | your total risk budget |
| **Net** | `abs(sum(positions)) ≤ $100,000` | stay roughly market-neutral |
| **Concentration** | `abs(position_i) ≤ $100,000` | no single name over 10% |

Break a limit and we **scale every position by the same factor** until all
three limits hold. This preserves your relative weights, signs, and zero
positions. Limits apply immediately after each rebalance; market moves can
change exposures overnight. NaN and infinity entries become zero and are
counted in the report. Wrong-shaped outputs and strategy errors stop the run.

The net limit is the one that catches people. If you just buy all 50
instruments, you get scaled down to a tenth of the budget and score almost
nothing. **To use the full book you have to be balanced long against short.**

---

## What it costs to trade

**3 basis points on every dollar you trade.** A basis point is one hundredth of
a percent, so this is `$300` per `$1,000,000` you move.

That sounds like nothing, and it adds up faster than you'd think. If you
rebalance the whole book every day you'll turn over more than 100× your capital
in a year and pay six figures in commission — often a third to a half of what
you earned before costs.

The evaluator reports `ann. turnover` and `total commission` on every run.
Look at them. If commission is eating most of your gross profit, two one-line
fixes are worth trying:

- **trade less of the book** — concentrate on your strongest signals
- **move partway to your target**, not all the way (`0.3*new + 0.7*old`)

Neither is automatically the right call. Try them and measure — sometimes
trading fast and paying the toll genuinely wins.

Holdings change value with prices. If a $1,000 long rises 10%, tomorrow's
`ctx.positions` contains $1,100 for that position. Returning $1,000 sells $100
and incurs commission; returning the current holding makes no trade (unless
limits require scaling). Short holdings change value with prices in the same
way, retaining their negative sign. Opening trades incur commission. The final
book is valued at the last close without a forced liquidation trade.

This is a simplified daily simulator: decisions using today's close execute
at that close. There is no slippage, financing charge, borrowing charge, or
volume-based execution limit. Volume is available as a research feature.

---

## How you're scored

**Per run:**

```
If Sharpe > 0: score = Sharpe × drawdown penalty × capital utilisation
Otherwise:    score = Sharpe
```

- **Sharpe** — mean daily net P&L divided by the larger of its sample standard
  deviation and **$1 per day**, multiplied by `sqrt(252)`. This small denominator
  floor keeps constant profits/losses finite and correctly signed. Flat P&L or
  fewer than two observations scores zero. Negative Sharpe is not reduced by penalties: taking more risk
  must not improve a losing score.
- **Drawdown penalty** — falls to zero as your worst peak-to-trough loss
  approaches 15% of the gross limit. It is `max(0, 1 - max_drawdown / $150,000)`.
  Drawdown includes losses from the starting value of zero cumulative P&L.
  At the cap, positive scores become zero; negative scores remain negative.
- **Capital utilisation** — full credit once your average gross exposure
  reaches $400k. Sharpe is scale-free, so without this you could trade $50k,
  take almost no risk, and score the same as a team running the full book.
  $1m is a maximum, not a target. Above $400k there is no further utilisation
  reward: reducing size can improve the drawdown penalty even if profit falls.
  The objective is risk-adjusted performance with meaningful deployment.

Local sample performance is practice feedback, not the final result.

**The final ranking** runs your last submission on **200 independently
simulated futures**. Same market, same planted structure, 200 different rolls
of the dice. Your score is the **25th percentile** of that distribution — how
you did in a bad-but-not-catastrophic world, not how you did on your luckiest
day.

All teams use the same futures, and percentiles use NumPy's linear
interpolation. Every path starts in a fresh Python process, including imported
helpers. Python's `random` and NumPy's global random generator are seeded by
path index (local runs use zero). Seed any generators you create yourself.

A strategy that makes a fortune in 60% of futures and blows up in the other 40%
will lose to a steadier one. That's the point.

**Catastrophic-loss gate:** at most **5% of futures** may reach a peak-to-trough
drawdown of **$150,000 or more**. On 200 futures, 10 such paths are allowed;
11 makes the strategy ineligible for a final technical score. This gate is
checked before ranking, so severe losses cannot hide below the 25th percentile.
The same fraction applies to smaller organiser test runs.

**Your final position:** `70% score  +  30% presentation.`

You present for five minutes at 6pm. Judges want to know: what did you think
was happening in this market, how did you check it was real rather than noise,
and how did you decide the size. A clean, well-argued, modest strategy beats a
lucky number.

---

## Strategy requirements

- Keep your strategy and helper files together for the organisers' final run.
- Allowed imports: `numpy`, `pandas`, `scipy`, `scikit-learn`, `statsmodels`,
  and the standard library.
- No network access, no reading files outside your own folder, no subprocesses.
- Each backtest has a **120-second wall-clock deadline**, including strategy
  imports. A timeout or error on any final path makes that evaluation invalid;
  failed paths are never dropped to improve a score. The runner reports the
  failing paths. Don't fit a fresh model every single day.
- Multiple files are fine — put them next to your strategy and import normally.

---

## Where to start

You have four hours. A reasonable plan:

1. **First 20 minutes.** Run `examples/baseline_reversal.py`. Read it. Change one number
   and run it again. Get the loop working before you get clever.
2. **Next hour.** Look for structure. Do yesterday's losers bounce? Do trends
   persist? Do any two instruments move together? Measure it — don't guess.
3. **Next hour.** Build your best single signal properly. Sector-neutralise it.
   Risk-adjust it. Check what it costs to trade.
4. **Last hour.** Combine two or three uncorrelated signals and weight them by
   how much you trust each one. Compare the combination against each component
   on unseen data; adding a weak signal can make performance worse.

Then stop tuning and write your slides. A number you can explain is worth more
than a number you can't.
