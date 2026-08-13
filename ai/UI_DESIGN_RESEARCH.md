# Stockist Funds — Investment Website UI Research

**Research date:** 13 August 2026  
**Scope:** Current investment-platform interfaces, fund comparison, fact sheets,
allocation controls, financial data visualisation, responsive layout, and
accessible interaction patterns.

This note studies design patterns and translates them into a proposed interface
for the FINS5545 coursework prototype. It does not copy another provider's
branding or imply regulatory approval.

## Design conclusion

Stockist Funds should use a **calm, light-first, evidence-led interface**. It
should feel closer to a clear institutional research product than a trading app:
strong hierarchy, generous white space, exact tables, restrained charts, and
plain-language explanations beside the relevant decision.

The interface should combine:

- Wealthfront's simple account hierarchy and current-versus-target allocation;
- Betterment's separation of portfolio, holdings, performance, and goal views;
- BlackRock's layered fund overview, benchmark performance, key facts, holdings,
  and literature;
- Vanguard's interactive illustration of fee effects; and
- public design-system guidance on hierarchy, comparison tables, accessible
  charts, progressive disclosure, and responsive behaviour.

It should not copy:

- a daily balance or daily gain as the dominant hero metric;
- marketing-led “get started” urgency;
- dense institutional pages that make users hunt for risk and fees;
- large top-level tab bars that hide content and break on small screens;
- dark trading-terminal aesthetics, flashing prices, neon gradients, or
  gamification; or
- decorative finance photography that adds no decision value.

## Reference-platform review

### Wealthfront — strongest pattern: current versus target allocation

Wealthfront's automated-investing presentation uses a strong visual hierarchy:
portfolio value, performance, a restrained time-series chart, and asset rows
showing current and target allocations. The methodology page also explains
diversified asset classes, risk tolerance, and periodic rebalancing.

**Borrow:**

- a single clear page purpose;
- current-versus-target bars;
- asset rows with percentage and dollar value;
- a visible link from summary to deeper methodology; and
- consistent automation/rebalancing language.

**Do not borrow:**

- placing today's gain above long-horizon risk evidence;
- deposit calls to action; or
- tax features irrelevant to the supplied dataset and coursework scope.

Sources: [Wealthfront automated-investing page](https://www.wealthfront.com/robo-advisor-investing),
[Wealthfront investment methodology](https://research.wealthfront.com/whitepapers/investment-methodology/).

### Betterment — strongest pattern: task-oriented portfolio layers

Betterment separates the user's home summary from account, portfolio strategy,
allocation, holdings, performance, and projection tasks. This reduces the need
to place every metric on one screen.

**Borrow:**

- task-based navigation;
- a distinct portfolio/allocation view;
- clear routes to holdings and performance; and
- settings that apply to the selected portfolio rather than globally.

**Do not borrow:**

- personalised goal projections or recommendations, which are beyond this
  prototype's evidence and could look like advice;
- a total-net-worth dashboard, because Stockist Funds has no investor-account
  data; or
- automation claims that have not been implemented.

Sources: [Betterment product presentation](https://www.betterment.com/),
[Betterment mobile portfolio tasks](https://www.betterment.com/help/mobile-investment-management).

### BlackRock Australia — strongest pattern: layered fund evidence

BlackRock's fund directory standardises name, ticker, multi-period performance,
performance date, inception, and NAV. Individual fund pages separate overview,
performance, key facts, holdings, pricing, and documents, and present fund and
benchmark returns together.

**Borrow:**

- a standardised directory/table for discovery;
- visible “as of” dates;
- fund-versus-benchmark presentation;
- one fund page with summary, performance, facts, holdings, and methodology;
- top holdings plus exposure breakdowns; and
- consistent definitions across funds.

**Do not borrow:**

- a very long page with many institutional fields above the investor's core
  decision;
- duplicated navigation rows; or
- multiple return tables without a clear hierarchy.

Sources: [BlackRock Australia fund directory](https://www.blackrock.com/au/products/investment-funds),
[BlackRock Balanced Fund page](https://www.blackrock.com/au/products/254847/).

### Vanguard Australia — strongest pattern: interactive fee impact

Vanguard's managed-fund fee calculator combines input controls with a projected
balance comparison and explicitly exposes assumptions. Its product browser also
describes ready-made portfolios through risk appetite and investment timeframe.

**Borrow:**

- sliders or numeric inputs beside the resulting fee-impact chart;
- assumptions displayed near the output;
- comparison only between reasonably similar funds; and
- an immediate dollar interpretation of percentage fees.

**Do not borrow:**

- imply that a constant return projection is a forecast;
- compare funds with materially different risk profiles without warning; or
- bury assumptions below the interaction.

Sources: [Vanguard managed-fund fee calculator](https://insights.vanguard.com.au/ManagedFundFee/ui/index.html),
[Vanguard Australia product browser](https://www.vanguard.com.au/personal/invest-with-us/products).

## Information architecture

Use a labelled Streamlit sidebar as the primary navigation. It should collapse
on small screens. Do not use top-level tabs as page navigation: tabs hide content
and make side-by-side comparison harder. GOV.UK specifically advises against
tabs when users need to compare information or read content in sequence.

Recommended primary pages:

1. **Overview** — product, fund families, methodology summary, and historical
   status.
2. **Compare funds** — filters, pinned funds, comparison table, and risk-return
   view.
3. **Fund details** — one complete selected-fund fact sheet.
4. **Allocation lab** — hypothetical allocation and aggregate evidence.
5. **News signal** — sentiment, coverage confidence, and fusion results.
6. **Methods & data** — backtest, assumptions, experiments, downloads, glossary,
   and limitations.

Use small tabs or segmented controls only within a page for closely related
views, such as `Growth | Drawdown` or `Holdings | Exposure`, when the user does
not need both simultaneously.

Source: [GOV.UK tabs guidance](https://design-system.service.gov.uk/components/tabs/).

## Global shell

### Header

- Stockist Funds wordmark in text, not a large decorative logo.
- Page title and one-sentence purpose.
- Persistent evidence strip:
  `Historical OOS simulation · Monthly primary · Data through 2023 · Not advice`.
- Optional “How to read this page” help link.

### Sidebar

- Six text-labelled destinations with simple line icons only if labels remain.
- Selected page uses the teal accent and a visible shape/border, not colour alone.
- Compact “Build status” area only during development; remove from public view.
- Methodology and download links at the bottom.

### Content width and spacing

- Maximum readable content width around 1,180–1,280 px on desktop.
- Twelve-column mental grid, implemented with simple Streamlit columns.
- 24–32 px between major regions and 16 px within related groups.
- Off-white page canvas, white analytical surfaces, a light-grey sidebar,
  subtle one-pixel borders, and almost
  no shadows.
- Avoid more than three columns of content; use one column on mobile.

## Stockist Funds visual language

Continue the Project A system:

| Role | Colour | Interface use |
|---|---:|---|
| Ink | `#0F172A` | Titles, primary values, axes |
| Secondary ink | `#475569` | Supporting copy, dates, notes |
| Page canvas | `#F4F6F5` | Off-white application background |
| Surface | `#FFFFFF` | Charts, tables, metrics, inputs, and content panels |
| Sidebar | `#E9EFF0` | Light neutral navigation rail |
| Soft surface | `#EEF2F3` | Grouped controls and alternating rows |
| Rule | `#D7DEE3` | Dividers, borders, quiet grids |
| Accent | `#0F766E` | Selected state, primary series, buttons |
| Accent soft | `#CCFBF1` | Selected-card and information backgrounds |
| Warning | `#B45309` | Thin evidence, high turnover, caveats |
| Adverse | `#C2410C` | Drawdown and material downside |

Use the accent for the focal series and neutral grey for benchmarks/context.
Reserve categorical colours for genuinely distinct fund methods or sectors.
Atlassian's data-visualisation guidance recommends a single brand colour by
default, limiting categorical palettes, and not relying on colour alone.

Source: [Atlassian data-visualisation colour guidance](https://atlassian.design/foundations/color-new/data-visualization-color/).

### Typography

- Use `Aptos`, `Inter`, or the operating-system sans-serif stack without a
  network-dependent font requirement.
- Sentence-case titles and controls.
- Large numbers use tabular figures where available.
- Page title: approximately 30–34 px desktop, 26–30 px mobile.
- Section title: 20–24 px.
- Body: 15–17 px with comfortable line height.
- Supporting notes: never below a readable 13–14 px.

### Cards

Use cards for summaries, not for large comparison matrices.

- A card must have one purpose and one obvious title.
- Use borders and spacing before shadows.
- Do not place every metric in a separate coloured tile.
- Status chips always include text, such as `Higher drawdown` or
  `Coverage: thin`.
- Comparison cards may introduce funds, but exact peer comparison belongs in a
  table with aligned rows and columns.

## Page designs

### Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Stockist Funds                     Historical OOS · through 2023    │
│ Systematic funds with inspectable risk and signal confidence       │
├───────────────┬─────────────────────────────────────────────────────┤
│ Overview      │ How it works: Data → Rules → Monthly OOS → App     │
│ Compare       │                                                     │
│ Fund details  │ [Equity]       [Crypto]        [Combined]          │
│ Allocation    │ objective      objective       objective           │
│ News signal   │ risk note      risk note       risk note           │
│ Methods       │                                                     │
│               │ What makes this evidence different?                │
│               │ OOS testing · costs · coverage confidence          │
└───────────────┴─────────────────────────────────────────────────────┘
```

Lead with the product's rule and evidence, not a fictitious account balance.
Use three family cards with comparable structure and a single “Compare funds”
action.

### Compare funds

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Compare monthly funds                                               │
│ [Family ▾] [Method ▾] [Cost view ▾] [Reset]                        │
│                                                                     │
│ Selected: [Equity Min Var ×] [Combined Risk Parity ×]              │
│                                                                     │
│ Metric              Equity Min Var       Combined Risk Parity       │
│ Objective           Lower equity risk    Balanced risk contribution │
│ Ann. return         xx.x%                 xx.x%                       │
│ Ann. volatility     xx.x%                 xx.x%                       │
│ Sharpe              x.xx                  x.xx                        │
│ Max drawdown        -xx.x%                -xx.x%                      │
│ Turnover / costs    ...                   ...                         │
│                                                                     │
│ [Risk-return dot plot]       [Growth of $1 with direct labels]      │
└─────────────────────────────────────────────────────────────────────┘
```

- Permit two or three pinned funds, not every fund at once.
- Keep the comparison table visible; do not split peer metrics into tabs.
- Add table caption, metric definitions, and “as of” dates.
- Use sorting only where it helps a stated task. Do not default to highest return.

Tables are the appropriate component for aligned row-and-column comparison, and
captions improve navigation and comprehension.

Source: [GOV.UK table guidance](https://design-system.service.gov.uk/components/table/).

### Fund details

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Combined · Risk Parity                     [Monthly] [OOS]          │
│ Balances risk contribution across equities and crypto              │
│ May suit: ...                 Key risks: crypto, drawdown, model    │
│                                                                     │
│ Return       Volatility       Sharpe       Maximum drawdown         │
│ xx.x%        xx.x%            x.xx         -xx.x%                   │
│                                                                     │
│ [Growth of $1: fund solid, benchmark dashed]                       │
│ [Drawdown: negative filled area directly below on same dates]      │
│                                                                     │
│ Latest simulated target weights · effective YYYY-MM-DD             │
│ [current vs previous horizontal bars]   [asset-family exposure]    │
│                                                                     │
│ Costs and turnover | Method | Risks and limitations | Download     │
└─────────────────────────────────────────────────────────────────────┘
```

- Give return, volatility, Sharpe, and drawdown equal visual weight.
- Keep growth and drawdown vertically aligned on the same time axis.
- Use “latest simulated target weights,” never unqualified “current holdings.”
- Show top holdings plus `Other`; provide the complete table below or by download.
- Add a “Why weights changed” table showing old weight, new weight, and change.
  Do not invent causal commentary that the optimisation does not support.

### Allocation lab

```text
┌───────────────────────────────┬─────────────────────────────────────┐
│ Hypothetical allocation       │ Combined historical evidence        │
│ Equity Min Var       [ 40% ]  │ Growth | Drawdown                   │
│ Crypto Risk Parity   [ 10% ]  │ [linked chart]                      │
│ Combined Min Var     [ 50% ]  │                                     │
│ Total                 100% ✓  │ Return  Vol  Sharpe  Max DD         │
│ [Equal example] [Reset]       │                                     │
│                               │ Fees: x.xx% / $xx per $10,000       │
│ Allocation concentration ...  │ Overlap: ...  Crypto exposure: ... │
└───────────────────────────────┴─────────────────────────────────────┘
```

- Keep controls and consequences visible together on desktop.
- Recalculate all summary panels from one shared allocation state.
- Add an equal-allocation example, but do not label any allocation recommended.
- Show underlying overlap and total crypto exposure prominently.
- On mobile, stack controls above results and keep the total allocation visible.

Linked charts and summaries should update consistently from the same selection;
Carbon's dashboard guidance stresses hierarchy, limited metrics, consistent
colour, and linked exploration views.

Source: [Carbon Design System dashboard guidance](https://carbondesignsystem.com/data-visualization/dashboards/).

### News signal

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Sector news signal                                                  │
│ [Sector ▾] [Score: Finance-VADER ▾] [Window ▾] [Reset]             │
│                                                                     │
│ Sentiment  +0.xx     Coverage  4/5     Confidence  Broad            │
│ [sentiment line with zero rule]                                    │
│ [coverage breadth directly below; aligned dates]                   │
│                                                                     │
│ What supports this score?                                          │
│ headline count · company breadth · concentration · no-news policy  │
│                                                                     │
│ Fund effect: Base vs coverage-aware fusion                         │
│ [growth/drawdown comparison] [before-after metrics table]          │
└─────────────────────────────────────────────────────────────────────┘
```

- Align sentiment and coverage on the same dates so confidence is contextual.
- Use a zero reference line and direct sector labels.
- Represent confidence with text plus shape/border, not traffic-light colour.
- Keep the tradable lag explanation next to the fund-effect view.
- Use small multiples for many sectors rather than ten overlapping lines.

## Chart system

Use charts only when they answer a named investor question. GOV.UK recommends
clarity, accessibility, accuracy, consistency, and a deliberate chart choice;
it also warns that dashboards can overwhelm users and require concise guidance.

Sources: [GOV.UK data-visualisation principles](https://brand.design-system.service.gov.uk/data/),
[GOV.UK dashboard guidance](https://brand.design-system.service.gov.uk/data/dashboards/),
[GOV.UK chart guidance](https://brand.design-system.service.gov.uk/data/charts/).

| Question | Preferred visual | Design rule |
|---|---|---|
| How did funds compound? | Line chart | Start at $1; benchmark dashed; direct labels |
| How painful were losses? | Drawdown area | Zero at top; adverse fill; same time axis |
| Which fund has better risk-adjusted evidence? | Horizontal dot plot | Return must remain available beside Sharpe |
| What does the fund hold now? | Horizontal bars + table | Top holdings, previous-weight marker, `Other` |
| How did weights evolve? | Small multiples or heatmap | Avoid 60-colour stacked areas |
| How does allocation change exposure? | Bars + exact table | Update from the same state as all metrics |
| How did sector sentiment evolve? | Small multiples | Common scale and zero line |
| Is sentiment well supported? | Aligned breadth band/dots | Text confidence and exact company count |
| Did fusion add value? | Two-line growth plus metric table | Same sample, base, costs, and assumptions |
| Does faster retraining help? | Turnover-versus-Sharpe scatter | Label monthly primary; diagnostics distinct |

### Chart constraints

- Maximum five or six categorical colours in one view.
- Accent teal always means selected/focal series, not “positive return.”
- Benchmark is consistently neutral grey and dashed.
- Drawdown uses adverse vermilion plus a text label.
- Positive and negative values cannot depend on red/green alone.
- Prefer direct labels; place legends consistently when unavoidable.
- Use quiet horizontal grid lines and no chart border.
- Keep units and sample in or immediately beside the chart.
- Provide a concise text takeaway and an exact data table/download.
- Do not make essential information hover-only.

Accessible charts must make their information available as text, not only as an
image or interaction.

Source: [GOV.UK accessible images and charts](https://design-system.service.gov.uk/styles/images/).

## Responsive behaviour

### Desktop

- Sidebar plus wide content panel.
- Comparison table and paired charts can use the full width.
- Allocation controls and results may sit side by side.

### Tablet

- Collapsible sidebar.
- Two-column cards become one or two columns depending on content.
- Filters wrap into two rows without changing their logical order.

### Mobile

- One-column reading order.
- Summary metrics use a two-by-two grid.
- Allocation controls appear before results.
- Wide comparison changes to pinned fund summary cards plus a horizontally
  scrollable exact table; do not shrink text to fit.
- Chart height remains sufficient for labels.
- Tabs turn into short segmented controls only when labels fit on one line;
  otherwise use headings and expanders.

## Interaction rules

- One clearly styled primary action per page.
- Every filter group includes a visible reset.
- Preserve selection when moving from compare to fund details.
- Display allocation total and validation continuously.
- Disable “view allocation” only with an adjacent explanation, or allow the
  action and show a specific error.
- Use inline definitions for Sharpe, drawdown, turnover, and confidence.
- Use expanders for technical detail, never for the principal risk or fee.
- Avoid modal dialogs for core evidence.
- Make downloadable tables match the filtered state and display the data date.
- Use positive friction before the final hypothetical allocation summary: the
  user should see costs, concentration, and historical-status language.

## UI acceptance criteria

The interface is ready only when:

- a user can identify the primary monthly funds without seeing daily/weekly
  diagnostics mixed into the fund menu;
- all peer metrics align in a comparison table using identical definitions;
- every fund page shows objective, risks, method, benchmark, costs, turnover,
  holdings date, and historical sample without extra navigation;
- the allocation total, consequences, and underlying overlap are visible;
- a positive sentiment score can visibly coexist with a low-confidence label;
- no chart is the only way to access its key information;
- keyboard navigation and visible focus work for all controls;
- layouts remain readable at 320 px, 768 px, and desktop widths;
- no essential label wraps or truncates silently;
- the most important page content appears before methodology detail;
- no screen implies live performance or holdings after 2023; and
- the fresh-user comprehension protocol in `APP_PRODUCT_RESEARCH.md` passes or
  produces documented corrections.

## Recommended next design artifact

Before implementing the complete app, create one low-fidelity Streamlit shell
using fixture data for these four critical screens:

1. Compare funds.
2. Fund details.
3. Allocation lab.
4. News signal.

Test navigation, hierarchy, mobile stacking, terminology, and comprehension
before adding final charts or visual polish. This prevents analytical code and
UI layout from becoming tightly coupled too early.
