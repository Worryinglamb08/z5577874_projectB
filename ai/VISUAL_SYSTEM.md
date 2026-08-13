# Stockist Funds — Project B Visual System

## Purpose

This is the approved visual baseline for the FINS5545 Stockist Funds Part B app,
report figures, tables, and fund fact sheets. It carries forward the student's
Project A identity and adapts it for interactive fund comparison, allocation,
sentiment, and evidence-confidence views.

`ai/UI_DESIGN_RESEARCH.md` records the research behind the interface decisions.
This file is the implementation authority: later visual changes should be made
here first and then applied consistently across the app and report.

## Product character

Stockist Funds is a calm, evidence-led systematic investment platform for
self-directed investors. It should look like a transparent research product,
not a trading terminal, brokerage feed, or promotional crypto app.

The visual system must communicate:

- repeatable investment rules;
- comparable out-of-sample fund evidence;
- risk and drawdown beside return;
- holdings, concentration, turnover, and costs;
- the difference between monthly investable funds and higher-frequency
  diagnostics; and
- the confidence and coverage limits of headline sentiment.

The app is a historical coursework prototype. Its design must never imply live
trading, live holdings, personalised advice, guaranteed performance, or evidence
beyond the supplied 2020–2023 sample.

## Design principles

1. **Evidence before decoration.** Lead with the decision, measure, unit, sample,
   and comparison.
2. **Risk beside return.** Do not make users navigate elsewhere to find the
   downside evidence qualifying a performance result.
3. **Confidence is visible.** Show data date, out-of-sample status, assumptions,
   and news-coverage quality near the relevant output.
4. **Comparison is aligned.** Peer values use the same definitions and appear in
   aligned tables or charts.
5. **Progressive detail.** Plain-language essentials appear first; equations,
   parameters, and data dictionaries remain directly accessible.
6. **Calm hierarchy.** Use spacing, alignment, type, and restrained contrast
   before colour, borders, or containers.
7. **Accessible without colour.** Text, shape, line style, position, and table
   alternatives carry meaning alongside colour.
8. **One visual question.** Every chart, card, and page has a clear purpose.
9. **Consistent interaction.** Filters, reset actions, dates, units, benchmarks,
   and selected states behave the same way everywhere.
10. **Honest uncertainty.** Negative, null, thin-coverage, and high-cost results
    remain visible and are not softened by visual treatment.

## Core colour tokens

The Part A palette remains unchanged.

| Token | Hex | Use |
|---|---:|---|
| Ink | `#0F172A` | Titles, primary text, axes, high-emphasis values |
| Secondary ink | `#475569` | Supporting text, dates, captions, benchmark lines |
| Page canvas | `#F4F6F5` | Off-white application background |
| Surface | `#FFFFFF` | Charts, tables, metric cards, inputs, and content panels |
| Sidebar | `#E9EFF0` | Light neutral navigation rail |
| Soft surface | `#EEF2F3` | Grouped controls and alternating rows |
| Rule | `#D7DEE3` | Dividers, borders, inactive controls, grid lines |
| Accent | `#0F766E` | Selected state, primary action, focal series |
| Accent soft | `#CCFBF1` | Selected-card background, quiet information state |
| Warning | `#B45309` | Thin evidence, high turnover, material caveat |
| Adverse | `#C2410C` | Drawdown, material loss, failed validation |

### Supporting categorical sequence

Use categorical colour only when several distinct series genuinely require it:

1. `#0F766E` — Stockist accent
2. `#0072B2` — blue
3. `#E69F00` — orange
4. `#CC79A7` — purple-pink
5. `#56B4E9` — light blue
6. `#D55E00` — vermilion-orange

Do not use more than five or six categories in one view. Prefer direct labels,
filters, a table, heatmap, or small multiples when more categories exist.

### Colour meanings

- Accent means **selected or focal**, not automatically positive.
- Secondary ink means **benchmark or context**.
- Warning means **review this evidence or assumption**.
- Adverse means **measured downside or failed validation**.
- Positive and negative cannot rely on green/red alone.
- Confidence states must contain literal text such as `Broad`, `Mixed`, `Thin`,
  or `No news`; colour may reinforce but never replace the label.
- Separate adjacent categorical fills with white space or a visible border.
- Do not place small text directly on categorical chart colours.

### Contrast and themes

- Use white on Accent only for short, sufficiently large button or chip text.
- Use Ink on Accent soft and Soft surface.
- Maintain at least WCAG AA contrast for text and interactive components.
- The app explicitly locks Streamlit to its light base theme. Do not inherit the
  browser or operating-system dark preference: the custom Stockist surfaces and
  charts are designed for the off-white canvas. A dark theme is not required and
  should not be added unless every chart, table, control, and semantic colour is
  redesigned and retested.

## Typography

### Font stack

- App: `Aptos`, `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`,
  `sans-serif`.
- Do not require a network font for the deployed app.
- Word report: Aptos, with Arial fallback.
- Generated report figures: DejaVu Sans for portable rendering.

### Hierarchy

| Level | Desktop guidance | Use |
|---|---:|---|
| Page title | 30–34 px, semibold | One per page |
| Lead | 17–19 px, regular | Page purpose or key interpretation |
| Section title | 20–24 px, semibold | Major page region |
| Card title | 15–17 px, semibold | One card purpose |
| Body | 15–17 px, regular | Explanations and labels |
| Supporting text | 13–14 px minimum | Dates, notes, sources, assumptions |
| Primary metric | 24–32 px, semibold | Limited summary measures |

- Use sentence case throughout.
- Prefer left alignment; centre only compact standalone elements.
- Use tabular numerals where available for metrics and comparison tables.
- Keep body line length near 65–80 characters where practical.
- Never shrink essential labels to force a layout to fit.

## Spacing, sizing, and surfaces

- Build layouts on an 8 px rhythm.
- Use 8 px between tightly related label/value pairs.
- Use 16 px within component groups.
- Use 24–32 px between major sections.
- Main desktop content width: approximately 1,180–1,280 px.
- Use a twelve-column mental grid implemented through simple Streamlit columns.
- Use no more than three content columns; most analytical views use one or two.
- Card corner radius: 6–10 px.
- Card border: one pixel Rule.
- Use no shadow or one extremely subtle shadow only where elevation is necessary.
- Do not use gradients, glass effects, bevels, textured backgrounds, or decorative
  chart containers.

## Global application shell

### Primary navigation

Use a labelled, collapsible Streamlit sidebar for five destinations:

1. Overview
2. Compare funds
3. Fund details
4. Allocation lab
5. News signal

- Place the compact monochrome Spartan brand mark above the `Stockist Funds`
  name. Centre the mark within the sidebar at approximately 88 px wide while
  retaining the left alignment of the name, subtitle and navigation. Use the
  local transparent PNG so the mark inherits the sidebar background cleanly.
- Use visible text labels. Icons are optional and never replace text.
- Render each navigation choice as a large, full-width button row with an icon
  and visible label; do not expose radio circles. The selected destination uses
  a pale accent surface, dark teal text and a left accent rule. Unselected rows
  remain transparent and gain a quiet surface on hover. Left-align the icon and
  label group consistently and use `1rem` navigation labels.
- Keep the title, subtitle and navigation close to the top of the sidebar.
- Use a full-height flex layout to push the monthly-review note and version/data
  metadata to the bottom. On short viewports the sidebar may scroll, but the
  metadata must remain in document flow and never overlap navigation.
- Preserve the selected fund when moving from comparison to fund details.
- Top-level tabs must not be used as page navigation.
- Short tabs or segmented controls are acceptable within a page only for closely
  related views that do not need simultaneous comparison.

### Page header

Every page begins with:

1. page title;
2. one-sentence purpose;
3. a persistent evidence strip; and
4. any page-level filters.

Default evidence-strip wording:

```text
Historical out-of-sample simulation · Monthly primary specification ·
Data through 2023 · Educational prototype, not financial advice
```

Use a soft neutral surface with Ink text. This is a status statement, not a
bright warning banner.

### Footer

The app footer should include:

- FINS5545 coursework prototype;
- data period and last artifact-build date;
- methodology and data-download links;
- historical/no-advice statement; and
- Stockist Funds version identifier.

Do not add social-media links, promotional signup copy, or fabricated contact
details.

## Component system

### Buttons

- One primary action per page region: Accent fill, white text.
- Secondary action: white/Soft surface, Ink text, Rule border.
- Tertiary action: text link with visible focus and underline on hover/focus.
- Destructive or reset actions should say exactly what they do; reset is not
  styled like data loss.
- Button text uses a verb and object: `Compare selected funds`, `Reset filters`,
  `Download filtered data`.
- Do not use `Invest now`, `Buy`, or `Deposit` in the coursework prototype.

### Filters and inputs

- Place related page filters in one Soft surface control strip.
- Order filters from broad to narrow: family, method, cost view, period.
- Use one segmented allocation bar for hypothetical fund weights. Draggable
  dividers transfer whole percentage points between neighbouring funds, making
  allocation size visible while mathematically preserving a 100% total.
- Label every control above or beside it; never rely on placeholder text.
- Give every filter group a visible reset.
- Use stable defaults and show the selected value in the output subtitle.
- Allocation inputs continuously show the total and a specific validation state.
- Sliders require an exact numeric companion when precision matters.

### Status chips

Use compact text chips for categorical status only:

- `Monthly primary`
- `Historical OOS`
- `Equity`, `Crypto`, or `Combined`
- `Coverage: broad`, `Coverage: mixed`, `Coverage: thin`, `No news`
- `Gross` or `After trading costs`

Chips are not buttons unless they visibly behave as controls. Do not use a chip
for every ordinary metadata value.

### Metric groups

Performance summary groups show these four metrics with equal visual weight in
a two-column grid. Never force four cards into one row: long financial labels and
values must remain visible without ellipsis at ordinary desktop widths.

1. annualised return;
2. annualised volatility;
3. Sharpe ratio; and
4. maximum drawdown.

- Do not enlarge return while shrinking risk.
- Add turnover, concentration, benchmark difference, and costs in the next
  evidence row when available.
- Each metric has a short definition via visible supporting text or accessible
  help.
- Use consistent percent and decimal precision across peer funds.

### Cards

- Use cards to introduce fund families, summarise one fund, or group one task.
- Each card has one unique title and one clear purpose.
- Use borders and spacing before colour blocks.
- Fund cards show objective, family/method, four balanced metrics, and a details
  action; they do not function as the sole comparison surface.
- Avoid nested cards and grids of individually coloured metric tiles.

### Tables

- Use tables for exact peer comparison, holdings, fees, assumptions, and method
  parameters.
- Include a descriptive caption or immediately preceding heading.
- Left-align text and right-align numbers.
- Align decimal places and units.
- Use a sticky header for long interactive tables where feasible.
- Use subtle row rules and optional alternating Soft surface rows.
- The first column identifies the row and is visually treated as the row header.
- Do not use vertical rules unless they materially improve grouping.
- Missing values display as an em dash in the interface and remain machine-null
  in the underlying CSV.
- Never use a table for general page layout.

### Notices

Use notices contextually:

- Information: Accent soft with Ink text.
- Caution: pale amber surface, Warning border/icon/text heading.
- Error/failed validation: pale adverse surface with Adverse border and a specific
  recovery instruction.

Do not repeat generic disclaimer boxes on every section. Place the risk or
limitation beside the figure, holding, signal, or allocation it qualifies.

### Expanders

Expanders may contain:

- equations;
- detailed optimiser parameters;
- data dictionaries;
- additional holdings; and
- secondary robustness output.

Expanders must not hide the primary risk, fee, sample, benchmark, or historical
status.

## Page-specific hierarchy

### Overview

Order:

1. product proposition;
2. how the systematic process works;
3. equity, crypto, and combined family cards;
4. what makes the evidence inspectable; and
5. route to comparison.

Do not lead with a fictitious balance, best-return fund, or hero photograph.

### Compare funds

Order:

1. selected funds, benchmark, and filters;
2. growth-of-$1 comparison;
3. risk-return plot;
4. aligned comparison table; and
5. definitions and limitations.

- Allow up to four selected funds for focused comparison. Put Selected funds
  and Benchmark first; place family and method filter pills in a secondary,
  clearly labelled filter panel below them.
- Monthly funds appear by default.
- Daily, weekly, and bi-weekly diagnostics remain report evidence and never
  share the default fund-selection menu.
- Do not sort by highest return by default.

### Fund details

Order:

1. fund name, family, method, objective, and status chips;
2. intended use and principal risks;
3. balanced four-metric group;
4. growth of $1 versus benchmark;
5. aligned drawdown;
6. latest simulated target weights and effective date;
7. target allocation through time, immediately before latest weight changes;
8. turnover, concentration, costs, and benchmark difference; and
9. method, limitations, and downloads.

Use `latest simulated target weights` rather than unqualified `current holdings`.
Use equity-sector bands for Equity and Combined funds, one Crypto band within
Combined funds, and individual cryptoasset bands for Crypto-only funds.
Place the complete-weight CSV download on the same row as the complete
target-weight-table heading, aligned to the right above the table.
Place section-specific CSV downloads in the same row as their section heading,
using a content-sized right column whose outer edge aligns with the tables below.
On Fund Details, group the return-history download with a **Historical
performance** heading immediately above the performance metrics and charts.

### Allocation lab

Desktop uses two columns:

- left: selected funds, allocation benchmark, fund-weight controls, total,
  validation, equal example, reset;
- right: combined historical growth/drawdown, aligned benchmark metrics, fees,
  overlap, and underlying exposure.

Keep Equal allocation across selected funds as the default benchmark because it
tests the user's weighting decision. Offer SPY and ONEQ only as external market
context, with exact common dates and a visible asset-mix mismatch caveat.

On small screens, controls appear before results. Every result updates from the
same allocation state. No allocation is labelled recommended.

### News signal

Order:

1. sector/model/window filters;
2. market-wide Stockist News Fear and Greed level plus standardized daily mood;
3. selected sector sentiment score and literal coverage confidence;
4. sector sentiment time series with zero rule;
5. aligned coverage breadth/concentration evidence;
6. plain versus finance-adjusted validation; and
7. base versus coverage-aware fusion result.

The market index must be labelled as headline language, not as the CNN Fear &
Greed Index or a direct measure of investor positioning. The upper panel uses a
selected-window average on a direct 0–100 rescaling of VADER and must disclose
that its displayed axis is zoomed. The lower panel standardizes daily tone over
the fixed 2020–2023 sample and must be described as full-sample, descriptive,
and separate from the lagged coverage-aware backtest signal. Hover evidence must
include headline count and the number of stocks with news because a low
standardized score can coincide with sparse coverage.

Positive sentiment must be able to coexist visibly with thin confidence. Keep
the one-trading-day lag explanation beside the fusion result.

### Methods & data

Order:

1. walk-forward timeline and first live date;
2. fund method cards;
3. default configuration;
4. monthly primary versus frequency experiment;
5. sentiment and confidence equations;
6. output/data dictionary;
7. assumptions and limitations; and
8. downloads and reproducibility instructions.

## Data visualisation system

### Global chart rules

- Every chart answers a named question.
- Use a descriptive title, concise subtitle, axes, units, sample, and source.
- Sort time series chronologically and categories deliberately.
- Use Accent for the selected/focal series.
- Use Secondary ink or a neutral grey dashed line for benchmarks everywhere.
- Use Adverse for drawdown fill plus an explicit text label.
- Add a zero line when it changes interpretation.
- Do not truncate a bar-value axis unless the break is explicit and justified.
- Prefer direct labels. If a legend is necessary, keep its location consistent
  and outside the data region when possible.
- Limit categorical colours to five or six.
- Do not use three-dimensional charts, gauges, speedometers, radial meters,
  decorative donuts, or dual axes without an exceptional analytical reason.
- Tooltips supplement visible information; they never contain the only value,
  date, unit, or interpretation.
- Provide a text takeaway and an exact data table or download.

### Approved chart mapping

| Investor question | Preferred chart | Required detail |
|---|---|---|
| How did the fund compound? | Line | Starts at $1; benchmark dashed; direct labels |
| When and how deeply did it lose? | Drawdown area | Zero at top; same dates as growth chart |
| How do funds compare on risk-adjusted evidence? | Horizontal dot or risk-return scatter | Return and drawdown remain visible nearby |
| What does the fund hold? | Horizontal bars plus table | Top holdings, previous marker, `Other` |
| How did weights change? | Small multiples or heatmap | Stable asset order; avoid 60-colour areas |
| What exposure does an allocation create? | Horizontal bars plus exact table | Equity, crypto, sector, and overlap views |
| How did sector sentiment evolve? | Small multiples or filtered line | Common scale and zero line |
| Is sentiment well supported? | Aligned breadth band/dots | Exact company count and confidence text |
| Did fusion change results? | Two-line growth plus comparison table | Identical sample, base method, and costs |
| Does faster retraining help? | Turnover-versus-Sharpe scatter | Monthly primary visually distinguished |

### Interactive charts

- Use interactivity only when it helps a real task such as selecting a sector,
  comparing a period, or inspecting an exact point.
- Shared filters update all related charts and summary values.
- Preserve consistent series colours and definitions during filter changes.
- Provide reset and download actions.
- Do not hide the main finding until the user interacts.

### Static report exports

- Export Word/A4-ready PNGs at 300 dpi on white Surface.
- Use DejaVu Sans and the same tokens as the app.
- Respect the Word report's usable page width.
- Each figure has a caption/evidence sidecar stating what it shows, why it
  matters, and what it does not establish.
- Exhibit numbering belongs in Word captions, not artifact filenames.

## Fund and method identification

Use a consistent naming hierarchy:

```text
Stockist <Family> <Method>
```

Examples:

- `Stockist Equity Minimum Variance`
- `Stockist Crypto Risk Parity`
- `Stockist Combined Maximum Sharpe`

Display the friendly full name first and the technical method below it where
space is limited. Do not invent marketing names that obscure the family or
method. Equal-weight funds are explicitly labelled benchmark where used as the
comparison baseline.

Recommended method line/marker treatment:

| Method | Default treatment |
|---|---|
| Equal Weight | Secondary ink, dashed or hollow marker when a benchmark |
| Minimum Variance | Accent solid |
| Risk Parity | Blue solid or distinct marker |
| Maximum Sharpe | Orange solid or distinct marker |
| Coverage-aware fusion | Purple-pink solid, only in fusion comparison |

Selected/focal state overrides the normal method colour with Accent, so direct
labels and line styles must preserve identity.

## Evidence-confidence language

### Historical status

Approved phrases:

- `Historical out-of-sample simulation`
- `First live simulated date: <date>`
- `Data through 2023`
- `Latest simulated target weights as of <date>`
- `Past simulated performance is not a forecast`

Avoid:

- `live performance`
- `today`
- `current market signal`
- `expected return` when reporting realised backtest return
- `will outperform`
- `safe`, `secure return`, or `best fund`

### Coverage confidence

The customer-facing app uses the literal zero-to-one confidence score rather
than qualitative evidence-status bands or a separate companies-covered metric.
Headline count and HHI remain available in the exact-observation table for users
who want the supporting detail. Any descriptive thresholds remain report audit
tools rather than customer-facing classifications.

No-news days display `No news` and confidence `0.00`; they are not described as
neutral evidence.

### Costs

Always distinguish:

- gross simulated return;
- after-trading-cost simulated return; and
- illustrative after-product-fee return.

Do not use `net return` without stating exactly which costs are included.

## Responsive rules

### Desktop

- Persistent sidebar and wide evidence panel.
- Two-column analytical layouts where inputs and consequences benefit from
  simultaneous visibility.
- Full comparison tables and paired aligned charts.

### Tablet

- Collapsible sidebar.
- Two-column regions collapse when labels or charts become compressed.
- Filter controls wrap in their logical reading order.

### Mobile

- One-column reading order.
- Metric groups remain a two-column grid; a fifth measure begins a final row.
- Allocation controls appear before consequences and retain a visible total.
- Comparison uses selected-fund summary cards followed by a horizontally scrollable
  exact table; text is not reduced to force fit.
- Chart heights preserve readable direct labels.
- Short segmented controls remain on one line; otherwise use headings or
  expanders.
- No content or action depends on hover.

Test at approximately 320 px, 768 px, and a normal desktop width.

## Accessibility requirements

- Keyboard access and visible focus for every control.
- Logical heading order and reading sequence.
- Descriptive control labels and specific error messages.
- Minimum target sizes suitable for touch.
- Text and non-text contrast meeting WCAG AA targets.
- No colour-only status or series identification.
- Chart takeaway and table/download alternative.
- No essential information available only in tooltips.
- Tables use meaningful headers and captions.
- Decorative images are omitted. Any meaningful image has concise alternative
  text and nearby written context.
- Layout remains usable under browser zoom and larger text settings.

## Streamlit implementation rules

- Prefer native Streamlit components and minimal scoped CSS.
- Do not manipulate fragile auto-generated DOM selectors when a stable component
  or wrapper can achieve the result.
- Keep styling in a small reusable app module or central CSS block rather than
  scattering raw HTML through page logic.
- Separate artifact loading, calculations, formatting, and rendering.
- Cache immutable precomputed artifact reads.
- The app must not run the optimiser, backtest, or VADER at interaction time.
- Validate artifact existence and schema before rendering; show a specific error
  and recovery instruction when an artifact is unavailable.
- Do not require external font, image, or analytics services for the core app.
- Preserve selected navigation and fund state where Streamlit session state makes
  this reliable.

## Quality checklist

Before accepting a page:

- Can the user state the page's purpose within five seconds?
- Are return, risk, benchmark, costs, and sample definitions visible together?
- Is the most important comparison visible without changing tabs?
- Are the selected filters and data dates explicit?
- Does every chart have a text/table alternative?
- Can all actions be completed with the keyboard?
- Does the page remain readable at mobile, tablet, and desktop widths?
- Are monthly funds separated from frequency diagnostics?
- Are latest weights clearly historical and dated?
- Can positive sentiment visibly carry low evidence confidence?
- Is any negative or null result visually suppressed?
- Are there unnecessary colours, cards, legends, icons, or notes?

## Approval and change control

This visual system was approved as the Phase 0 baseline on 13 August 2026. It
retains the Part A identity and adds Part B interaction rules. Fixture-data
prototyping and fresh-user testing may reveal necessary changes; record the
evidence and reason here before changing the implementation globally.
