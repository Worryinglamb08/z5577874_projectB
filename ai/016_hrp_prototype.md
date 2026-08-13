# Prompt log — Hierarchical Risk Parity prototype

**Date:** 13 August 2026  
**Scope:** Pre-registration, isolated implementation, monthly walk-forward
comparison, constraint analysis, validation, and possible fund-menu decision

## Student prompt

The student instructed:

> Prototype HRP and see it's results

## Research and pre-registered specification

The assistant had shortlisted HRP using López de Prado's
[Building Diversified Portfolios that Outperform Out-of-Sample](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678),
which introduces the method as a covariance-based response to instability and
concentration in conventional quadratic portfolio optimisers.

Before examining HRP performance, the assistant fixed the experiment as:

- the standard distance transformation
  `sqrt((1 - correlation) / 2)`;
- deterministic single-linkage hierarchical clustering;
- the linkage-tree leaf order as the quasi-diagonal asset order;
- recursive bisection, allocating between each pair of child clusters inversely
  to their cluster variances;
- cluster variance computed using the inverse-variance portfolio inside each
  cluster;
- no expected-return or sentiment input;
- the unchanged Equity, Crypto and Combined return panels, trailing windows,
  monthly dates, calendars, 10 bp turnover cost, drifted pre-trade turnover and
  strict prior-only timing;
- the unchanged 10% equity cap, 25% crypto cap and 30% Combined crypto-sleeve
  cap; and
- Risk Parity as the controlled comparator in all three families.

Raw HRP weights are retained when feasible. If a raw target breaches a product
constraint, the target is projected to the nearest feasible vector by squared
Euclidean distance. The experiment records whether projection occurred and its
L1 magnitude. This keeps the constraint effect auditable rather than silently
calling a materially rewritten allocation raw HRP.

The method remains excluded from `DEFAULT_CONFIG.methods`, so the approved four
methods, 12 primary funds, fixed app artifact contract, and deployed investor
menu are unchanged.

## What the assistant produced

- Pure correlation-distance, cluster-variance, linkage ordering and recursive
  bisection calculations in `src/hierarchical_risk_parity.py`.
- An experimental `hierarchical_risk_parity` solver branch that reuses the
  existing walk-forward and validation engine without changing the default
  method tuple.
- A six-path experiment covering HRP and Risk Parity for Equity, Crypto and
  Combined families.
- Five synthetic tests and six prototype-only CSV artifacts.
- A standalone runner in `scripts/run_hrp_prototype.py`. The Streamlit app does
  not load the prototype artifacts.

## Real-data result

All figures are net of the existing 10 bp turnover cost and use the identical
2021–2023 live samples.

| Family | Method | Annualised return | Volatility | Sharpe | Maximum drawdown | Average monthly turnover |
|---|---|---:|---:|---:|---:|---:|
| Equity | HRP | 8.17% | 13.68% | 0.642 | -17.44% | 14.72% |
| Equity | Risk Parity | 9.83% | 14.53% | 0.718 | -18.51% | 5.87% |
| Crypto | HRP | 42.40% | 77.04% | 0.848 | -78.14% | 13.05% |
| Crypto | Risk Parity | 44.14% | 79.89% | 0.861 | -79.90% | 9.02% |
| Combined | HRP | 9.61% | 13.95% | 0.727 | -17.91% | 13.12% |
| Combined | Risk Parity | 13.88% | 16.20% | 0.883 | -19.49% | 6.46% |

HRP lowers annualised volatility and improves maximum drawdown in all three
families, but it also lowers return and Sharpe and raises turnover. Its weight
paths are economically distinct from Risk Parity: mean L1 distances are 0.314
for Equity, 0.240 for Crypto and 0.367 for Combined. Net-return correlations
remain high at 0.988, 0.998 and 0.964 respectively.

Relative to all four approved methods, HRP sits between Risk Parity and Minimum
Variance for Equity and Combined portfolios. For Combined, its 9.61% return,
13.95% volatility and 0.727 Sharpe are all above Minimum Variance's 5.67%,
12.52% and 0.504 except for the desired lower-volatility dimension, while Risk
Parity remains stronger on return and Sharpe. Crypto Minimum Variance remains
the strongest of these sample-specific risk-adjusted results.

## Constraint and product interpretation

- Equity and Combined raw HRP weights satisfied every constraint at all 36
  rebalances; no projection was applied.
- Crypto required projection at 8 of 36 rebalances because one raw weight
  exceeded 25%. Across all Crypto decisions, average projection L1 distance was
  only 0.0137; the largest was 0.0898. All ten coins retained positive latest
  weights, with TRX at the 25% cap.
- All Equity and Combined assets retained positive weights and no asset reached
  its cap.
- Combined HRP assigned only 2.57% to crypto on average, ranging from 0.73% to
  5.25%, with 3.87% latest. Combined Risk Parity averaged 6.96%. HRP therefore
  remains technically multi-asset but behaves predominantly like an equity
  portfolio because the recursive variance rule penalises the high-volatility
  crypto cluster.

## Checks performed

- Five synthetic tests cover known correlation-distance limits, correlated-pair
  clustering, valid positive weights, cap projection, exact determinism, and
  future-return isolation.
- Six paths and 216 monthly path-rebalances completed with zero solver, timing,
  weight-sum, bound, or distinctness failures.
- Maximum weight-sum residual was `2.22e-16`, below the `1e-7` tolerance.
- Recomputed Risk-Parity return, volatility, Sharpe, drawdown and turnover match
  the approved primary artifacts exactly for all three families.
- A second complete run produced byte-for-byte identical returns, weights,
  diagnostics, metrics, distinctness, and validation CSVs.
- Focused regression tests, app tests, lint, diff checks and the hand-in checker
  are completed after this record is written.

## Interpretation and recommendation

HRP is the first additional method tested that is a **credible inclusion
candidate**, but the evidence does not show performance dominance. Its genuine
advantages are lower volatility, shallower drawdowns, broad holdings, no return
forecasting, and a distinct correlation-cluster construction. Its disadvantages
are lower return and Sharpe than Risk Parity, roughly two to two-and-a-half
times Risk-Parity monthly turnover, linkage sensitivity, and a Combined fund
with very little crypto exposure.

The assistant recommends retaining the prototype and asking the student to make
the product decision. If included, it should be positioned as a
cluster-diversified, lower-risk alternative rather than a superior-return fund.
Its fact sheet must explain that clusters can change abruptly as correlations
change. It should not be described as outperforming Risk Parity.

## Artifacts

- `results/data/hrp_prototype_returns.csv`
- `results/data/hrp_prototype_weights.csv`
- `results/tables/hrp_prototype_diagnostics.csv`
- `results/tables/hrp_prototype_metrics.csv`
- `results/tables/hrp_prototype_distinctness.csv`
- `results/tables/hrp_prototype_validation.csv`

## Student review still required

The student must decide whether HRP's differentiated lower-risk role justifies
expanding the app from 12 to 15 funds. The current app and primary evidence have
not been changed.
