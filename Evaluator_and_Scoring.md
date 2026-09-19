# Evaluator and scoring

Run the included evaluator using the [demo setup guide](competition_demo/README.md).
The complete public implementation is in [comp/evaluator.py](competition_demo/comp/evaluator.py).

## The evaluator is the referee

A strategy supplies one dollar position per instrument. Positive means long,
negative means short, and zero means no holding. It requests dollar exposure,
not a number of shares.

Each simulated day, the evaluator:

1. Gives the strategy prices and volumes through today's close and its current holdings.
2. Receives the requested portfolio and applies the position limits.
3. Charges commission on changes from the current holdings.
4. Calculates profit or loss from today's close to tomorrow's close.
5. Updates the dollar value of the holdings and repeats.

The organiser process retains future prices, limits, accounting, and scoring.
The strategy runs in a separate process and receives only visible history.
It returns positions, not a self-reported score.

## Portfolio scale

| Rule | Value |
|---|---|
| Gross exposure: sum of absolute positions | At most $1,000,000 |
| Net exposure: absolute sum of signed positions | At most $100,000 |
| Exposure in any single instrument | At most $100,000 in either direction |
| Commission | 0.03% of dollars traded, also called 3 basis points |
| Full utilisation credit | $400,000 average gross exposure |

All dollar values are simulated. For example, $500k long plus $500k short uses
$1m gross exposure and has zero net exposure. The net cap promotes dollar balance;
it does not guarantee that all market or sector risk has been removed.

If a limit is exceeded, every requested position is scaled by the same factor.
Signs and relative weights are preserved. Limits apply after each rebalance.

## Daily profit calculation

```text
Net P&L = sum(target position × next-day percentage price change)
          − 0.0003 × sum(abs(target position − current holding))
```

The target position is the dollar amount after limits have been applied. Current
holdings reflect price changes since the previous decision.

For example, opening a $50k long and a $50k short trades $100k, costing $30.
If the long rises 2% and the short's price falls 1%, the book earns $1,500 before
commission and $1,470 after it.

Holdings change value with prices: a $1,000 long that rises 10% becomes $1,100.
Returning to a $1,000 target sells $100 and incurs $0.03 commission.

Each run starts flat and pays its opening costs. The final book is valued at the
last close without forced liquidation. The simulation assumes close-price
execution and excludes slippage, financing costs, borrowing costs, and liquidity
constraints. It is an educational model, not a complete trading venue simulation.

## Per-future score

```text
H = sqrt(252) × mean(daily net P&L)
    / max(sample standard deviation of daily net P&L, $1)

D = max(0, 1 − maximum drawdown / $150,000)

U = min(1, average gross exposure / $400,000)

If H > 0:  Score = H × D × U
Otherwise: Score = H
```

- **H, adjusted Sharpe:** average performance relative to variability, annualised
  using 252 trading days. A $1/day denominator floor keeps constant outcomes finite
  and correctly signed. Fewer than two observations gives zero.
- **D, drawdown penalty:** penalises the largest fall from a previous peak in
  cumulative profit, including the starting value of zero.
- **U, utilisation:** reduces credit for portfolios deploying less than $400k on average.

Flat P&L scores zero. Negative Sharpe remains negative: penalties do not improve
a losing score. The score has no fixed maximum and is not a percentage.

Example: H = 2, maximum drawdown = $30k, average gross exposure = $500k:
`Score = 2 × 0.8 × 1 = 1.6`.

$1m is a maximum exposure, not a target. Above $400k, a smaller portfolio can
score better by reducing drawdown even if its dollar profit falls. The objective
is risk-adjusted performance with meaningful deployment, not maximum raw profit.

## Where Monte Carlo is used

The normal participant command tests one strategy on the supplied public history.
It produces a local score, not the final Monte Carlo score.

Organisers run that strategy through each of the same 200 saved futures. Each
future produces a separate score. The final technical score is their **25th
percentile**, calculated using linear interpolation. A percentile describes a
position in the distribution; it is not the average of the worst quarter.

Before ranking:

- Every path must finish successfully. An error or timeout invalidates the evaluation;
  failed paths are never dropped to improve a result.
- At most 10 of 200 futures may reach a drawdown of $150k or more. Eleven makes
  the strategy ineligible, even if its 25th-percentile score is strong.
- The execution deadline is 120 seconds per backtest, including strategy imports
  and communication. Each future starts with fresh strategy state.

All futures preserve the same planted structure but use different random movements.
This measures robustness within the generator, not proof of real-market profitability.

## Overall event marks

The evaluator produces the technical score only. A proposed 70% technical / 30%
presentation split still needs a defined normalisation, judging rubric, and tie-break
rule before it can be used to determine the overall competition winner.
