# Prompt log — Effective Number of Bets prototype

**Date:** 13 August 2026  
**Scope:** Research, isolated implementation, monthly walk-forward comparison,
validation, and promotion decision for a possible fifth portfolio method

## Student prompts

The student asked:

> What portfolio method can be a good option to add? Markowitz? Effective
> Number of bets?

The student then clarified:

> Markowitz is already min variance, Look into the Effective number of bets

After reviewing the method, the student instructed:

> Let us prototype it and see it's results

## Research and design decision

The assistant confirmed that Minimum Variance and Maximum Sharpe already sit
inside the Markowitz mean–variance family. Effective Number of Bets (ENB) is
different: it measures entropy across uncorrelated portfolio-variance sources,
not merely the number of assets or equality of asset-level risk contributions.

The primary sources reviewed were:

- Attilio Meucci, [Managing Diversification](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1358533),
  which defines ENB as exponential entropy of uncorrelated-bet variance shares;
- Deguest, Martellini and Meucci,
  [Risk Parity and Beyond](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2355778),
  which distinguishes asset risk parity from factor risk parity, documents
  non-uniqueness, and evaluates PCA-based ENB portfolios; and
- Meucci, Santangelo and Deguest,
  [Risk Budgeting and Diversification Based on Optimized Uncorrelated Factors](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2276632),
  which develops Minimum-Torsion Bets as a more interpretable alternative to
  PCA factors.

The first prototype deliberately uses the documented PCA decomposition as a
baseline. It is not presented as the final Minimum-Torsion implementation. The
method remains excluded from `DEFAULT_CONFIG.methods`, so the approved 12 funds,
fixed app artifact contract, and investor menu are unchanged.

## What the assistant produced

- Added pure PCA bet-distribution and ENB calculations.
- Added `effective_bets` to the solver's allowed experimental vocabulary while
  leaving the four approved primary methods unchanged.
- Maximised PCA-bet Shannon entropy under the existing fully invested,
  long-only, individual-asset and combined crypto-sleeve caps.
- Used seven deterministic feasible starts at each decision date: equal weight,
  inverse volatility, minimum variance, risk parity, and three seeded projected
  Dirichlet portfolios. Among numerically tied maximum-entropy candidates, the
  lower-variance solution is selected.
- Reused the approved trailing windows, monthly dates, annualisation calendars,
  10 bp turnover cost, drifted pre-trade turnover, and strict prior-only timing.
- Built six paths: PCA-ENB and Risk Parity for equity, crypto, and combined.
- Added an isolated runner and six prototype-only CSV artifacts. No prototype
  result is loaded by the deployed app.

## Real-data result

All figures below are after the existing 10 bp turnover cost and cover the same
2021–2023 live samples as the primary funds.

| Family | Method | Annualised return | Volatility | Sharpe | Maximum drawdown | Average monthly turnover | Average ENB |
|---|---|---:|---:|---:|---:|---:|---:|
| Equity | PCA Effective Bets | 3.79% | 13.23% | 0.347 | -16.40% | 25.98% | 8.47 |
| Equity | Risk Parity | 9.83% | 14.53% | 0.718 | -18.51% | 5.87% | 2.01 |
| Crypto | PCA Effective Bets | 47.49% | 76.17% | 0.891 | -71.81% | 16.89% | 1.86 |
| Crypto | Risk Parity | 44.14% | 79.89% | 0.861 | -79.90% | 9.02% | 1.07 |
| Combined | PCA Effective Bets | 5.82% | 13.65% | 0.483 | -17.57% | 26.25% | 13.74 |
| Combined | Risk Parity | 13.88% | 16.20% | 0.883 | -19.49% | 6.46% | 3.63 |

The mean L1 target-weight distance from Risk Parity was 1.394 for equity,
1.059 for crypto, and 1.420 for combined, so the rule is economically distinct.
It increased average ENB at every one of the 36 monthly decisions in each
family. However, it also created sparse, cap-heavy portfolios: the latest
equity and combined prototypes held 12 nonzero assets, while the latest crypto
prototype held four assets, each at its 25% cap. This is mathematically
consistent: diversified orthogonal factor exposure does not guarantee broad
asset holdings.

## Error found and correction

The first real-data run was computationally impractical because every numerical
finite-difference evaluation repeated the covariance eigendecomposition. The
run was stopped. The assistant derived an analytic gradient for negative PCA-bet
entropy, cached one eigendecomposition per optimisation, and checked the
gradient against numerical differentiation. The maximum absolute discrepancy
was approximately `6e-08`. The complete real-data prototype then ran normally.

## Checks performed

- Five synthetic tests cover known ENB limits, variance-share reconstruction,
  invalid covariance, constrained optimisation, and temporal leakage.
- Six comparison paths and 216 monthly rebalances completed with zero solver
  failures or timing violations.
- Maximum weight-sum residual was `9.27e-10`, below the `1e-7` tolerance; there
  were no individual or sleeve-cap violations.
- ENB was never below Risk Parity at a matching decision date.
- The recomputed Risk Parity return, volatility, Sharpe, drawdown, and turnover
  matched the approved primary artifacts exactly in all three families.
- A complete second run produced byte-for-byte identical returns, weights,
  metrics, distinctness, and validation CSVs.

## Interpretation and recommendation

The raw PCA-ENB rule should **not yet be promoted into the app**. It is distinct
and improves its stated diversification score, but the equity and combined
Sharpe ratios fall by 0.371 and 0.400 relative to Risk Parity, while average
monthly turnover rises by about 20 percentage points. Only crypto improves
slightly, and that result comes from a four-asset, cap-bound portfolio with a
71.81% maximum drawdown.

A defensible follow-up would test Minimum-Torsion Bets and/or a target-ENB
constraint with turnover regularisation rather than maximising raw PCA ENB.
That would be a new exploratory specification and must remain outside the app
until its rule is fixed prospectively and its out-of-sample evidence is
validated. The student must decide whether that follow-up is worth the added
complexity.

## Artifacts

- `results/data/effective_bets_prototype_returns.csv`
- `results/data/effective_bets_prototype_weights.csv`
- `results/tables/effective_bets_prototype_diagnostics.csv`
- `results/tables/effective_bets_prototype_metrics.csv`
- `results/tables/effective_bets_prototype_distinctness.csv`
- `results/tables/effective_bets_prototype_validation.csv`
