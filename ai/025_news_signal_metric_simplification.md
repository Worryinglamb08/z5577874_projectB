# Prompt log — News Signal metric simplification

**Date:** 14 August 2026  
**Scope:** Customer-facing sentiment metrics, observation tables, regression
testing, and preservation of the analytical model

## Student prompt

After reviewing the purpose of Companies covered, Evidence Status and the
coverage chart, the student instructed:

> In that case I would like to remove Companies Covered and Evidence Status, it
> creates confusion to the user instead of clarity

## Decision and change

The two concepts were removed from every visible News Signal occurrence:

- the top metric cards no longer show Companies covered or Evidence status;
- the recent exact-observations table omits both columns; and
- the positive-but-thin examples table omits Companies covered.

The page now leads with only the latest supported sentiment score and literal
Coverage Confidence. Coverage Confidence remains because it is the actual
zero-to-one quantity used to scale the fusion signal. Headline count and HHI
remain as optional exact-observation detail.

## Analytical boundary

This is a customer-interface simplification only. The precomputed sector data
still retain constituent coverage fields for reproducibility and report audit.
No sentiment score, confidence value, VADER result, signal lag, fund weight or
fusion return was recomputed or changed.

## Validation

- A Streamlit regression test verifies that Coverage Confidence remains while
  the removed concepts appear in neither metric cards nor displayed tables.
- The focused app, logic and chart suite passes 36 tests.
- Ruff passes for the changed Python files.
