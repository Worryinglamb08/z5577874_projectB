# Prompt log — Phase 6 exhibits and evidence reconciliation

**Date:** 13 August 2026  
**Scope:** Report tables, complete fact sheets, coverage diagnostic, exhibit
catalog, claim provenance, numerical reconciliation, and final visual review

## Prompt

The student instructed:

> Move on to phase 6

## What the assistant produced

- Added a compact report-facing performance table for all 12 monthly funds. It
  includes net growth, CAGR, volatility, Sharpe, drawdown, turnover, effective
  asset count, and equal-weight benchmark return difference.
- Expanded each fact-sheet record with complete current non-zero holdings,
  cumulative turnover, total simulated transaction cost, HHI, effective asset
  count, non-zero holdings count, top-ten concentration, benchmark identity,
  tracking error, information ratio, and a historical-evidence limitation.
- Added a ten-panel Word/A4 coverage-confidence chart with daily values and a
  21-day rolling mean, plus a machine-readable sector summary.
- Added a plain-VADER versus finance-VADER validation table that distinguishes
  score changes, label changes, and neutrality without treating fewer neutral
  labels as proof of accuracy.
- Added an eight-exhibit catalog linking each investor question to its PNG,
  caption, backing data, and automated validation artifact.
- Added a nine-row findings sheet linking each candidate report claim to its
  displayed values, units, exact source artifact, source filter, and field.
- Added a Phase 6 validation contract covering fact sheets, figures, claims,
  source existence, upstream validations, and finite report values.
- Added generated-artifact regression tests for the evidence contract, report
  metric identity, and complete holdings disclosure.
- Updated the project roadmap and README to record Phase 6 completion.

## What was wrong or risky

- The first end-to-end attempt correctly failed the new provenance gate because
  the coverage-dispersion claim cited the Phase 6 summary file before that file
  existed. The claim now cites the underlying daily sector index, removing the
  circular dependency.
- The first manual visual pass found crowded and edge-adjacent labels in the
  risk/return exhibit that automated layout checks missed. Family-and-method-
  specific label offsets replaced the generic offsets, and the chart was
  regenerated and re-inspected.
- The late-December decline in every rolling confidence line initially looked
  suspicious. Direct inspection of the daily data confirmed that the headline
  evidence ends before the final market dates. Explicit no-news zeros therefore
  make the decline genuine and important for users, not a charting defect.
- A top-ten holdings string alone is not a complete fact sheet for a fund with up
  to 60 assets. The fact-sheet artifact now includes every current non-zero
  holding while retaining the shorter top-ten field for app display.

## Key reconciled findings

- The menu contains 12 primary monthly funds.
- Combined Risk Parity has the highest combined net Sharpe, approximately 0.883.
- Combined Equal Weight has the highest combined net CAGR, approximately 15.04%.
- Daily Maximum Sharpe has a higher diagnostic Sharpe than monthly but about
  4.24 times its annualised turnover; monthly remains the Risk Parity winner.
- The finance lexicon changes 9,564 compound scores and 5,778 polarity labels,
  reducing the neutral share from 49.57% to 46.64%.
- Mean coverage confidence ranges from 0.39 for Materials to 0.82 for Consumer.
- The coverage-aware fusion lowers net annualised return by about 0.67 percentage
  points and Sharpe by about 0.051, while making maximum drawdown about 0.77
  percentage points shallower.

## Checks performed

- The complete pipeline rebuilt successfully and reported 8 reconciled exhibits,
  12 reconciled fact sheets, and 9 traced findings.
- All nine rows in `phase6_validation_summary.csv` pass.
- Every fact-sheet metric matches the corresponding performance row; every
  latest date, complete holdings vector, HHI, and weight sum matches the weight
  history.
- Every figure has a PNG, complete caption context, backing artifact, and a
  passing automated validation record.
- Every claim source path exists and all Phase 2–5 upstream validation tables
  remain green.
- All eight final figures were inspected manually at report size. The detailed
  record is `ai/PHASE_6_FIGURE_REVIEW.md`.
- The final test, lint, and whitespace-check results should be read from the
  verification section below rather than inferred from implementation success.

## Verification

- The focused Phase 6 generated-artifact tests pass 2 of 2.
- The complete Project B suite passes 51 tests in the verified local build
  environment.
- Ruff passes across every Python file added or changed for Phase 6.
- `git diff --check` reports no whitespace errors in the project.
- A repository-wide Ruff scan also reports unrelated pre-existing formatting
  findings in the supplied `src/data_access.py`, starter `streamlit_app.py`, and
  `scripts/check_handin.py`. Those files were preserved because Phase 6 does not
  authorise cleanup of the provided app and data-access scaffolds.
- The full pipeline completed successfully after the coverage-claim provenance
  correction and printed the expected Phase 6 summary.
