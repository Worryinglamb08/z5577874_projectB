# Prompt log — Allocation Lab benchmarks

**Date:** 14 August 2026  
**Scope:** Allocation benchmark selection, common-date comparison, relative
metrics, URL state, and Streamlit validation

## Student prompts

The student first asked why the Equal-fund reference appeared identical to the
chosen allocation. Inspection confirmed that the default 34/33/33 choice is
almost identical to the equal 33.33/33.33/33.33 reference. The student then
asked whether a benchmark would be useful and instructed:

> Can we add it

## Product decision

The Allocation Lab now offers:

1. Equal allocation across selected funds — default;
2. S&P 500 through the SPY adjusted-close total-return proxy; and
3. Nasdaq Composite through the ONEQ adjusted-close total-return proxy.

Equal selected funds remains the most controlled benchmark because it answers
whether the chosen fund weights changed the result while holding the selected
fund menu constant. SPY and ONEQ answer a different question: how the entire
hypothetical mix compared with familiar equity-market references.

## Comparison rules

- External comparisons use exact dates shared by the allocation and proxy.
- Both growth paths restart at $1 on the first common observation.
- External comparisons use 252-day annualisation.
- The displayed evidence includes aligned allocation return, benchmark return,
  annualised return difference and tracking error.
- Dates, common-observation count, source and adjusted-return basis are visible.
- A caveat states that an equity proxy may not match a multi-asset allocation's
  asset mix or risk.
- The default near-equal allocation produces an explanatory overlap message.

## Runtime boundary

The app uses the already committed `external_benchmarks.csv` artifact. It makes
no runtime network request and does not recompute fund backtests, optimisation
or VADER results.

## Validation

- Pure tests cover Equal selected funds, SPY and ONEQ.
- Chart tests confirm that the selected benchmark label appears in the growth
  figure.
- Streamlit interaction testing switches the Allocation Lab from Equal selected
  funds to SPY and verifies URL state, exact-date caption and chart traces.
- The focused logic, chart and app suite passes 35 tests; Ruff and whitespace
  validation pass.
