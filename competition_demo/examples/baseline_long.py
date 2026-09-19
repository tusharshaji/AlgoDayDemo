"""
BASELINE 0 - equal weight long only.

Included to make a point in the workshop: the net exposure limit caps this at
$100k of exposure out of a $1M budget, so it can barely trade. If you want to
use the whole book you have to be market neutral.
"""
import numpy as np


def get_positions(ctx):
    return np.full(ctx.n_inst, 1_000_000.0 / ctx.n_inst)
