"""
EXAMPLE 0 - the smallest thing that works.

Three real lines. Run it, read it, change a number, run it again. Get the loop
going before you get clever.

Idea: if an instrument fell more than the others yesterday, buy it; if it rose
more, short it. Bet on things coming back to the middle.
"""
import numpy as np


def get_positions(ctx):
    r = ctx.returns(2)[-1]                      # yesterday's move, per instrument
    signal = -(r - r.mean())                    # bet against it
    return signal / np.abs(signal).sum() * 1_000_000     # scale to the budget
