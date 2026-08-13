# Prompt log — Black-Litterman sentiment prototype

**Date:** 13 August 2026  
**Scope:** Research, specification, isolated implementation, monthly
walk-forward comparison, validation, and promotion decision for a possible
Black-Litterman fund

## Student prompts

The student asked:

> How about the Black-Litterman method?

After discussing the data needed for a classical historical market-cap prior,
the student instructed:

> Lets prototype it and see results before including it

## Research and decision context

The assistant reviewed Fischer Black and Robert Litterman's original
[Global Portfolio Optimization](https://rpc.cfainstitute.org/research/financial-analysts-journal/1992/faj-v48-n5-28),
which starts from equilibrium-implied returns and blends manager views according
to uncertainty. Goldman Sachs' institutional history of the
[Black-Litterman model](https://www.goldmansachs.com/our-firm/history/moments/1990-black-litterman-model)
was used only as background on its purpose and development.

A classical market-cap prior was rejected for this prototype because the
project has historical prices but not point-in-time shares outstanding for
equities or circulating supply for crypto. Using current values at historical
decisions would create look-ahead error. The prototype therefore uses a
transparent modified specification: the existing Equity Risk-Parity weights
are the neutral reference and are reverse-optimised into implied returns. This
is labelled a Risk-Parity Black-Litterman reference, not a historical market
equilibrium portfolio.

## Specification fixed before the real-data result

- Equity only, because the supplied headlines and sector classifications cover
  equities and no crypto sentiment is invented.
- Monthly rebalancing, 252 prior equity trading observations, 2021–2023 live
  sample, 0% risk-free rate, long-only, fully invested, 10% individual cap, and
  the existing 10 bp turnover cost.
- Risk-aversion coefficient `2.5` and Black-Litterman `tau=0.05`.
- One non-overlapping equal-weight basket view for each of the ten sectors.
- Each sector view begins at its prior-implied return and is shifted by the
  cross-sectional z-score of the previous observed trading day's raw
  finance-VADER sector sentiment.
- Primary shift: 2% annual expected sector-basket return per one sentiment
  z-score. Pre-declared 1% and 4% paths are sensitivities, not alternatives from
  which the best result is selected.
- The previous day's coverage-confidence index controls view uncertainty. A
  zero-confidence or zero-direction view is omitted and confidence is capped at
  95% for numerical stability.
- Posterior expected returns feed a constrained quadratic-utility optimiser
  using the unchanged covariance matrix and asset constraints.
- A like-for-like direct coverage-aware exponential tilt is applied to the same
  Risk-Parity reference for comparison.
- The approved four methods and 12 deployed funds remain unchanged.

## What the assistant produced

- Pure view-matrix, posterior-return, confidence-uncertainty, and constrained
  utility functions in `src/black_litterman.py`.
- A monthly, drift-aware, cost-adjusted comparison engine in
  `src/black_litterman_experiment.py`.
- A standalone runner, five synthetic tests, and six prototype-only CSV
  artifacts. None of these artifacts is loaded by the Streamlit app.
- Typed adjustable settings in `ModelConfig` for risk aversion, tau, primary
  annual view scale, view-scale sensitivities, and the confidence cap.

## Errors found and corrections

The first runner attempt stopped before producing results because the local
optional NLTK VADER lexicon was absent. Rescoring was unnecessary: the approved
leakage-safe `coverage_adjusted_sentiment.csv` already exists as a validated
project artifact. The runner was changed to consume that exact committed signal
artifact, avoiding a new dependency and any accidental score variation.

The first complete model run revealed that the initial view matrix contained
ten sector-versus-rest views even though only nine were linearly independent,
while their view errors were treated as independent. This duplicated
cross-sector information and overstated the tilts. The output was rejected.
The assistant replaced it with ten non-overlapping sector-basket views, each
expressed as a shift from its own prior-implied return. Cross-sectional
sentiment z-scores remain centred, so positive sectors are raised and negative
sectors lowered. This was a mathematical correction rather than a parameter
change made to improve the outcome. All reported results below use the corrected
matrix.

## Corrected real-data result

All figures are net of the existing 10 bp turnover cost and cover the identical
2021–2023 Equity live sample.

| Path | Annualised return | Volatility | Sharpe | Maximum drawdown | Average monthly turnover | Latest holdings |
|---|---:|---:|---:|---:|---:|---:|
| Risk-Parity reference | 9.83% | 14.53% | 0.718 | -18.51% | 5.87% | 50 |
| Direct coverage-aware tilt | 8.27% | 14.51% | 0.620 | -18.71% | 13.78% | 50 |
| Black-Litterman, 1% sensitivity | 3.32% | 15.04% | 0.292 | -24.44% | 50.12% | 23 |
| Black-Litterman, 2% primary | 1.01% | 15.74% | 0.143 | -25.72% | 65.10% | 14 |
| Black-Litterman, 4% sensitivity | -1.18% | 16.67% | 0.012 | -28.60% | 72.73% | 13 |

Trading costs do not explain the main result. Before costs, the primary 2% path
returned 1.81% annually with a 0.192 Sharpe, versus 9.91% and 0.723 for the
Risk-Parity reference. The primary path displaced an average 105.16% of total
asset weight from the neutral target at each monthly decision. Across all 36
decisions it produced 88 asset-cap observations and 788 numerical zero weights
out of 1,800 asset-rebalance rows. Its latest portfolio held 14 stocks, with
five at the 10% cap.

## Checks performed

- Five synthetic tests cover sector-basket construction, posterior direction,
  confidence response, no-view prior recovery, constrained allocation, and
  future-signal isolation.
- Five paths and 180 monthly path-rebalances completed with zero solver,
  estimation-timing, signal-timing, weight-sum, or cap failures.
- The recomputed Risk-Parity daily path and every target vector exactly match
  the approved Risk-Parity fund used elsewhere in the project.
- The largest weight-sum residual was `4.44e-16`, below the `1e-7` tolerance.
- A second corrected run produced byte-for-byte identical returns, weights,
  diagnostics, metrics, distinctness, and validation artifacts.
- Focused regression tests, lint, diff checks, and the hand-in checker are run
  after documentation.

## Interpretation and recommendation

The prototype should **not be included in the app or promoted as a fifth
method**. It is distinct, deterministic, feasible, and leakage-safe, but every
pre-declared Black-Litterman scale underperforms Risk Parity and the direct
sentiment tilt. Larger views monotonically worsen return, Sharpe, drawdown,
turnover, and concentration in this sample.

The diagnostic exposes an important conceptual problem: coverage confidence
measures whether sector news is broad and evenly distributed; it does not prove
that sentiment predicts returns. Treating coverage values averaging about 66%
as return-view confidence gives a noisy one-day sentiment observation too much
authority. The negative result is therefore evidence against this mapping, not
against every possible Black-Litterman application.

A future low-confidence or smoothed-signal variant would be an adaptive
follow-up after seeing these results. It may be useful as an explicitly
exploratory robustness exercise, but it cannot replace the failed pre-specified
prototype or be reported as untouched out-of-sample evidence.

## Artifacts

- `results/data/black_litterman_prototype_returns.csv`
- `results/data/black_litterman_prototype_weights.csv`
- `results/tables/black_litterman_prototype_diagnostics.csv`
- `results/tables/black_litterman_prototype_metrics.csv`
- `results/tables/black_litterman_prototype_distinctness.csv`
- `results/tables/black_litterman_prototype_validation.csv`

## Student review still required

The student should decide whether the negative prototype belongs in the report
as a concise innovation/critical-reflection experiment. The assistant's
recommended product decision is to leave both Black-Litterman and PCA Effective
Bets outside the investor-facing fund menu.
