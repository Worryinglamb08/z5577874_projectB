# Prompt log — Allocation-history charts

**Date:** 14 August 2026  
**Scope:** Five-method report exhibit, Fund-details allocation history, shared
precomputed-data transformation, and validation

## Student prompt

The student supplied an example 100% stacked allocation-over-time figure and
asked:

> Next we need something like this as well for the 5 portfolio methods we have,
> would provide good insight? We could also add a similar chart to Fund Details
> in the **Largest target-weight changes at the latest rebalance section before
> the table**

## Decision

The chart adds useful evidence because it reveals whether a method maintained
stable exposures or rotated sharply between sectors. It complements the latest
holdings snapshot and weight-change table: those show one rebalance, while the
stacked bands expose the entire monthly target history.

The existing `combined_weight_history.png` report artifact was redesigned as a
five-panel figure, one panel for each promoted method. Fund details now renders
the corresponding interactive chart for the selected fund immediately before
the latest-rebalance changes table.

## Encoding and data treatment

- Equity and Combined funds use the supplied equity-sector classifications.
- Combined funds aggregate all cryptoassets into one dark Crypto band.
- Crypto-only funds show individual cryptoassets; a single 100% Crypto band
  would provide no allocation insight.
- Every date is validated to sum to 100%, and negative target weights are
  rejected.
- Bands show monthly target weights before subsequent daily drift, not realised
  holdings between rebalances.
- Sector colours are stable between the app pie chart, app history chart, and
  report figure.

## Runtime boundary

The Streamlit chart reads only committed `results/data/fund_weights.csv` and
`results/data/fusion_weights.csv`. It performs a light group-by for display; it
does not rerun the portfolio optimiser, walk-forward backtest, external data
fetch, or VADER pipeline.

## Validation

- Allocation-history tests cover Equity, Crypto, and Combined funds across all
  36 monthly rebalance dates.
- A Plotly test verifies the 100% stacked encoding, labels, bounded vertical
  axis, and three-column bottom legend.
- A Streamlit interaction test confirms that Fund details renders the chart.
- The five-panel Word/A4 report figure passed all selected automated checks and
  was manually inspected at original resolution.
- The nine-row exhibit catalogue was refreshed and all nine exhibits pass.
- The focused app, logic, chart, and Phase 6 tests passed (34 tests).
- The wider suite reached 105 passes; seven build-pipeline tests could not run
  because this environment cannot fetch the remote course bundle and does not
  have the optional local NLTK VADER lexicon. Those failures do not exercise
  the precomputed app/chart path changed here.
