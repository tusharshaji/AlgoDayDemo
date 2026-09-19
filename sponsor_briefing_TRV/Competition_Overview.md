# Competition overview

## What teams do

AlgoDay asks a practical question: **Can you find a pattern in noisy data, turn it
into a working strategy, and demonstrate that it remains useful across different
possible futures?**

Teams investigate a fictional market and write a Python function that chooses
dollar positions in 50 instruments. They can take long positions, which benefit
from price increases, or short positions, which benefit from price decreases.
The evaluator charges trading costs and applies portfolio limits.

The competition is intended for students interested in programming, data science,
algorithms, or quantitative problem-solving. Working Python examples provide a
starting point. A workshop would introduce the market, long and short positions,
the testing loop, and the scoring rules.

This is an applied data and coding challenge. It is not a contest in predicting
real stock prices, and simulated profit has no monetary payout of its own.

## Participant journey

1. **Learn the interface.** Run a supplied example and inspect its results.
2. **Form a hypothesis.** Look for a relationship that may predict future movements.
3. **Build and test.** Edit the strategy, compare results, and account for costs.
4. **Check the evidence.** Test on later portions of available history rather than
   repeatedly optimising against one full-history score.
5. **Explain the result.** Present the hypothesis, experiments, risk decisions,
   and limitations in a short team presentation.
6. **Receive the final technical result.** Organisers evaluate the strategy on
   200 saved futures unavailable to participants during development.

Finding a useful pattern is sometimes called finding an **alpha**. In this event,
that means an exploitable predictive relationship in the simulated market, after
costs. Combining more signals is not automatically better; teams must test it.

## Proposed event schedule

The following is the working schedule in the project, not a confirmed booking.
Presentation capacity depends on the eventual number of teams.

| Time | Activity |
|---|---|
| 13:00 | Welcome and competition introduction |
| 13:15–14:00 | Introductory workshop |
| 14:00–18:00 | Four-hour strategy development session |
| 16:30 | Organiser scoring dry run to identify runtime or compatibility issues |
| 18:00 | Strategy deadline; final scoring and presentations begin |
| Around 19:15 | Results and prizes, subject to team count and scoring duration |

## Learning outcomes

- Translate a hypothesis into executable code.
- Distinguish historical fit from performance on unseen data.
- Compare alternatives through controlled experiments.
- Balance expected performance, transaction costs, and downside risk.
- Communicate evidence, limitations, and technical choices clearly.

These are intended outcomes, not measured claims from a completed participant pilot.

## Why evaluate 200 futures?

A single favourable market period can make a weak strategy look successful.
Evaluating the same strategy across many continuations gives a broader view of its
behaviour. Every team uses the same futures, making results directly comparable.

The final percentile and loss rule favour strategies that hold up across this
synthetic market. They do not demonstrate profitability in real financial markets
or eliminate every source of uncertainty.

## Presentations and awards

The working proposal is 70% technical performance and 30% presentation. The
evaluator currently computes only the technical score. The conversion of technical
scores into marks, judging rubric, and tie-break procedure must be agreed before
the event and communicated to participants.

Presentations could cover the team's hypothesis, how it was tested, the strongest
counter-evidence, and why the team chose its final portfolio size. Sponsor judges
could contribute to this component if agreed.
