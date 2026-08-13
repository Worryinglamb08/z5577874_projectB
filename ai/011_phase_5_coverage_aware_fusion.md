# Prompt log — Phase 5 coverage-aware sentiment fusion

**Date:** 13 August 2026  
**Scope:** Event-audit record, coverage-adjusted signal, equity tilt, controlled
before-versus-after backtest, sensitivity, validation, and report exhibit

## Prompt

The student instructed:

> Okay record the findings with suggested solution and move to phase 5

This followed two event-level reviews requested by the student: the Utilities
sentiment spike ending 15 February 2022 and the Tech decline ending 25 October
2022.

## What the assistant produced

- Recorded both audits, their cross-ticker repetition rates, VADER edge cases,
  interpretations, and the agreed non-destructive robustness solution in
  `ai/SENTIMENT_EVENT_AUDIT.md`.
- Preserved the primary assignment-compliant index rather than changing data or
  language rules after inspecting conspicuous events.
- Replaced the fusion placeholder with a typed Phase 5 pipeline that keeps raw
  finance sentiment, coverage confidence, their same-day product, the previous
  observed sector date, and the lagged tradable value in separate fields.
- Selected Equity Minimum Variance as the fixed comparison base, consistent
  with the earlier Project B product notes. The base optimiser targets and every
  rebalance date are reused exactly.
- Fixed the primary tilt strength at `0.20` before inspecting fusion performance.
  The ten sector signals are standardised cross-sectionally at each monthly
  decision, clipped to `[-2, 2]`, mapped only to the 50 equity tickers, and
  applied with the positive multiplier `exp(0.20 * z)`. Capped proportional
  normalisation restores full investment under the original 10% equity cap. At
  the clipping boundary this permits an interpretable pre-normalisation
  multiplier range of about `exp(-0.4)=0.67` to `exp(0.4)=1.49`: material enough
  to test, but not an attempt to replace the underlying optimiser.
- Compared base, plain-VADER, finance-VADER, and coverage-aware finance variants
  over the identical 2021-01-04 to 2023-12-29 live sample with the same monthly
  dates and 10 basis-point turnover-cost assumption.
- Added labelled coverage-aware tilt-strength sensitivities at `0.10` and `0.40`.
  They are diagnostic and were not used to replace the pre-specified `0.20`
  primary result.
- Exported app-readable signal, return, and weight paths; a full comparison
  table; sensitivity and validation tables; and a Word/A4 growth comparison.
- Added synthetic tests for exact confidence multiplication and lagging, future-
  headline leakage, cap/normalisation behaviour, zero-dispersion signals, and a
  real-data end-to-end regression.

## Timing and fusion equations

For sector `s` on observed trading date `t`:

```text
coverage_adjusted[s,t] = finance_sentiment[s,t] * confidence[s,t]
tradable_signal[s,t]   = coverage_adjusted[s,t-1]
z[s,t]                 = clip(cross_sectional_z(tradable_signal[:,t]), -2, 2)
raw_weight[i,t]        = base_weight[i,t] * exp(0.20 * z[sector(i),t])
target_weight[:,t]     = capped_proportional_normalise(raw_weight[:,t])
```

The signal source date stored for every augmented target is strictly earlier
than its rebalance date. Crypto receives no news score.

## What was wrong or risky

- The first capped-normalisation guard rejected exact zero base weights even
  though the long-only base optimiser can legitimately allocate zero to an
  asset. It was corrected to allow nonnegative raw weights while still rejecting
  negative, nonfinite, or all-zero vectors.
- The first implementation of the strength-sensitivity table calculated each
  variant alone, which left its `delta_*_vs_base` fields anchored incorrectly.
  Every nonzero sensitivity is now evaluated in a two-path table containing the
  identical base.
- The first rendered log-axis figure displayed intermediate dollar values in
  scientific notation. Automated checks passed, but visual inspection caught the
  problem. Fixed dollar ticks at five-cent increments replaced the default log
  formatter and the figure was regenerated and inspected again.
- A same-sector value gives all five companies in that sector the same
  multiplier. This is intentional because the required sentiment product is a
  sector index, but it is not a stock-selection signal.
- Coverage confidence qualifies evidence breadth and concentration; it does not
  prove sentiment accuracy. Multiplication shrinks thin evidence toward zero but
  cannot repair false-positive or false-negative language classifications.
- Cross-ticker repeated headlines remain in the untouched primary signal under
  the required upstream deduplication rule. Their known effect is an explicit
  interpretation limit and planned robustness view, not silently edited away.

## Key result retained

At the fixed primary strength, coverage-aware sentiment did not improve the base
fund:

| Measure | Base | Coverage-aware | Difference |
|---|---:|---:|---:|
| Net annualised return | 5.668% | 5.002% | -0.666% |
| Net annualised volatility | 12.496% | 12.493% | approximately 0.000% |
| Net Sharpe | 0.504 | 0.453 | -0.051 |
| Maximum drawdown | -15.724% | -14.951% | +0.773% shallower |
| Cumulative turnover | 5.225 | 5.959 | +0.734 |

The tilt modestly improves the realised maximum drawdown but lowers return and
Sharpe and increases turnover. Strength `0.10` also underperforms the base; `0.40`
deteriorates further. The result is retained rather than tuned away.

## Checks performed

- Coverage-adjusted sentiment equals finance sentiment times same-day confidence
  exactly.
- The tradable value equals the previous observed sector date's adjusted value.
- Every augmented signal source date precedes the monthly rebalance date.
- Every target is finite, long-only, fully invested, and at or below the 10%
  individual equity cap.
- Every fused asset is an equity; no `-USD` crypto ticker is present.
- The reconstructed base daily gross and net returns exactly match the original
  primary Equity Minimum Variance path.
- All four primary variants use 753 common live return dates and finite metrics.
- The end-to-end script rebuilds Phases 1–5 and writes the new evidence.
- The generated fusion figure passes selected automated checks and a second
  manual visual inspection after the dollar-axis correction.
- The final complete Project B suite passes 49 tests; focused Phase 5 tests pass
  six of six. Ruff passes for every changed Python file, and `git diff --check`
  reports no whitespace errors.

## Student interpretation required

The student should explain the economic result in their own words. Defensible
points include the noisy headline proxy, sector-level rather than company-level
resolution, repetition and mixed-language errors found in the event audit, and
the added turnover from changing monthly signals. The evidence does not show
that sentiment is useless in every sample or implementation; it shows that this
pre-specified coverage-aware rule did not improve this base fund during the
supplied 2021–2023 historical simulation.
