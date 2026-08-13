# Prompt log — Required Sharpe barplot

**Date:** 14 August 2026  
**Scope:** Literal Part B exhibit compliance, grouped Sharpe comparison,
report-figure validation, and evidence-catalogue integration

## Student prompts

After reviewing lines 155–165 of the brief, the student supplied a sample
grouped chart and asked:

> For "Sharpe or return-versus-risk barplot" Should it look something like this?

The student then instructed:

> Okay make it like this please

The student clarified that it should be a report image and did not need to be
added to the Streamlit site.

## Decision

The existing `fund_risk_return.png` scatter remains useful additional evidence,
but a separate grouped bar chart now satisfies the brief's literal barplot
wording. It is a static Word/A4-ready report artifact only; no Streamlit code
or deployed app artifact contract was changed.

## Figure design

`results/figures/fund_sharpe_by_family.png` contains:

- Equity, Crypto and Combined groups on the horizontal axis;
- Equal Weight, Minimum Variance, Risk Parity, Maximum Sharpe and Hierarchical
  Risk Parity bars within each family;
- stable method colours matching the Stockist report figures;
- exact two-decimal net Sharpe labels above each bar;
- a 0% risk-free-rate and after-trading-cost assumptions line; and
- a source note identifying the supplied data and historical-simulation status.

The caption sidecar states the 2021–2023 sample, 10 bp turnover-cost assumption,
0% risk-free rate, 252/365-day annualisation distinction and the limitation that
higher historical Sharpe is not a forecast.

## Validation and correction

The first render failed the automated Word-readability check because the bar
labels were 6.6 pt. They were increased to 7.2 pt before acceptance. The final
figure passes context, label, layout, tick, readability and non-blank-image
checks and was manually inspected at original resolution.

The exhibit catalogue now contains nine validated figures, and the Phase 6
contract reports `all_9_exhibits_have_context_and_pass`. The catalogue and
validation summaries were refreshed from existing analytical artifacts only;
portfolio backtests and VADER were not rerun.
