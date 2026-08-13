# Prompt log — Risk-return family markers

**Date:** 13 August 2026  
**Scope:** Compare-funds risk-return chart encoding and focused regression test

## Student prompt

The student observed that Equity used a different marker while Crypto and
Combined both appeared as circles and asked:

> Can each individual one have different shapes

## Diagnosis

The chart previously used marker shape for selection state: selected funds
were diamonds and unselected funds were circles. Because the selected funds in
the supplied view were Equity funds, this accidentally looked like an
asset-family distinction while leaving Crypto and Combined visually identical.

## Change made

Marker shape now consistently identifies the asset family:

- Equity: diamond;
- Crypto: circle; and
- Combined: square.

Selection no longer changes the marker shape. Selected funds remain visible
through a larger marker, Stockist teal fill and a dark outline. A compact
three-item **Asset family** legend explains the shapes, while hover text still
identifies the exact family, method, return, volatility and Sharpe ratio.

This creates a stable two-channel encoding: shape identifies asset family and
colour identifies method for unselected funds. It also remains interpretable
when colours are difficult to distinguish.

## Validation

- Added a focused chart test covering all three marker mappings, uniqueness,
  selected-point styling and legend entries.
- App, app-logic and chart tests: 22 passed.
- Ruff passed for the changed chart and test files.
- A live check against the 15-fund committed artifacts confirmed one unique
  symbol and one legend entry for each asset family.
- `git diff --check` passed.
