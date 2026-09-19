# Data and participant pack

The files described here are included in [competition_demo](competition_demo/README.md).

## The public dataset

| File | Contents | Use |
|---|---|---|
| `prices.csv` | 750 daily closing observations for each of 50 instruments | Essential input for strategy research |
| `volumes.csv` | Matching daily share volumes | Optional feature for investigation |
| `metadata.csv` | Instrument identifiers and sector membership | Helps compare related instruments |

Instrument names are fictional, from `INS00` to `INS49`. The six sectors are
energy, financials, technology, health, industrials, and consumer.

**Volumes are share counts, not traded dollars.** The generator makes volume tend
to increase on days with larger price movements, with additional randomness.
The evaluator does not currently use volume to impose liquidity limits or determine
commission. A competitive strategy can use prices without using volume.

**Sectors influence prices.** Instruments in a sector share a sector-specific
source of movement, alongside market-wide movements and individual effects.
They do not move identically. A sector label is a fixed grouping, not a signal
that a price will rise or fall.

## How the market is constructed

The generator combines market-wide variation, sector variation, individual noise,
and deliberately discoverable effects. Periods of higher volatility and occasional
large movements create uncertainty around those effects.

The pattern families include short-term reversals, slow trends, linked instruments
whose relative prices sometimes converge, delayed relationships between instruments,
and a small volatility-related drift. These effects are noisy, overlap, and vary
in usefulness. Their exact assignments and parameters are organiser information.

The task therefore has discoverable structure without handing participants a list
of which instruments to trade. Baseline code introduces several broad approaches;
teams improve their selection, testing, and implementation.

## What participants receive

| File or folder | Purpose |
|---|---|
| `README.md` and `RULES.md` | Setup, usage, constraints, and scoring explanation |
| `strategy.py` | Blank function template to edit |
| `data/` | Public prices, volumes, and sector metadata |
| `comp/` | Public evaluator, configuration, and strategy execution tools |
| `examples/example_simple.py` | Minimal reversal example |
| `examples/baseline_long.py` | Equal-weight long-only comparison |
| `examples/baseline_reversal.py` | Sector-relative reversal with risk adjustment and smoothing |
| `examples/baseline_momentum.py` | Longer-term momentum with reduced emphasis on the latest week |
| `examples/baseline_pairs.py` | Linked-instrument selection and relative-price trading |
| `examples/_toolkit.py` | Shared utilities used by the examples |
| `requirements.txt` | Core Python dependencies |

Basic Python familiarity is expected. The examples reduce the initial barrier,
but are not guaranteed optimal strategies. More advanced organiser strategies
are not included in the participant pack.

## What remains hidden

Organisers retain 150 additional historical days and 200 saved futures, each with
250 trading days, together with the generator and answer key. The futures are
generated in advance; organisers do not give each team a different random dataset.

At final evaluation, a strategy starts flat at the end of the public-plus-hidden
historical prefix. It receives that prior history, and then sees new prices only
as the simulated days arrive. The first decision earns the move into the first
future day. All 250 future returns are scored.

Thus hidden data is genuine held-back information, even though it was generated
synthetically. Students do not receive the final datasets during development.

## Expected difficulty

The supplied examples make a working starting strategy accessible. Current organiser
testing shows substantial room to improve it, especially by identifying which
instruments exhibit reliable reversal behaviour. Adaptive reversal is currently a
strong component; the pattern families are not equally profitable.

Difficulty has been examined with reference strategies, but not established through
a completed student pilot. A short pilot should check setup time, comprehension,
and whether the four-hour scope suits the intended audience.
