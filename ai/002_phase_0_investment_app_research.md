# Prompt log — Investment app product research

**Date:** 12 August 2026  
**Scope:** Research-backed product and UX requirements for Stockist Funds

## What I wanted

Identify what makes an effective investment app offering several systematically
managed funds, then translate the findings into concrete requirements for the
Stockist Funds comparison, fact-sheet, allocation, sentiment, and methodology
journeys.

## Prompt(s)

> Research what makes a good invest app that offers a user several
> 'systematically managed' funds

## What the assistant produced

- Researched current official guidance and examples from ASIC Moneysmart, ASIC,
  the US SEC, the UK FCA, W3C, BlackRock Australia, and Wealthfront.
- Created `ai/APP_PRODUCT_RESEARCH.md` with research findings, direct source
  links, a six-part information architecture, feature priorities, anti-patterns,
  and a proposed user-comprehension test.
- Recommended a decision-confidence positioning: risk, benchmark, holdings,
  concentration, turnover, costs, model rules, and evidence quality should be as
  visible as return.
- Proposed extending Project A's coverage-confidence work into a user-facing
  distinction between sentiment that is broadly supported and sentiment based
  on thin or concentrated news coverage.

## What was wrong or risky

- Regulatory materials describe real financial-product obligations, while
  Stockist Funds is a coursework prototype. The research note treats these as
  design benchmarks and explicitly does not claim legal compliance.
- Commercial product pages illustrate useful information architecture but are
  also marketing materials. Recommendations were therefore anchored primarily
  in regulator and standards sources rather than copied from one provider.
- Risk questionnaires and recommended allocations can cross from education into
  personalised financial advice. The proposed app uses hypothetical allocation
  controls and suitability descriptions, not personal recommendations.
- “Current holdings” could imply live data. The app must state that holdings are
  the latest simulated target weights within a dataset ending in 2023.
- An impressive dashboard could still be misleading if it ranks funds by return,
  hides costs, or separates warnings from decisions. The research therefore
  prioritises balanced, contextual evidence over visual density.
- User testing is proposed but has not yet occurred. No claim should be made that
  the final app is understandable until the tasks are actually run and recorded.

## Checks performed

- Used current official or first-party sources wherever possible.
- Compared Australian investor guidance with international fund-disclosure,
  digital-design, and accessibility principles.
- Checked that proposed fact-sheet fields include every metric required by the
  assignment brief.
- Checked that the architecture supports the required compare, fact-sheet,
  allocation, and sentiment journey.
- Confirmed the recommendation keeps monthly funds separate from daily, weekly,
  and bi-weekly sensitivity experiments.
- Confirmed the deployed app can implement the proposal using precomputed
  artifacts and does not require runtime VADER or backtesting.
- Avoided inserting unverified statistics or claiming that a regulator endorsed
  Stockist Funds.

## What I changed and why

The assistant translated external evidence into a project-specific product
brief rather than producing a generic list of finance-app features. It centred
the app on informed comparison and decision confidence because this directly
supports the brief, the investor journey, the Project A innovation, and the
Part B marking criteria.

## Student review still required

- Decide whether the app should use six navigation pages or consolidate them
  into fewer tabs for Streamlit.
- Approve the proposed suitability language, fee illustration, and positive
  friction before allocation.
- Decide which distinction features are feasible after the core analytical
  artifacts exist.
- Conduct and document the proposed comprehension test with a fresh user before
  making usability claims.

