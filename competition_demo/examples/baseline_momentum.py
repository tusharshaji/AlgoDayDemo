"""
BASELINE 2 - cross sectional momentum, volatility targeted.

Hypothesis: names that have drifted up over the last few months keep drifting.
Skip the most recent week, which is contaminated by short term reversal.
"""
import numpy as np
from _toolkit import sector_neutralise, to_dollars, smooth


def get_positions(ctx):
    if ctx.day < 70:
        return np.zeros(ctx.n_inst)
    long_ret = ctx.trailing_return(60)
    recent = ctx.trailing_return(5)
    signal = long_ret - recent                   # 60d momentum, 5d skipped
    signal = sector_neutralise(signal, ctx.sectors)
    signal = signal / (ctx.volatility(60) + 1e-9)
    target = to_dollars(signal)
    return smooth(target, ctx.positions, alpha=0.15)   # slow signal, trade slowly
