# Prompt log — Phase 3 rebalance-frequency experiment

**Date:** 13 August 2026  
**Scope:** Controlled daily, every-5-day, every-10-day, and monthly combined-fund
experiments with 5/10/25 basis-point cost sensitivity

## What I wanted

Test whether more frequent portfolio retraining improves the selected combined
funds or mainly increases turnover and cost drag, while retaining monthly as the
assignment-compliant product specification.

## Prompt(s)

The student instructed:

> Move to phase 3

The Phase 0 roadmap had already fixed daily, every 5 observations, every 10
observations, and monthly as the schedules and 5, 10, and 25 basis points as the
cost cases.

## What the assistant produced

- Generalised the Phase 2 backtest to accept an explicit schedule and cost while
  leaving the primary monthly call unchanged.
- Added exact fixed-observation schedule generation anchored to the same first
  eligible return date and preserved first-observed-date monthly rebalancing.
- Predeclared Risk Parity and Maximum Sharpe as complementary combined-fund
  experiment methods in the central configuration.
- Ran eight controlled paths and reconstructed net performance under all three
  predeclared transaction-cost assumptions without re-solving weights.
- Added a deterministic solution cache: same-date target solutions from the daily
  run are reused by lower-frequency paths, which changes runtime but not results.
- Produced return paths, 2,032 decision diagnostics, performance/cost tables,
  decision-support evidence, and a report-ready turnover-versus-Sharpe exhibit.
- Added synthetic schedule, cost-isolation, drift-turnover, and future-return
  leakage tests plus a full real-data experiment regression.

## What was wrong or risky

- Calling every fifth observed equity date “weekly” is a trading-observation
  interval, not a calendar-week anchor. Outputs therefore use the explicit label
  `Every 5 days`; similarly, `Every 10 days` avoids overstating calendar meaning.
- Comparing schedules from different first live dates would confound the result.
  All fixed-interval paths begin on the first date after the complete 252-return
  window, and monthly begins on that same date because it is also the first
  observed date of January 2021.
- Re-running a cost case with re-estimated weights could accidentally change more
  than cost. The 5/10/25 basis-point sensitivity applies each cost to the same
  saved gross path and turnover series.
- Higher-frequency results are not assignment-compliant primary funds. Every
  non-monthly record is labelled `diagnostic experiment`, and the Phase 2 required
  files remain monthly-only.
- Maximum Sharpe's daily result improves net Sharpe and CAGR at 10 basis points.
  Hiding that because it complicates the monthly product decision would be
  misleading. The result is reported, alongside its roughly 1,412% annualised
  turnover, stronger cost sensitivity, and non-compliance with the primary rule.
- Two optimisers across four frequencies required many repeated constrained
  solves. Caching reuses mathematically identical same-date solutions without
  weakening the test or importing future information.
- The first figure export passed automated validation but showed scientific and
  percentage tick collisions on visual inspection. The log axis now uses explicit
  percentage ticks and suppresses minor labels; it was regenerated and inspected.

## Checks performed

- Eight frequency paths and 24 frequency-by-cost metric rows were generated.
- All paths share one first live date, one last live date, one 252-observation
  window, and one 60-asset universe.
- All 2,032 decisions have estimation dates strictly before the first return
  earned and pass solver, sum, bound, and crypto-sleeve checks.
- Maximum target-weight sum residual is approximately `1.65e-9`, below the
  `1e-7` tolerance; maximum bound residual is zero.
- Phase 3 monthly gross/net returns and target weights reconcile exactly to the
  Phase 2 primary funds.
- For every path, increasing costs from 5 to 10 to 25 basis points decreases
  ending net wealth; no monotonicity violation is present.
- Rebalance counts decrease in the intended order: daily, every 5 days, every 10
  days, monthly.
- A synthetic cost test confirms changing only the cost leaves gross returns and
  turnover unchanged while lowering net wealth.
- A future-return perturbation leaves the first daily minimum-variance target
  unchanged.
- The complete Project B test suite passes `37` tests, including the independent
  full-data experiment reconstruction.

## Key observed results

- Risk Parity monthly is strongest on 10 bp net Sharpe: about 0.883, versus 0.872
  daily, 0.865 every 5 days, and 0.876 every 10 days.
- Risk Parity annualised turnover rises from about 78% monthly to 216% daily,
  without improving net Sharpe.
- Maximum Sharpe daily achieves about 17.1% net CAGR and 0.897 net Sharpe at 10
  bp, versus about 14.8% and 0.776 monthly.
- Maximum Sharpe daily annualised turnover is about 1,412%, versus 333% monthly;
  cumulative 2021--2023 turnover is about 42.2 versus 10.0.
- At 25 bp, Maximum Sharpe daily net CAGR falls to about 14.6%, illustrating how
  its apparent frequency benefit depends more heavily on execution assumptions.

## What I changed and why

The assistant kept Phase 3 as an experiment layer above the verified Phase 2
engine rather than creating new user-facing funds or rewriting the primary output
contract. This makes frequency the intended comparison and preserves an exact
audit bridge back to the monthly product evidence.

The build-figure workflow influenced the exhibit design: the chart uses a small-
multiple turnover-versus-net-Sharpe comparison, fixed colors by schedule,
monthly-reference lines, self-contained source/sample/units context, and explicit
diagnostic wording. Visual inspection led to a second formatting pass even after
the automated validator passed.

## Student review still required

- Review this contemporaneous log and rewrite any wording that does not reflect
  the student's own evaluation.
- Confirm the report should lead with Risk Parity as the cleaner product-frequency
  result while disclosing Maximum Sharpe's higher-frequency counterexample.
- Do not promote the daily Maximum Sharpe diagnostic into the app's primary fund
  menu unless the assignment rule and product governance are deliberately changed.
