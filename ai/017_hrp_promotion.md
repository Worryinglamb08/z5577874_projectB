# Prompt log — Hierarchical Risk Parity promotion

**Date:** 13 August 2026  
**Scope:** Student product decision, primary-menu expansion, complete artifact
rebuild, app integration, documentation, and regression validation

## Student prompt

After reviewing the isolated HRP prototype, the student instructed:

> Results seems fair for a low risk, add it.

## Student decision and interpretation

The student accepted HRP as a differentiated lower-risk option. This promotes
the existing prototype without changing its pre-registered construction,
constraints, timing, cost assumption, or evidence period.

HRP is positioned as a **cluster-diversified, lower-risk method**, not as an
outperforming method. In the 2021–2023 sample it lowered volatility and made
maximum drawdown shallower than Risk Parity in every asset family, but also
lowered return and Sharpe and increased average monthly turnover. The app and
report evidence must preserve that trade-off.

## Primary product change

The approved menu expands from 12 to **15 monthly funds**:

- three asset families: Equity, Crypto and Combined;
- five portfolio methods: Equal Weight, Minimum Variance, Maximum Sharpe, Risk
  Parity and Hierarchical Risk Parity; and
- one HRP fund in each asset family.

The app comparison limit remains four selected funds. That is a separate
usability rule and does not limit the number of funds in the product menu.

Effective Number of Bets and Black–Litterman remain experimental and excluded
from the primary app. Their standalone artifacts are retained for the report.

## Implementation

- Added `hierarchical_risk_parity` to `DEFAULT_CONFIG.methods`.
- Reused the tested correlation-distance, deterministic single-linkage,
  quasi-diagonal ordering and recursive-bisection implementation in
  `src/hierarchical_risk_parity.py`.
- Expanded the portfolio-suite contract, app-artifact validation and evidence
  reconciliation from 12 to 15 funds and from 432 to 540 monthly fund
  rebalances.
- Added the investor-facing method label, objective explanation and a distinct
  purple chart colour.
- Updated the overview, method filters, comparison charts, risk-return chart,
  weight-history layout and report exhibits for five methods.
- Updated `AGENTS.md`, `README.md`, the project-phase record and regression
  expectations.
- Regenerated every primary portfolio and Phase 6 evidence artifact.

## Rebuilt HRP results

All figures are net of the existing 10 bp turnover cost and use the same
2021–2023 live samples as the other primary funds.

| Family | Annualised return | Volatility | Sharpe | Maximum drawdown | Average monthly turnover |
|---|---:|---:|---:|---:|---:|
| Equity HRP | 8.17% | 13.68% | 0.642 | -17.44% | 14.72% |
| Crypto HRP | 42.40% | 77.04% | 0.848 | -78.14% | 13.05% |
| Combined HRP | 9.61% | 13.95% | 0.727 | -17.91% | 13.12% |

The Combined HRP portfolio averaged only 2.57% crypto because the recursive
variance allocation penalised the high-volatility crypto cluster. It is still
technically multi-asset, but investors should understand that it behaved
predominantly like an equity portfolio in this sample.

## Validation performed

- The complete seven-phase build succeeded: 15 monthly funds and 540 validated
  fund rebalances; eight reconciled exhibits; 15 reconciled fact sheets; and
  nine traced findings.
- The standalone HRP rerun completed six comparison paths and 216 validated
  path-rebalances with all validation checks passing.
- All **101 project tests passed** in 11 minutes 46 seconds.
- All HRP-related and promotion-touched Python files passed Ruff.
- `git diff --check` passed.
- The hand-in checker passed all 21 checks. Its two reminders are to remove
  generated Python caches before zipping and to export the final Word report to
  `report/report.pdf`.
- A repository-wide Ruff scan still reports six pre-existing formatting
  findings in unchanged `scripts/check_handin.py` and `src/data_access.py`.
  These unrelated files were not modified as part of the HRP decision.

## Artifacts promoted or regenerated

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/tables/performance_metrics.csv`
- `results/tables/rebalance_diagnostics.csv`
- `results/tables/method_distinctness.csv`
- `results/tables/fund_fact_sheets.csv`
- `results/tables/report_performance_table.csv`
- `results/tables/portfolio_validation_summary.csv`
- `results/tables/phase6_validation_summary.csv`
- the four primary portfolio figures and their reconciled exhibit records

The prototype-only HRP artifacts remain available as a controlled comparison
with Risk Parity. They are not loaded separately by the app because HRP is now
present in the primary artifacts.

## Student review still required

The student should review the deployed five-method interface and ensure the
report describes HRP as a lower-risk, cluster-diversified alternative with
higher turnover and lower sample return than Risk Parity. The final report PDF
still needs to be authored/exported before submission.
