# Prompt log — Phase 2 monthly funds

**Date:** 13 August 2026  
**Scope:** Typed configuration, constrained portfolio rules, monthly walk-forward
backtests, costs, fact sheets, and report-ready fund exhibits

## What I wanted

Move from the verified Project A foundation to the assignment's core product:
12 independently investable monthly Stockist Funds across three asset families
and four transparent methods, supported by genuinely out-of-sample evidence.

## Prompt(s)

The student instructed:

> Move to Phase 2

The approved Phase 0 defaults and the Phase 1 calendar/return foundation supplied
the modelling constraints.

## What the assistant produced

- Added one immutable `ModelConfig` containing every approved primary setting.
- Implemented Equal Weight, Minimum Variance, equal-risk-contribution Risk Parity,
  and deterministic multi-start Maximum Sharpe under long-only, full-investment,
  individual asset caps, and the combined crypto-sleeve cap.
- Implemented first-observed-date monthly rebalancing after a complete fixed
  trailing window, with target weights earning returns only after the estimation
  sample ends.
- Allowed holdings to drift between rebalances, calculated turnover from drifted
  pre-trade weights, and deducted 10 basis points per unit of turnover.
- Generated gross and net daily returns, wealth, drawdown, metrics, current
  simulated target weights, benchmark-relative results, diagnostics, method-
  distinctness evidence, configuration evidence, and compact fact sheets.
- Generated and visually checked four report-ready figures using the repository's
  figure workflow and the approved Stockist Funds visual system.
- Added synthetic calculation tests plus a full real-data 12-fund regression.

## What was wrong or risky

- Holding each target weight constant every day would silently rebalance daily and
  understate true monthly turnover. The implementation drifts post-return weights
  until the next target date.
- Using the previous target instead of the pre-trade drifted portfolio would also
  mismeasure turnover. Rebalance records retain both vectors.
- Applying a target to a return used in its estimation window would create look-
  ahead. Each diagnostic stores estimation start/end and first held return date;
  all 432 decisions satisfy `estimation_end < first_held_return_date`.
- Optimiser success flags alone are weak evidence. The code additionally checks
  finite weights, sum residual, bounds, sleeve caps, objective values, expected
  moments, covariance conditioning, concentration, and risk-contribution
  dispersion.
- Maximum Sharpe is sensitive to noisy sample means and local solutions. The
  implementation uses analytic gradients and deterministic starts from equal
  weight, minimum variance, and a return-seeking linear programme, then selects
  the best valid candidate without seeing later realised returns.
- A combined opportunity set does not force a positive crypto holding under the
  approved maximum-only sleeve rule. Combined Minimum Variance averages roughly
  0.7% crypto and reaches zero in some months. This is disclosed rather than
  obscured; introducing a minimum crypto sleeve would be a new product assumption
  requiring approval.
- Crypto results are large and volatile. They use the native seven-day calendar,
  365-day annualisation, and the same historical 2021--2023 live sample logic;
  they are not forecasts or evidence beyond 2023.
- Charging initial deployment is a modelling choice. The implementation records
  one-way initial turnover of one and then half-L1 rebalance turnover, ensuring
  the net wealth series includes the cost of establishing a new investment.
- The first rendered figures passed automated checks but still showed a legend
  collision and crowded labels on visual inspection. Layout, dollar log ticks,
  annotation spacing, and font sizes were corrected and the figures regenerated.

## Checks performed

- Fund count: 12; monthly rebalances: 432; failed decisions: 0.
- Maximum weight-sum residual: approximately `5.4e-11`; maximum individual-cap
  residual: zero; maximum combined crypto sleeve: 30% within tolerance.
- All 18 method pairs pass the predeclared L1-distance distinctness check.
- Risk-parity risk-contribution dispersion is close to zero for every family.
- First live dates are 1 January 2021 for crypto and 4 January 2021 for equity and
  combined funds; all estimation windows end on earlier dates.
- Hand test for three returns reproduces ending wealth `0.924`, cumulative return
  `-7.6%`, and maximum drawdown `-20%`.
- A drift/turnover test independently calculates the pre-trade allocation after a
  10% single-asset move and reconciles the next rebalance turnover.
- A temporal-leakage test changes all future high-volatility-asset returns while
  preserving the history and confirms the first minimum-variance target is
  unchanged.
- The full real-data portfolio regression passes and writes every required Phase 2
  file using its fixed filename.
- Selected Phase 2 files pass Ruff; the full Project B test result is recorded in
  the phase completion evidence.

## Key observed results

- Combined Equal Weight: about 15.0% net CAGR, 21.6% volatility, 0.76 Sharpe, and
  -27.9% maximum drawdown.
- Combined Risk Parity: about 13.9% net CAGR, 16.2% volatility, 0.88 Sharpe, and
  -19.5% maximum drawdown.
- Combined Maximum Sharpe: about 14.8% net CAGR, 20.5% volatility, 0.78 Sharpe,
  and substantially higher average turnover of about 27.7% per rebalance.
- Combined Minimum Variance: about 5.7% net CAGR, 12.5% volatility, 0.50 Sharpe,
  and -15.9% maximum drawdown.
- Crypto funds have materially higher returns and 73%--83% maximum drawdowns;
  these outcomes reinforce the need to show return and risk with equal prominence.

## What I changed and why

The assistant expanded the initial placeholder into a financially explicit engine
rather than a matrix-weight shortcut. It separated target weights, drifted
pre-trade weights, gross performance, cost deductions, diagnostics, and product-
facing metrics so later schedule and sentiment experiments can change one layer
without silently changing the rest.

The build-figure workflow influenced the exhibit work: growth is shown as growth
of `$1` on a dollar-labelled log scale, captions carry sample/source/units, dense
drawdowns use thin translucent lines, and the weight history uses small-multiple
part-to-whole panels instead of an unreadable 60-asset chart.

## Student review still required

- Review this contemporaneous log and rewrite any wording that does not reflect
  the student's own evaluation.
- Decide whether the app should describe combined funds as a combined *opportunity
  set* when an optimiser temporarily assigns zero crypto, or whether a future
  separately labelled fixed/minimum-sleeve sensitivity is desirable.
- Keep daily, weekly, and bi-weekly comparisons in Phase 3 as diagnostics; do not
  replace these monthly funds as the primary product specification.
