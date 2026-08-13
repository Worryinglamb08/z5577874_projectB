# Stockist Funds — Investment App Product Research

**Research date:** 12 August 2026  
**Purpose:** Translate current investor-protection, fund-disclosure,
accessibility, and automated-investing practices into a concrete product brief
for the FINS5545 Stockist Funds prototype.

This is product-design research, not legal advice and not a claim that the
coursework prototype is a regulated financial product.

## Executive finding

A good systematic-fund app helps a non-technical investor make a deliberate,
comparable, and risk-aware decision. It should answer six questions in order:

1. Is this type of fund appropriate for my objective, time horizon, liquidity
   needs, and tolerance for loss?
2. What assets does the fund hold and what repeatable rule manages them?
3. What return did the rule produce out of sample, and what risk did it take?
4. What benchmark, fees, turnover, concentration, and model limitations qualify
   that result?
5. How would several funds behave together rather than in isolation?
6. What information is current, historical, simulated, uncertain, or missing?

The strongest Stockist Funds concept is therefore not “more charts.” It is a
**decision-confidence layer** combining fund evidence, implementation frictions,
and news-signal coverage quality.

## What the external evidence implies

### 1. Start with suitability, not the highest return

ASIC's Moneysmart explains that managed funds can simplify diversification but
are not risk-free. It asks investors to consider time horizon, risk tolerance,
liquidity needs, ongoing fees, and comfort with losses. It also identifies
market, sector, liquidity, currency, inflation, interest-rate, credit,
concentration, and gearing risks where relevant.

For Stockist Funds, every fund card and fact sheet should therefore state:

- objective and asset family;
- who it may and may not suit;
- suggested decision horizon as a product description, not personal advice;
- risk level with the reason for it;
- liquidity/calendar characteristics; and
- the most relevant fund-specific risks.

Source: [ASIC Moneysmart, “What is a managed fund”](https://moneysmart.gov.au/managed-funds-and-etfs/what-is-a-managed-fund).

### 2. Comparison must be standardised and balanced

ASIC says fund promotion should balance returns, features, benefits, and
significant risks; use appropriate benchmarks; explain that past performance is
not indicative of future performance; and avoid confusing graphs or tables.
The SEC similarly advises investors to consider volatility, turnover, strategy,
risk, and the path of returns rather than a headline average alone.

The compare screen should use the same definitions, live sample, calendar, fee
assumption, and benchmark convention for all peer funds. It should show return
and risk side by side, never rank funds using return alone, and identify when
funds are not directly comparable because their calendars or asset families
differ.

Sources: [ASIC on managed-fund performance and risk marketing](https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2022-releases/22-061mr-asic-scrutinises-marketing-of-managed-fund-performance-and-risks),
[SEC, “Look at More Than a Fund's Past Performance”](https://www.sec.gov/about/reports-publications/investorpubsmfperformhtm).

### 3. A short fact sheet should stand on its own

Current disclosure thinking favours concise, investor-friendly summaries. The
FCA's product-summary framework says a short summary should give sufficient
understanding of a product's nature, objectives, risks, and costs. The SEC's
tailored-report framework emphasises concise presentation, expenses, holdings,
turnover, performance, and benchmark context. A current BlackRock Australia
product page illustrates common fund-page layers: target investor, objective,
performance, key facts, holdings, and supporting documents.

Each Stockist Funds fact sheet should contain:

- one-sentence objective;
- “how it works” in plain English plus an expandable technical methodology;
- asset family, optimisation method, estimation window, monthly rebalance rule,
  constraints, and first live out-of-sample date;
- growth of $1 against an appropriate transparent benchmark;
- annualised return, volatility, Sharpe ratio, and maximum drawdown;
- drawdown history and worst observed period, not only the average result;
- latest target holdings, effective date, concentration, and asset/sector split;
- turnover and cost-adjusted result;
- fee illustration in both percent and dollars;
- principal risks and model limitations;
- historical-simulation and sample-end labels; and
- downloadable data/methodology links.

Sources: [FCA product-summary requirements](https://handbook.fca.org.uk/handbook/disc3),
[SEC tailored shareholder-report guide](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/tailored-shareholder-reports-mutual-funds-exchange-traded-funds-fee-information-investment-company),
[BlackRock Australia fund-page example](https://www.blackrock.com/au/products/280914/).

### 4. Costs should be visible before allocation

The FCA found that consumers should be able to identify and compare investment
charges, while activity-based charges can be difficult to find. Its guidance
calls for total costs in both cash and percentage terms, a breakdown, and an
illustration of the effect on returns. The SEC also requires fee presentations
not to omit qualifications that make them misleading.

Stockist Funds should show:

- management fee and any performance-fee rule separately;
- assumed trading cost from rebalancing separately;
- gross return, net-of-trading-cost return, and illustrative net-of-product-fee
  return without mixing the definitions;
- annual fee dollars for the user's hypothetical allocation; and
- a multi-year fee-drag illustration, clearly labelled as an illustration.

Sources: [FCA investment-platform cost review](https://www.fca.org.uk/firms/investment-platforms-consumers-investment-costs-good-poor-practice),
[SEC fee and expense presentation](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/tailored-shareholder-reports-mutual-funds-exchange-traded-funds-fee-information-investment-company).

### 5. The allocation builder must reveal portfolio-level risk

Moneysmart notes that diversification can reduce reliance on one investment or
manager, but portfolio weights drift and require rebalancing to restore the
intended risk mix. Automated-investing platforms commonly connect risk tolerance,
diversified allocations, and periodic rebalancing rather than treating fund
selection as isolated picks.

The Stockist Funds allocation builder should:

- require allocations to total 100% and provide a visible reset;
- use a neutral starting example rather than a “best fund” default;
- show aggregate historical growth, annualised volatility, Sharpe, and maximum
  drawdown for the chosen mix;
- show fund correlations and underlying asset overlap so several labels are not
  mistaken for genuine diversification;
- show combined exposure to equities, crypto, sectors, and individual assets;
- show estimated annual fees in dollars and percent;
- compare the chosen mix with an equal-allocation reference by default, with
  optional SPY and ONEQ market context on exact common dates;
- label the output as a hypothetical historical simulation, not personal advice
  or a forecast.

Sources: [ASIC Moneysmart on diversification and rebalancing](https://moneysmart.gov.au/how-to-invest/diversification),
[Wealthfront investment-methodology example](https://research.wealthfront.com/whitepapers/investment-methodology/).

### 6. Systematic management must be inspectable

“Systematic” should mean a repeatable process the user can understand and audit,
not a black-box marketing label. The app should expose:

- eligible universe and asset family;
- objective function and constraints;
- estimation window and information cutoff;
- monthly rebalance timing;
- current target weights and the previous weights;
- turnover and largest weight changes;
- benchmark and transaction-cost assumptions;
- sensitivity to rebalance frequency; and
- known model risks such as unstable estimated means, covariance sensitivity,
  concentration, regime dependence, and the short 2021–2023 live sample.

A useful “Why did this fund change?” panel can show the largest weight changes at
the latest rebalance and distinguish model inputs from narrative explanations.
It must not invent causal stories that the optimisation does not establish.

### 7. Sentiment needs an evidence-quality label

The sentiment page should not present a positive sector score as a buy signal.
For each sector and date, show:

- finance-adjusted sentiment and its recent history;
- number of covered companies out of five;
- headline count and concentration;
- a plain-language confidence label derived from disclosed coverage rules;
- the one-trading-day signal lag;
- comparison with plain VADER where useful; and
- the measured before-versus-after effect of the fund tilt.

This is where Stockist Funds can be distinctive: “positive but thin” is
different from “positive and broadly supported.” The raw score, coverage
confidence, adjusted score, and tradable lagged score should remain separately
auditable.

### 8. Use contextual risk information, not disclaimer wallpaper

The FCA says communications should be clear, fair, balanced, and designed around
what a consumer needs at that stage. It notes that generic warnings can be
ineffective and supports contextual explanations of benefits and risks.

Stockist Funds should place risk next to the relevant decision:

- crypto calendar and drawdown risk beside crypto funds;
- concentration beside current holdings;
- turnover and costs beside the frequency experiment;
- no-look-ahead and historical-simulation labels beside performance;
- thin-news warnings beside sentiment; and
- aggregate risk beside the allocation control.

Source: [FCA risk-warning guidance](https://www.fca.org.uk/firms/risk-warnings-mainstream-investments).

### 9. Avoid gamification and rushed decisions

An FCA experiment involving more than 9,000 consumers found that certain digital
engagement practices, including push notifications and prize-based features,
increased trading and risky-investment activity. Its broader digital-design
review recommends clear layouts and language, appropriate friction, testing,
and avoiding biased defaults that drive customers toward a choice.

For this app:

- do not use confetti, streaks, leaderboards, countdowns, “hot fund” badges,
  flashing prices, fear-of-missing-out copy, or return-only rankings;
- do not preselect the riskiest or best-performing fund;
- require users to see the material risk/cost summary before finalising a model
  allocation; and
- test whether users can correctly identify the riskiest fund, worst drawdown,
  fee effect, and historical nature of the results.

Sources: [FCA trading-app experiment](https://www.fca.org.uk/news/press-releases/fca-keeps-trading-apps-under-review-over-gaming-concerns),
[FCA digital-journey design review](https://www.fca.org.uk/publications/good-and-poor-practice/digital-design-customers-online-journeys).

### 10. Accessibility is part of decision quality

WCAG 2.2 requires text alternatives for non-text content and keyboard-operable
functionality, among many other perceivability and operability requirements.
Stockist Funds should therefore provide:

- sufficient text and control contrast;
- no red-versus-green-only meaning;
- keyboard-accessible controls and visible focus;
- descriptive chart titles, captions, and adjacent text summaries;
- readable tables as alternatives to charts;
- clear control labels and error messages;
- responsive layouts and usable target sizes; and
- no information available only on hover.

Source: [W3C Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/).

## Recommended Stockist Funds information architecture

### 1. Discover

- Product proposition and target user.
- Three asset-family explanations: equity, crypto, combined.
- Historical-simulation status, 2020–2023 data period, and first live date.
- “How systematic management works” in four short steps.
- Clear route to compare funds, with no return leaderboard.

### 2. Compare funds

- Consistent cards plus a compact comparison table.
- Filters for asset family and method.
- Columns: objective, annualised return, volatility, Sharpe, maximum drawdown,
  turnover, concentration, benchmark difference, and fee illustration.
- Select two or three funds for a side-by-side comparison.
- Default to monthly primary funds; keep high-frequency experiments separate.

### 3. Fund fact sheet

- Suitability and objective.
- Plain-English rule plus technical details.
- Growth of $1 against benchmark.
- Drawdown and risk metrics.
- Latest target holdings, allocation date, asset/sector exposure, concentration,
  and recent weight changes.
- Turnover, trading-cost effect, and fee illustration.
- Limitations, method version, data cutoff, and data download.

### 4. Build an allocation

- Fund-allocation controls summing to 100%.
- Portfolio-level growth, risk, drawdown, and fee estimate.
- Correlation, overlap, and aggregate exposure diagnostics.
- Plain-language “what changed?” summary relative to equal allocation.
- Reset and download actions.

### 5. News signal

- Sector sentiment through time.
- Coverage-confidence panel.
- Plain versus finance-adjusted VADER diagnostics.
- Signal-lag explanation.
- Base versus sentiment-fusion result, including negative outcomes.

### 6. Methods and evidence

- Model cards for optimisation methods.
- Walk-forward timeline and no-look-ahead explanation.
- Monthly primary versus frequency sensitivity experiment.
- Artifact/data dictionary and reproducibility note.
- Assumptions, limitations, citations, and glossary.

## Feature priority

### Must build for a strong submission

- Monthly fund comparison.
- Complete fact sheet per user-facing fund.
- Allocation builder with portfolio-level risk.
- Sector sentiment with coverage confidence.
- Contextual risk and sample labels.
- Cost/turnover visibility.
- Accessible charts plus table alternatives.
- Fast loading from precomputed artifacts.

### High-value distinction features

- Evidence-confidence ribbon on every fund/signal view.
- “Why did weights change?” rebalance explanation.
- Fund overlap and false-diversification warning.
- Gross versus net performance toggle with a dollar fee illustration.
- Frequency-versus-turnover trade-off explorer.
- Downloadable filtered evidence and methodology/version details.
- Short comprehension test or research usability protocol demonstrating that
  users understand risk, costs, and historical status.

### Avoid

- Return-only leaderboards or “best fund” labels.
- Same-day sentiment trading.
- Mixing monthly investable funds with daily/weekly diagnostics.
- Unlabelled in-sample or full-sample results.
- Implied live/current data beyond 2023.
- Generic warnings detached from decisions.
- Risk labels without the underlying evidence.
- Hidden fees or gross/net ambiguity.
- Gamified urgency, celebratory trading feedback, or biased defaults.
- Heavy backtest or NLTK computation inside the deployed app.

## Proposed product-design test

Before finalising the app, give a fresh user five tasks without coaching:

1. Identify which fund had the largest maximum drawdown and explain what that
   means in dollars on a hypothetical investment.
2. Compare an optimised fund with its benchmark after costs.
3. Find the most recent holdings and state their effective date.
4. Create an allocation and identify its main concentration or overlap risk.
5. Find a sector-day with positive sentiment but low coverage confidence and
   explain why it should not automatically be treated as a buy signal.

Record completion, errors, questions, and whether the user notices that results
are historical out-of-sample simulations ending in 2023. This provides stronger
evidence of app quality than aesthetic polish alone.
