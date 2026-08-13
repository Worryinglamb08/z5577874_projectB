# Prompt log — Minimum-CVaR prototype

**Date:** 14 August 2026  
**Scope:** Pre-specified historical Expected Shortfall method, monthly
walk-forward comparison, tail-risk evidence, validation and product decision

## Student prompts

The student first asked whether CVaR was similar to an existing method. After
the distinction between tail-loss minimisation, overall variance minimisation
and cluster risk diversification was explained, the student instructed:

> Prototype it

## Pre-specified experiment

Before examining performance, the prototype fixed:

- historical CVaR, also called Expected Shortfall, at 95% confidence;
- the Rockafellar-Uryasev linear-program formulation with one loss scenario per
  trailing return observation;
- no expected-return target and no sentiment input;
- long-only, fully invested weights;
- the existing 10% equity cap, 25% crypto cap and 30% Combined crypto-sleeve
  cap;
- the unchanged 252-observation Equity/Combined and 365-observation Crypto
  trailing windows;
- first-of-month walk-forward decisions using returns strictly before the first
  return earned under each target;
- the unchanged 10 basis-point turnover cost and drifted pre-trade turnover;
  and
- Minimum Variance and HRP as controlled defensive comparators in Equity,
  Crypto and Combined families.

The 95% setting leaves approximately 13 tail observations in a 252-day window
and 19 in a 365-day window. It was not selected by testing alternatives against
the final out-of-sample result.

## Real-data result

All performance figures are out of sample from 2021 through 2023 and net of the
existing turnover-cost assumption.

| Family | Method | Return | Volatility | Sharpe | Maximum drawdown | Daily 95% CVaR | Average monthly turnover |
|---|---|---:|---:|---:|---:|---:|---:|
| Equity | Minimum Variance | 5.67% | 12.50% | 0.504 | -15.72% | 1.73% | 14.52% |
| Equity | HRP | 8.17% | 13.68% | 0.642 | -17.44% | 1.92% | 14.72% |
| Equity | Minimum CVaR | 3.53% | 12.95% | 0.333 | -16.23% | 1.76% | 22.88% |
| Crypto | Minimum Variance | 69.49% | 76.91% | 1.072 | -72.87% | 9.21% | 15.92% |
| Crypto | HRP | 42.40% | 77.04% | 0.848 | -78.14% | 9.48% | 13.05% |
| Crypto | Minimum CVaR | 50.79% | 78.14% | 0.915 | -74.40% | 9.31% | 14.31% |
| Combined | Minimum Variance | 5.67% | 12.52% | 0.504 | -15.85% | 1.74% | 14.64% |
| Combined | HRP | 9.61% | 13.95% | 0.727 | -17.91% | 1.96% | 13.12% |
| Combined | Minimum CVaR | 4.66% | 13.18% | 0.412 | -16.54% | 1.80% | 23.77% |

## Interpretation

CVaR is not merely Minimum Variance under another name. Mean L1 target-weight
distances from Minimum Variance are 0.572 for Equity, 0.385 for Crypto and 0.591
for Combined; all exceed the predeclared 0.05 economic-distinctness threshold.
Return correlations are high but not identical at 0.956, 0.979 and 0.946.

However, distinctness did not produce a better defensive product in this
sample. Minimum Variance has lower realised daily 95% CVaR, shallower maximum
drawdown and higher Sharpe in every family. CVaR also raises average monthly
turnover materially for Equity and Combined. Its targets are more concentrated:
the latest CVaR portfolios hold 17 of 50 Equity assets, 5 of 10 Crypto assets
and 17 of 60 Combined assets, compared with HRP's broad positive holdings.

CVaR does improve tail loss and drawdown relative to HRP in all three families,
and it improves return and Sharpe relative to HRP for Crypto. That is not enough
to justify a sixth production method because Minimum Variance already supplies
a stronger low-risk role with lower realised tail loss and simpler covariance-
based communication.

The Combined CVaR portfolio is also barely multi-asset in practice: its crypto
sleeve averages 0.78%, ranges from 0% to 4.79%, and is 0% at the latest target.
Like Combined Minimum Variance, direct downside minimisation strongly penalises
the supplied crypto return history despite the permitted 30% maximum sleeve.

The result is plausible rather than contradictory. CVaR minimises average loss
in the worst scenarios of each trailing estimation window. With only roughly
13–19 tail observations, the selected assets can change abruptly as individual
crash days enter or leave the window. This produces concentrated, less stable
targets and higher turnover; minimising past-window tail loss does not guarantee
the lowest tail loss in the next out-of-sample month.

## Validation

- Nine comparison paths and 324 monthly decisions completed without solver,
  temporal-order, weight-sum or bound failures.
- Maximum target-weight sum residual was approximately `2.27e-13`, below the
  `1e-7` tolerance.
- Five synthetic tests cover a known tail-loss preference, asset and crypto-
  sleeve caps, solver diagnostics, exact determinism and future-return
  isolation.
- Minimum Variance and HRP metrics reconcile exactly to the primary 15-fund
  artifacts, confirming that only the new method changed.
- The comparison figure passed the selected Word/A4 context, label, layout,
  tick, readability and non-blank checks and was visually inspected.
- The Streamlit app and primary `fund_returns.csv`, `fund_weights.csv` and
  performance table were not changed.

## Artifacts

- `results/data/cvar_prototype_returns.csv`
- `results/data/cvar_prototype_weights.csv`
- `results/tables/cvar_prototype_diagnostics.csv`
- `results/tables/cvar_prototype_metrics.csv`
- `results/tables/cvar_prototype_distinctness.csv`
- `results/tables/cvar_prototype_validation.csv`
- `results/figures/cvar_prototype_comparison.png`
- `results/figures/cvar_prototype_comparison.caption.md`
- `results/tables/cvar_prototype_figure_validation.csv`

## Recommendation

Retain Minimum CVaR as documented experimental evidence and do not add it to
the app's primary fund menu. The negative inclusion decision is itself useful:
the method was motivated, implemented under controlled conditions and rejected
because the measured tail-risk and implementation evidence did not improve on
the existing Minimum Variance fund.
