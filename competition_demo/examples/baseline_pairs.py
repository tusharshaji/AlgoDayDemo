"""
BASELINE 3 - pairs / statistical arbitrage.

Hypothesis: some instruments are cointegrated - their log price spread wanders
but keeps being pulled back. Find them once, then trade the spread when it
stretches.

Selection matters more than the trade itself. See _toolkit.find_pairs for the
two screens and why ranking on half-life alone overfits.
"""
import numpy as np
from _toolkit import find_pairs, pair_signal, to_dollars, smooth

_PAIRS = None


def get_positions(ctx):
    global _PAIRS
    if ctx.day < 420:
        return np.zeros(ctx.n_inst)
    if _PAIRS is None:
        _PAIRS = find_pairs(ctx.close, ctx.sectors)
    if not _PAIRS:
        return np.zeros(ctx.n_inst)

    signal = pair_signal(ctx.close, _PAIRS, ctx.n_inst)
    target = to_dollars(signal)
    return smooth(target, ctx.positions, alpha=0.35)
