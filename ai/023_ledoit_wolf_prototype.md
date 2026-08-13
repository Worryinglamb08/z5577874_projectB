# Prompt log — Ledoit–Wolf covariance prototype

**Date:** 14 August 2026  
**Scope:** Controlled covariance-estimator experiment, walk-forward paths,
conditioning and stability diagnostics, and product decision support

## Student prompts

The student supplied a description of modern portfolio construction and asked
whether it represented a custom method. After the assistant identified
covariance shrinkage as the most relevant untested component, the student asked:

> So Ledoit–Wolf covariance shrinkage is what you suggest doing?

The student then instructed:

> Prototype it

## Research and design decision

Ledoit and Wolf developed linear shrinkage to reduce the estimation error and
poor conditioning of large sample covariance matrices. The prototype uses the
standard `sklearn.covariance.LedoitWolf` implementation, which shrinks the
sample covariance toward a scaled identity target and estimates the shrinkage
intensity from each trailing window.

Primary reference: Olivier Ledoit and Michael Wolf, “A Well-Conditioned
Estimator for Large-Dimensional Covariance Matrices,” *Journal of Multivariate
Analysis* 88(2), 2004.

The test is deliberately isolated from the investor-facing menu. It compares:

```text
Reference: sample covariance + existing 1e-8 numerical ridge
Prototype: standard Ledoit–Wolf linear shrinkage covariance
```

Everything else is identical: 252-observation trailing window, first-of-month
rebalancing, long-only weights, individual caps, 30% Combined crypto cap,
0% risk-free rate, 10 basis-point turnover cost, and 2021–2023 live sample.

The first pass covered Equity and Combined, where 50 or 60 assets are estimated
from 252 observations. Four covariance-dependent methods were tested: Minimum
Variance, Risk Parity, Maximum Sharpe, and Hierarchical Risk Parity.

After reviewing that result, the student requested a separate Crypto HRP test.
Before running it, the existing adoption thresholds were frozen unchanged.
Crypto uses its native 365-day calendar and 365-observation trailing window.
No other Crypto method was added to the experiment.

## Pre-declared adoption screen

Before reading the real-data results, a matched method/family pair was defined
as a candidate only when Ledoit–Wolf:

- reduced the median covariance condition number;
- did not increase average target change by more than the larger of 0.5
  percentage points or 5% of the reference value;
- did not increase average rebalance turnover by more than the same tolerance;
- did not reduce net Sharpe by more than 0.05; and
- did not deepen maximum drawdown by more than 2 percentage points.

These are guardrails against material deterioration, not proof that every
passing pair improved economically.

## Results

All 18 paths and 648 monthly decisions passed timing, solver, feasibility,
positive-definiteness, shrinkage-range and covariance-input identity checks.
Mean shrinkage intensity was 4.62% for Equity and 5.50% for Combined. Median
condition numbers fell from 451 to 218 for Equity (51.7% reduction) and from
1,689 to 560 for Combined (66.9% reduction).

Differences below are Ledoit–Wolf minus the existing estimator. Annual return
differences are basis points; turnover is percentage points per rebalance.

| Family | Method | Return | Sharpe | Max-drawdown change | Turnover change | Mean target L1 distance |
|---|---|---:|---:|---:|---:|---:|
| Equity | Minimum Variance | +9.5 bp | +0.007 | -0.15 pp | -0.46 pp | 0.053 |
| Equity | Risk Parity | +1.0 bp | +0.000 | -0.01 pp | -0.02 pp | 0.003 |
| Equity | Maximum Sharpe | -2.7 bp | -0.003 | -0.05 pp | -0.16 pp | 0.018 |
| Equity | HRP | +74.2 bp | +0.049 | +0.95 pp | +0.06 pp | 0.211 |
| Combined | Minimum Variance | +7.1 bp | +0.006 | -0.10 pp | -0.81 pp | 0.122 |
| Combined | Risk Parity | +2.8 bp | -0.000 | -0.05 pp | -0.04 pp | 0.006 |
| Combined | Maximum Sharpe | -45.1 bp | -0.024 | -0.09 pp | -0.11 pp | 0.041 |
| Combined | HRP | +72.0 bp | +0.040 | +0.39 pp | -0.97 pp | 0.197 |
| Crypto | HRP | -515.6 bp | -0.047 | -0.59 pp | +0.04 pp | 0.115 |

A positive maximum-drawdown change means the loss became shallower. All nine
pairs meet the pre-declared guardrails, but the economic interpretation is
mixed. Equity and Combined HRP show the clearest improvements, Minimum Variance
improves modestly, Risk Parity is nearly invariant, and Maximum Sharpe does not
benefit—especially for Combined. Covariance shrinkage cannot solve the separate
instability of sample expected returns used by Maximum Sharpe.

Crypto HRP narrowly passes the unchanged guardrails but is not an economic
improvement in this sample. Ledoit-Wolf reduces its median condition number from
95.8 to 55.8, but annualised return falls from 42.40% to 37.25%, Sharpe falls
from 0.848 to 0.801, and maximum drawdown deepens from -78.14% to -78.73%.
Average turnover rises only 0.04 percentage points per rebalance. The result
supports caution about applying the high-dimensional-panel remedy automatically
to 10 cryptoassets estimated from 365 observations.

## Validation and production boundary

- The existing default estimator remains `sample_ridge`.
- The nine reference paths reconcile exactly to the committed production
  artifacts: 7,119 daily return rows and 16,200 target-weight rows have zero
  maximum numeric residual.
- Synthetic tests prove positive definiteness, improved conditioning, valid
  weights for all four methods, deterministic reruns and no future-return effect
  on an earlier target.
- Thirty-four focused portfolio, frequency, Black–Litterman, Effective Bets
  and Ledoit–Wolf tests pass; Ruff and `git diff --check` pass.
- `scikit-learn` is build-only in `requirements-dev.txt`; the deployed app still
  reads precomputed CSVs and does not estimate covariance matrices.

## Student decision

After reviewing the Crypto result, the student decided:

> I'd skip it then, I do not wish to add asset specific models. I'll note it but
> not implement it

Ledoit-Wolf therefore remains an isolated robustness experiment. It is not
promoted into any production fund, app label, fact sheet, or primary result.
All Equity, Crypto, and Combined production methods retain the same existing
sample-plus-ridge covariance specification. This preserves a consistent method
definition across asset families and avoids selectively adopting the estimator
only where the observed historical result was favourable.

The experiment can still be discussed briefly in the report as a documented
negative or mixed extension: conditioning improved in every family, Equity and
Combined HRP improved, but Crypto HRP lost 5.16 percentage points of annualised
return and 0.047 Sharpe. The result demonstrates why numerical robustness alone
does not guarantee better realised portfolio performance.

## Artifacts

- `results/data/ledoit_wolf_prototype_returns.csv`
- `results/data/ledoit_wolf_prototype_weights.csv`
- `results/tables/ledoit_wolf_prototype_diagnostics.csv`
- `results/tables/ledoit_wolf_prototype_metrics.csv`
- `results/tables/ledoit_wolf_prototype_paired_comparison.csv`
- `results/tables/ledoit_wolf_prototype_validation.csv`
