"""
BASELINE 1 - short horizon cross sectional reversal.

Hypothesis: a name that fell hard yesterday relative to its sector tends to
bounce. Buy the idiosyncratic losers, sell the idiosyncratic winners.

This is the highest turnover idea in the pack, so it is the one where
commission decides whether you make money. Two things keep it alive:
  - concentrate: only trade the strongest quarter of the signal
  - smooth: move part of the way to the new target, not all of it
These are hypotheses to test, not guaranteed improvements. On the current
sample, removing smoothing improves performance, and removing concentration
still leaves a profitable strategy. Compare both on unseen periods.
"""
import numpy as np
from _toolkit import sector_neutralise, to_dollars, smooth, top_bottom


def get_positions(ctx):
    r = ctx.returns(3)[-1]                       # yesterday's move
    resid = sector_neutralise(r, ctx.sectors)    # strip out the sector move
    resid = resid / (ctx.volatility(60) + 1e-9)  # risk adjust

    signal = -resid                              # bet against it
    signal = top_bottom(signal, frac=0.25)       # only the strongest quarter
    target = to_dollars(signal)
    return smooth(target, ctx.positions, alpha=0.40)
