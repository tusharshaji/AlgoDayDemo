# AlgoDay — runnable competition demo

This folder contains the actual public evaluator, the full participant sample
dataset, and working starter strategies. It runs independently of the organiser
repository after installing Python and the dependencies below.

## Run an example

Install **Python 3.10 or newer**. Extract the sponsor ZIP, open a terminal in
this `competition_demo` folder, and run:

```sh
python -m pip install -r requirements.txt
python -m comp.evaluator examples/example_simple.py
```

On Windows, if `python` is not recognised but the Python launcher is installed,
use `py` instead of `python` in these commands. On macOS or Linux, the command
may be `python3`. Run installation and evaluation with the same interpreter.

A successful run prints daily simulation counts, profit and loss, commission,
Sharpe, maximum drawdown, portfolio exposure, and a final local `SCORE`.
The example normally finishes in a few seconds; runtime depends on the machine.

## Compare approaches

```sh
python -m comp.evaluator examples/baseline_long.py
python -m comp.evaluator examples/baseline_reversal.py
python -m comp.evaluator examples/baseline_momentum.py
python -m comp.evaluator examples/baseline_pairs.py
```

Edit `strategy.py` to try your own idea, then run:

```sh
python -m comp.evaluator strategy.py
```

The template starts with no positions and therefore scores zero. A working
example can be copied into it as a starting point. Examples importing `_toolkit`
should stay in `examples/`, or have `_toolkit.py` copied beside the strategy.

## Included files

| File | Purpose |
|---|---|
| `RULES.md` | Participant rules and complete scoring explanation |
| `requirements.txt` | Core dependencies: NumPy, pandas, SciPy |
| `strategy.py` | Blank strategy template |
| `data/prices.csv` | Actual public dataset: 750 days × 50 instrument closing prices |
| `data/volumes.csv` | Matching daily share volumes |
| `data/metadata.csv` | Instrument names and sector labels |
| `comp/evaluator.py` | Daily accounting, portfolio limits, metrics, and command-line interface |
| `comp/config.py` | Limits, commission, and scoring constants |
| `comp/execution.py` | Parent-side evaluation and strategy-process communication |
| `comp/_strategy_worker.py` | Child process that receives visible history and returns positions |
| `comp/__init__.py` | Python package marker |
| `examples/example_simple.py` | Minimal reversal strategy |
| `examples/baseline_*.py` | Long-only, reversal, momentum, and pairs examples |
| `examples/_toolkit.py` | Shared example helpers |

Keep the `comp`, `data`, and `examples` directory names unchanged: the evaluator
and example imports use them. All commands above run from this folder.

## Local score versus final Monte Carlo score

This demo produces a score on the supplied **public history**. A report line
mentioning 200 futures describes the event's final method; it does not mean
the local command has run Monte Carlo evaluation.

Final competition scoring runs on the organiser's separate 200 saved futures.
Those private datasets, their generator, the answer key, and the organiser-only
Monte Carlo runner are not included in this sponsor demo. No access to the
organiser's computer or a submission website is needed for the local demo.

## Practical notes

- Python and dependencies must be installed; an internet connection may be needed
  for dependency installation, but the supplied examples do not need network access.
- Positions and profits use simulated dollars. Nothing connects to a broker.
- The runner separates strategy code from trusted scoring, but is not an OS
  security sandbox. Only run trusted code on a personal machine.
- For the sponsor pitch and event background, return to [the main README](../README.md).
