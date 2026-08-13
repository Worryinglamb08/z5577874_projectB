# Prompt log — Phase 0 visual system and default configuration

**Date:** 13 August 2026  
**Scope:** Final Phase 0 configuration approval and Part B visual system

## What I wanted

Close Phase 0 by confirming the default modelling configuration and adapting the
approved Project A Stockist Funds visual system for the Part B Streamlit app,
interactive evidence, report figures, tables, and fact sheets.

## Prompt(s)

The student first confirmed that model settings should remain adjustable:

> Okay that should be good. What is left for phase 0?

After the assistant listed the remaining configuration and design decisions, the
student instructed:

> Confirmed Default config. Create the VISUAL_SYSTEM.md, use the visual design we
> had in part A

## What the assistant produced

- Created `ai/VISUAL_SYSTEM.md` as the authoritative Part B visual baseline.
- Preserved the Part A dark-ink, white/soft-neutral, teal-accent system and its
  accessible categorical sequence.
- Added Part B rules for navigation, headers, evidence strips, cards, buttons,
  inputs, status chips, tables, notices, expanders, responsive layouts, app
  terminology, and Streamlit implementation.
- Defined page hierarchy for Overview, Compare funds, Fund details, Allocation
  lab, News signal, and Methods & data.
- Defined a chart-selection system covering growth, drawdown, risk-return,
  holdings, weights, allocation exposure, sentiment, confidence, fusion, and
  rebalance-frequency experiments.
- Recorded the approved 12-fund menu and default model configuration in
  `AGENTS.md` and `ai/PROJECT_PHASES.md`.
- Marked both remaining Phase 0 tasks and its completion gate complete.

## What was wrong or risky

- Directly copying the Project A document would omit interactive state,
  responsive behaviour, fund comparison, allocation controls, and accessibility
  requirements. The assistant retained its identity but expanded its scope.
- A polished “fintech” interface could make a historical prototype look live or
  predictive. The system requires persistent out-of-sample, data-through-2023,
  and no-advice language and uses `latest simulated target weights` instead of
  unqualified `current holdings`.
- Using card grids for all metrics would make exact fund comparison difficult.
  Cards are limited to summaries; aligned comparison uses tables.
- Qualitative sentiment-confidence labels could appear empirically calibrated
  before thresholds have been validated. The system prefers literal confidence,
  company breadth, and HHI until any text-band thresholds are fixed in advance.
- Configurable caps can weaken reproducibility if values are changed without an
  audit trail. The primary defaults anchor required outputs; alternatives are
  separately labelled sensitivity runs.
- The visual specification remains a hypothesis until the fixture shell and
  fresh-user comprehension tests are completed.

## Checks performed

- Read the full Project A visual system and retained its exact core palette,
  typography continuity, accessibility principles, and report-export rules.
- Reconciled the new system with `ai/UI_DESIGN_RESEARCH.md` and
  `ai/APP_PRODUCT_RESEARCH.md`.
- Confirmed the required app journey remains compare, fact sheet, allocation,
  and sentiment, with methods/evidence accessible.
- Confirmed daily, weekly, and bi-weekly diagnostics remain visually separated
  from monthly user-facing funds.
- Confirmed return, volatility, Sharpe, and maximum drawdown receive equal
  summary prominence.
- Confirmed charts require table/download alternatives and do not make essential
  information hover-only.
- Confirmed the default settings are documented as central configuration values,
  not hard-coded implementation constants.
- Kept the supplied brief, context, data-access helper, and protected prompt-log
  template unchanged.

## What I changed and why

The student approved the proposed default configuration and specifically asked
to retain the Part A design. The assistant made that continuity operational:
the same visual identity now governs interactive decisions, model evidence, and
static report outputs, while the default model assumptions are explicit enough
to reproduce and audit.

## Student review still required

- Review the low-fidelity fixture shell when Phase 7 prototyping begins.
- Approve any future change to default caps, costs, methods, confidence formula,
  or visual tokens before it replaces the primary specification.
- Test the finished interface at mobile, tablet, and desktop widths and complete
  the fresh-user comprehension protocol before making usability claims.

