# Prompt log — Phase 7 Streamlit investor app

**Date:** 13 August 2026  
**Scope:** Artifact contract, six-page Stockist Funds interface, interactive
charts, allocation calculations, runtime testing, and hand-in readiness

## Prompt

The student instructed:

> Move to phase 7

## What the assistant produced

- Replaced the raw-data starter with a thin root entrypoint and a six-page
  Stockist Funds interface: Overview, Compare funds, Fund details, Allocation
  lab, News signal, and Methods & data.
- Added a deployment-safe loader that validates 15 committed analytical CSVs,
  required schemas, the 12-fund menu, and the Phase 6 evidence status before any
  investor view renders.
- Added pure app calculations for the fund catalog, aligned comparison, complete
  latest weights, mechanical rebalance changes, monthly hypothetical fund-level
  allocation, portfolio metrics, look-through asset/class exposure, return
  correlation, holdings overlap, and disclosed coverage-evidence labels.
- Added Plotly figures for risk-return comparison, fund growth, drawdown,
  holdings, allocation growth/drawdown/exposure, sentiment, confidence, fusion,
  and the frequency-turnover experiment using the approved Stockist palette.
- Added URL-shareable state for the selected view, fund, and sector.
- Added exact filtered downloads, contextual risks, data dates, historical
  labels, cost definitions, evidence limits, equations, artifact health, and
  reproducibility instructions.
- Added pure calculation tests and Streamlit runtime tests for every active page.
- Added Plotly to the deployed requirements while keeping NLTK in the existing
  build-only requirements.

## App calculation decisions

### Hypothetical allocation

The allocation lab combines the selected funds' existing after-trading-cost
daily returns on their common dates. It resets the user-selected fund weights at
the first observation of each new month and lets them drift between those dates.
No additional fund-level trading cost is invented. If every selected fund is
crypto-only it uses the 365-day convention; otherwise it uses the common equity
calendar and 252 days. The product fee is a Stockist-controlled app setting,
defaulted to 0.12% annually, and its dollar illustration is not silently
deducted from the historical metrics.

### Look-through exposure and overlap

Each fund's latest dated target vector is multiplied by its hypothetical fund
allocation. Asset and asset-class exposures sum those products. Pairwise overlap
is the sum of the smaller latest weight for every shared underlying asset. Return
correlation uses the same common dates as the hypothetical allocation path.

### Sentiment confidence

The app displays the literal zero-to-one score, covered companies out of five,
headline count and HHI. The existing Phase 6 audit bands are translated into
text—`Thin evidence` below 0.25, `Broad evidence` at or above 0.75, and `Mixed
evidence` otherwise. No-news observations remain explicitly `No news`. These
labels describe evidence support, not classification accuracy or forecast
certainty.

## What was wrong or risky

- The first Allocation lab runtime used a `min_selections` argument that the
  installed Streamlit multiselect does not support. The every-page AppTest found
  it immediately. The app now performs an explicit two-fund validation while
  retaining the supported four-fund maximum.
- The first news-table render rounded a dataframe containing datetime columns,
  which produced harmless warnings. Rounding now applies only to numeric fields.
- The shared `fintools.apps` helpers were reviewed but not imported by the final
  project app because the Project B folder becomes its own deployment repository;
  importing a parent-repository package would fail on Streamlit Community Cloud.
  The required patterns were implemented locally in focused modules instead.
- The app must not imply that the allocation lab is a recommendation. The
  allocation remains hypothetical, while the disclosed 0.12% annual product fee
  is fixed in code rather than presented as an investor choice.
- Mixing crypto-only and equity-calendar funds requires a common-date rule. The
  app uses common observed fund dates and states the resulting 252-day convention;
  it does not forward-fill returns or mix price levels.
- Automated component tests do not establish visual quality at 320 px or whether
  a new person understands the product. The fresh-person five-task protocol
  remains open in the roadmap.

## Checks performed

- The artifact loader recognises all 15 required inputs and produces a 12-fund
  catalog with three families and four methods.
- The default allocation has finite performance, unit-sum look-through exposure,
  valid correlations, and three bounded pairwise overlaps.
- Seven pure app tests pass.
- Seven Streamlit tests pass: all six pages render without an exception or error,
  and a source scan excludes NLTK, raw-data access, portfolio building, sentiment
  scoring, and fusion-building imports from the deployed path.
- A real Streamlit server started locally on port 8517 and returned `ok` from
  `/_stcore/health`; it was then stopped cleanly.
- The complete Project B suite passes **65 tests**.
- Ruff passes across every Phase 7 Python file.
- `scripts/check_handin.py` reports **21 checks passed** and no blocking problem.
  It retains two expected reminders: remove generated Python caches before the
  final ZIP and author/export the report in Phase 9.
- The source scan finds no local absolute paths or committed secrets in the app
  implementation.

## Student review still required

Run the five tasks in `ai/APP_PRODUCT_RESEARCH.md` with a fresh participant in a
real browser. Observe rather than coach them, test desktop and mobile widths,
and record completion, mistakes, questions, the participant's recognition of
historical status, and every design correction. This human comprehension check
is the remaining Phase 7 completion gate.

## Visual-system correction after first browser review

The student's first browser screenshot exposed a material theme failure: because
the project config did not define a Streamlit theme, the host inherited dark
mode and Streamlit's red default accent while custom Stockist components assumed
a light canvas. Dark headings became nearly invisible, metric cards appeared
blank, red selected states contradicted the approved teal identity, and the
sidebar and content surfaces had no coherent hierarchy.

The app is now version `0.8` and explicitly uses Streamlit's light base theme:

- off-white page canvas `#F4F6F5`;
- white charts, tables, inputs, cards, and metric surfaces `#FFFFFF`;
- light-grey navigation rail `#E9EFF0`;
- dark ink text `#0F172A` and secondary slate text `#475569`;
- teal primary interaction colour `#0F766E` with a pale teal selected surface;
- neutral borders and dataframe headers; and
- the approved categorical chart sequence.

Scoped CSS now reinforces, rather than fights, the native theme for evidence
strips, cards, metric values, input/select surfaces, multiselect tags, bordered
containers, dataframes, expanders, buttons, links, and mobile spacing. The
authoritative visual-system and UI research notes were updated to distinguish
the off-white page canvas from white analytical surfaces.

The theme configuration is covered by a regression test, all 15 focused app
tests pass, Ruff passes, and a newly started server accepted the theme and
returned a healthy response. A browser refresh requires restarting Streamlit
because configuration changes are loaded when the server starts.

## Navigation-state correction after interaction testing

Clicking **Compare monthly funds** on Overview originally tried to assign
`st.session_state.stockist_view` after the sidebar radio using that key had
already been instantiated in the same run. Streamlit correctly rejected that
late mutation with `StreamlitAPIException`. Navigation now writes a separate
pending-view key and reruns. At the start of the next run, the app consumes that
pending value before constructing the radio, then synchronises the URL from the
rendered selection. A regression test clicks the real Overview button and
asserts that the Compare funds page renders without an exception.

## External benchmark options

The student requested S&P 500 and Nasdaq choices beside fund selection. The app
now keeps **Same-family Equal Weight** as the default strategy benchmark and adds
two optional investable market references:

- S&P 500 through the SPY ETF adjusted-close series; and
- Nasdaq Composite through the ONEQ ETF adjusted-close series.

The labels deliberately say “proxy”: SPY and ONEQ are not the official index
series. Adjusted prices were chosen so dividends, capital distributions and
splits are incorporated, unlike a price-only index comparison. The external
data are fetched during the analytical build with `yfinance`, stored in
`results/data/external_benchmarks.csv`, and loaded by the deployed app without a
runtime network request. The artifact records source, ticker, return basis and
retrieval date.

The Compare funds and Fund details views place the benchmark dropdown beside
fund selection and share it through `?benchmark=`. Excess return is recomputed
for each selected fund on exact common dates. The fact sheet also redraws the
growth-of-$1 benchmark line and discloses the selected reference, aligned sample,
observation count, annualisation convention, source and return basis. For an
external comparison, a crypto fund is restricted to shared US trading dates and
uses a 252-day convention; its primary full-calendar metrics remain separately
labelled with the native 365-day convention.

The benchmark implementation adds a build-only acquisition module, pure aligned
comparison logic, an app-artifact schema check and interaction coverage that
switches the live dropdown from SPY to ONEQ. Same-family Equal Weight remains the
main test of optimisation value; the ETF proxies provide recognisable market
context rather than replacing that controlled benchmark.

## Allocation-through-time evidence

Fund details now places a 100% stacked target-allocation chart immediately
before the latest-rebalance changes table. Equity and Combined funds aggregate
the supplied equity classifications by sector; Combined funds also show all
cryptoassets as one Crypto band. Crypto-only funds instead show individual
cryptoasset bands, because a single 100% Crypto band would add no information.
The app derives the chart only from committed `fund_weights.csv` and
`fusion_weights.csv`; it does not run an optimiser or backtest.

## Metric-card wrapping correction

A browser review of Combined historical evidence showed four metric cards being
compressed into one row. Streamlit truncated both labels and values, making the
headline evidence difficult to read. The shared metric renderer now uses no more
than two cards per row at every viewport. Four measures render as a two-by-two
grid; the five-measure allocation summary renders as 2–2–1. A focused layout
test records each requested column group and protects the `[2, 2, 1]` wrapping
behaviour.

## Allocation-weight control correction

The original fund-weight inputs looked like plain numeric steppers, and the
intermediate correction used several independent range sliders. Neither matched
the requested proportion-control metaphor. The lab now uses one local,
bidirectional Streamlit component containing a 100%-wide segmented bar. A
divider changes only the two neighbouring fund segments in whole percentage
points, so the combined allocation cannot leave 100%.

The component uses no runtime CDN or third-party slider package. It supports
mouse and touch dragging plus keyboard arrows, Shift+arrow, Home and End; exposes
each divider as an accessible slider; shows a Stockist-coloured legend with exact
percentages; and collapses the legend to one column on narrow screens. The bar
spans the full content width above the balance, fee and evidence panels. Changing
the selected fund set creates a matching component state, while Reset restores
the equal-allocation example before the component is mounted.

Streamlit was raised to version 1.59 or later because the implementation uses
the official inline bidirectional component API. Validation rejects malformed
state, AppTest confirms a single component is mounted instead of multiple native
sliders, a 20/30/50 state remains valid, and Reset restores 34/33/33 without a
runtime exception.

## Fixed product-fee correction

The student subsequently instructed:

> Okay, next I'd like to remove the annual product fee % from the Allocation
> lab since that is not something a user would select. It would be something
> the fund sets, make it a setting in the code, default it to 0.12%

The user-editable product-fee number input was removed. A typed, immutable app
setting now stores the annual fee as `0.0012`, equivalent to 0.12%. The
Allocation lab continues to disclose the resulting annual dollar estimate for
the chosen illustrative balance, but labels the percentage as fixed by the fund
and does not deduct it from historical performance. App tests verify that the
balance is the only number input, the default A$10,000 illustration reports A$12,
and invalid configured rates are rejected.

## Customer-facing navigation correction

The student subsequently decided:

> I'd remove it from the site since it can be considered a funds proprietary
> knowledge. We can mention the experiment on the report

The **Methods & data** destination was removed from the sidebar and app route.
Its detailed configuration, frequency-versus-turnover experiment, equations,
artifact inventory and reproduction controls remain available in the project
evidence and will be discussed in the report instead. The app retains essential
investor disclosures on the relevant comparison, fact-sheet, allocation and
news-signal views, including historical status, risk, benchmark, holdings, fees,
cost basis and evidence limits. A regression test confirms that an old shared
`?view=Methods%20%26%20data` URL safely falls back to Overview.

## Fund-comparison control hierarchy correction

The student observed that family and method multiselects visually overwhelmed
the actual fund choice and could be mistaken for chart controls. The page now
puts **Selected funds** and **Benchmark** in the first row. Asset family and
portfolio method are rendered beneath them as multi-select filter pills inside
a bordered **Filter available funds** panel. The risk–return chart keeps the
complete 12-fund context and highlights only the selected funds, so displayed
comparison evidence is controlled by the current Selected funds and Benchmark.

The student then increased the comparison limit from three to four selected
funds. The fourth growth path uses a distinct accessible series colour.

After testing the interaction, the student corrected the filter behaviour: a
fund should not remain selected after its family or method is excluded. Filters
now prune every non-matching selected fund before the selection widget is
instantiated, avoiding Streamlit's post-instantiation session-state error. The
table and charts then update from the remaining selection. The runtime
regression test selects four funds, narrows to Equity plus Minimum Variance, and
confirms that only Equity Minimum Variance remains selected.

The student then prioritised the visual evidence sequence. The selected-fund
growth-of-A$1 chart now appears immediately after the controls, followed by the
return-versus-volatility chart. The aligned exact-metrics table and its download
come last, providing numerical detail after the two visual comparisons.

## Allocation-benchmark extension

The Allocation lab now has its own URL-shareable benchmark control. Equal
allocation across the same selected funds remains the default because it
isolates whether the chosen fund weights added value. Optional SPY and ONEQ
total-return proxies provide recognisable market context.

For either external option, the chosen allocation and benchmark are joined on
exact common US trading dates, both growth paths are restarted at one, and all
comparison metrics use a 252-day convention. The lab displays aligned allocation
return, benchmark return, their annualised difference, tracking error, the exact
sample, observation count, source and return basis. It also warns that an equity
index proxy may not match a multi-asset allocation's composition or risk.

The control reads the already committed external-benchmark artifact and never
downloads data or reruns the portfolio backtest in Streamlit. When the default
34/33/33 weights are compared with exact thirds, the lab now explains why the
two lines substantially overlap.

## News-signal metric simplification

The student found **Companies covered** and **Evidence status** more confusing
than clarifying. Both were removed from the News Signal headline cards and from
the expandable exact-observation tables. The page retains the literal
zero-to-one Coverage Confidence measure because it is the value that scales the
fusion signal, alongside headline count and HHI as optional table detail. This
is a presentation change only; sector sentiment, confidence calculations and
the precomputed fusion experiment are unchanged.

## Sidebar and weight-download refinement

The sidebar navigation now uses five real, full-width Streamlit buttons with
Material icons instead of a styled radio control. The selected destination uses
a pale teal row, dark teal label and left accent rule; unselected destinations
remain quiet until hover. Session-state and URL synchronisation are handled
explicitly by the existing pending-view navigation path. Sidebar header and
content padding are reduced so the product title, subtitle and navigation begin
near the top of the rail. A full-height flex column pushes the monthly-review
note and version/data line to the bottom without removing either from document
flow, preventing the footer from overlapping the navigation.

On Fund details, **Download complete weight vector** now shares the row above the
table with the **Complete target-weight table** heading. This associates the
download with the artifact it exports and removes the detached button beneath
the table.

## Stockist News Fear and Greed prototype

The News Signal page now adds a market-wide view above the required sector
evidence. The precomputed `market_news_index.csv` constituent-weights the ten
sector indices, which is equivalent to equal-weighting the fixed 50-stock
universe because each sector contains five supplied stocks. Ticker-days without
headlines retain the project's explicit neutral-zero treatment.

The upper panel directly maps VADER from `[-1, +1]` to `[0, 100]` and plots the
selected 21- or 63-trading-day mean. Its visible axis is explicitly disclosed as
zoomed to 44–66. The lower panel shows daily full-sample z-scores with positive
and negative bars and includes headline count and covered-stock count in hover
evidence. The z-score is labelled as a descriptive standardization over the
fixed 2020–2023 sample and is not fed into the lagged coverage-aware fund
experiment.

Finance-adjusted daily levels are above 50 on 99.304% of dates; all valid 21-day
means are above 50. The latest 21-day value is 53.26 (Neutral) and sits above
only 3.3% of comparable rolling observations. This persistent positive raw
baseline is retained visibly rather than normalized away, which explains why
the standardized panel is needed. Recent low standardized readings also occur
with only one of 50 stocks carrying aligned news, so the app warns that low
relative readings can reflect thin evidence rather than unambiguous fear.
