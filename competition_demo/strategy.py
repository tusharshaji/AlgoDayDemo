"""
YOUR STRATEGY. This is the only file you need to edit.

Run it with:
    python -m comp.evaluator strategy.py

In the organiser repository, use strategies/template.py instead.

The rules, in one box:
    - return DOLLARS per instrument, positive = long, negative = short
    - sum of |positions|  <= 1,000,000   (gross limit)
    - |sum of positions|  <=   100,000   (net limit - stay market neutral)
    - |any one position|  <=   100,000   (concentration limit)
    - you pay 3 bps on every dollar you trade
Break a limit and we scale you to fit, we do not reject you.
"""
import numpy as np


def get_positions(ctx):
    """
    Called once per day.

    ctx.close      (days, 50) prices up to and including today
    ctx.volume     (days, 50) share volume
    ctx.sectors    (50,)      sector id per instrument
    ctx.positions  (50,)      what you are holding right now
    ctx.day        int        today's index

    Helpers:
    ctx.returns(n)           last n daily returns, shape (n, 50)
    ctx.trailing_return(n)   total return over last n days, shape (50,)
    ctx.volatility(n)        daily vol over last n days, shape (50,)

    Return: np.ndarray of 50 dollar amounts.
    """
    # ---------------------------------------------------------------
    # Start here. This does nothing - it holds no positions at all.
    # ---------------------------------------------------------------
    return np.zeros(ctx.n_inst)


# -------------------------------------------------------------------------
# A worked example to copy from. Delete or ignore.
#
# def get_positions(ctx):
#     # yesterday's move, per instrument
#     r = ctx.returns(2)[-1]
#
#     # bet against it: buy the losers, sell the winners
#     signal = -(r - r.mean())
#
#     # scale so we use the full gross budget
#     signal = signal / (np.abs(signal).sum() + 1e-12)
#     return signal * 1_000_000
# -------------------------------------------------------------------------
