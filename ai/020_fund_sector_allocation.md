# Prompt log — Fund-details sector allocation

**Date:** 13 August 2026  
**Scope:** Latest target-weight aggregation, sector pie chart, Fund details
layout, and validation

## Student prompt

The student requested:

> In the fund details can we add sector wise allocation as well. It should be a pie chart

## Data decision

The deployed app already loads two relevant precomputed artifacts:

- `results/data/fund_weights.csv` contains every fund's latest target weights
  and asset class; and
- `results/data/fusion_weights.csv` contains the supplied sector classification
  for all 50 equity tickers.

The sector chart therefore requires no raw-data access, VADER scoring,
optimisation or backtest recomputation. The app deduplicates the precomputed
asset-sector pairs, joins them to the selected fund's latest target vector and
sums target weights within sector.

No sector taxonomy was supplied for cryptoassets. Crypto exposure is therefore
shown honestly as a separate **Crypto** slice rather than assigning invented
equity-style sectors. Consequently:

- an Equity fund shows its represented equity sectors;
- a Crypto fund shows one 100% Crypto slice; and
- a Combined fund shows its equity sectors plus one Crypto slice.

## Change made

- Added a pure, validated `sector_allocation` aggregation in `src/app_logic.py`.
- Added a Stockist-styled Plotly pie chart with stable sector colours, inside
  percentage labels, exact hover weights and a sector legend.
- Placed the sector pie beside the existing latest-holdings bar chart on Fund
  details.
- Moved the complete target-weight table beneath both charts and retained the
  existing CSV download.
- Added visible copy explaining the supplied equity mapping and Crypto bucket.

## Legend refinement

The student then observed that the vertical sector key occupied part of the pie
and requested it at the bottom in two columns. The legend is now horizontal and
placed beneath the plotting area. Each legend entry receives 48% of the
available width, creating two stable columns even when sector labels differ in
length. The chart height and bottom margin were increased to reserve a separate
165-pixel legend area, preventing overlap with the pie and its percentage
labels.

After seeing the two-column result, the student requested a three-column trial.
Legend entries now receive 32% of the available width, producing three columns
and four rows for a Combined fund's 11 entries. The chart height was reduced
from 540 to 500 pixels and the reserved bottom margin from 165 to 125 pixels;
the pie's effective plotting height remains unchanged.

The student then requested that the adjacent holdings card match the sector
card's height. The holdings chart canvas was increased from 430 to 500 pixels,
matching the pie exactly while retaining equal Streamlit column widths.

## Validation

- Equity Equal Weight: 10 sector slices summing to exactly 100%.
- Crypto Equal Weight: one Crypto slice summing to exactly 100%.
- Combined Equal Weight: 11 slices summing to exactly 100%.
- Added aggregation tests for all three asset families, a focused pie-chart
  test, and a Streamlit test confirming that Fund details renders the chart.
- The chart test verifies the bottom horizontal legend, fractional three-column
  entry width and reserved lower margin.
- A focused test enforces equal 500-pixel heights for the holdings and sector
  charts.
- App, logic and chart tests: 27 passed.
- Ruff passed for all changed Python files.
- `git diff --check` passed.
