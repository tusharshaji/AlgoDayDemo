# AlgoDay — sponsorship briefing for TRV

**A Devs Society competition in coding, data analysis, and decision-making under uncertainty.**

Prepared 19 September 2026 · Discussion proposal

## The proposal in one minute

Devs Society is developing AlgoDay: a team competition with a four-hour build
session in which students create Python strategies for a fictional financial
market. Participants investigate data, test ideas, and explain their decisions.
All trading uses simulated money; no real assets are bought or sold.

Teams receive market history, starter strategies, and the same local scoring
engine used by the organisers. The final technical result evaluates each
strategy across the same **200 alternative market futures**, rewarding
risk-adjusted performance beyond a single favourable backtest. An additional
loss rule prevents a strategy from hiding frequent severe drawdowns below its
percentile score.

We would welcome a discussion with TRV about supporting prizes, participant
hospitality, or event delivery, and optionally contributing mentors, judges,
or a short educational session. The sponsorship amount, benefits, and scope
would be agreed together; this pack does not propose a binding commitment.

## At a glance

| Item | Current proposal |
|---|---|
| Organiser | Devs Society |
| Event | AlgoDay |
| Activity | Team-based Python strategy development using synthetic market data |
| Build time | Four hours, preceded by an introductory workshop |
| Participant data | 750 daily observations across 50 fictional instruments in six sectors |
| Final technical evaluation | 200 shared futures, each containing 250 trading days |
| Final score | 25th percentile of per-future scores, subject to execution and loss checks |
| Presentation component | Proposed 30%; technical component proposed 70%, with the combined-mark method still to be finalised |
| Current implementation | Market generator, evaluator, participant pack, calibration tools, organiser visualiser |
| Date, venue, attendance and budget | To be confirmed by the organising team |

## Why this is a useful student event

- **Accessible entry:** working examples reduce setup friction. Basic Python
  familiarity is expected; specialist trading knowledge is not an entry requirement.
- **Depth for stronger teams:** participants can investigate predictive signals,
  test assumptions, compare strategies, and manage transaction costs and risk.
- **Visible reasoning:** proposed short presentations let teams explain their
  evidence and tradeoffs, not just show a final number.
- **Practical sponsor involvement:** mentoring or judging can give TRV direct
  opportunities to discuss students' technical thinking, subject to the agreed format.

## Read this pack

| File | What it covers |
|---|---|
| [Competition overview](Competition_Overview.md) | Purpose, student experience, learning outcomes, proposed event schedule |
| [Market data and starter strategies](Market_Data_and_Starter_Strategies.md) | Prices, volumes, sectors, example strategies, and public versus hidden information |
| [Evaluator and scoring](Evaluator_and_Scoring.md) | Daily accounting, portfolio limits, Monte Carlo evaluation, formulas and examples |

For an initial conversation, start with this README. The sponsorship invitation
is provided separately in the accompanying email.
The other files provide detail for organisers, technical reviewers, and judges.

## Try the actual competition

The [competition demo](competition_demo/README.md) contains the real public
scoring engine, the full 750-day dataset, all four baseline strategies, the
minimal example, the blank strategy template, and the participant rules.

After extracting this package, open a terminal in `competition_demo` and run:

```sh
python -m pip install -r requirements.txt
python -m comp.evaluator examples/example_simple.py
```

Use Python 3.10 or newer. See the [demo setup guide](competition_demo/README.md)
for Windows/macOS command variations, the other examples, and a file-by-file guide.
No organiser repository or submission website is needed.

The output is a **local score on public data**. The statement about 200 futures
in the report describes final event scoring; it is not a Monte Carlo result.

## Package layout

```text
AlgoDay_TRV_Sponsor_Briefing/
  README.md
  Competition_Overview.md
  Market_Data_and_Starter_Strategies.md
  Evaluator_and_Scoring.md
  competition_demo/
    README.md
    RULES.md
    requirements.txt
    strategy.py
    comp/       actual scoring engine and strategy execution code
    data/       prices.csv, volumes.csv, metadata.csv
    examples/   starter strategies and shared helpers
```

## Scope of this briefing

This sponsor briefing includes a runnable demo built from the same public sources
as the participant pack. It includes public sample prices, volumes, metadata,
and the actual local evaluator. Hidden final-evaluation datasets, the answer key,
market-generation code, and organiser-only strategy implementations remain excluded.

Technical descriptions reflect the current project. Event logistics and sponsor
benefits are proposals where identified. Attendance, funding, recruitment outcomes,
and sponsor deliverables are not yet committed.
