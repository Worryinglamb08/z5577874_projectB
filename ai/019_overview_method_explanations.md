# Prompt log — Overview portfolio-method explanations

**Date:** 13 August 2026  
**Scope:** Overview information architecture, client-facing method copy, and
Streamlit regression coverage

## Student prompt

The student requested:

> On the overview page I would like to add a section that explains each type of portfolio method briefly. This section should be after Choose an Asset Family section

## Change made

Added **Choose a portfolio method** immediately after **Choose an asset family
before choosing a method** and before **What makes the evidence inspectable**.

The section explains all five approved monthly methods in plain language:

- Equal Weight;
- Minimum Variance;
- Risk Parity;
- Maximum Sharpe; and
- Hierarchical Risk Parity.

Each card briefly states how the method sets weights and its main interpretation
or limitation. The copy preserves the approved positioning: Equal Weight is the
transparent benchmark, Maximum Sharpe is estimation-sensitive, and HRP is a
lower-risk alternative rather than a promise of higher returns.

The cards use a three-card first row and two-card second row so the descriptions
remain readable instead of being compressed into five narrow columns. Shared
method summaries live beside the existing labels and objectives in
`src/app_logic.py` rather than being duplicated inside the view.

## Layout refinement

The student then supplied a screenshot and asked to arrange the cards properly.
The first implementation used two independent Streamlit column rows, which left
the shorter third card visibly misaligned and placed the second row edge to
edge. It was replaced with one responsive CSS grid:

- desktop: three equal-height cards followed by two equal-height centred cards;
- tablet: two columns with the fifth card centred; and
- mobile: one full-width column.

One grid container now controls all five cards, so content length cannot create
the staggered borders shown in the screenshot.

The student then requested the same treatment for the three asset-family cards.
Those cards now share a responsive grid row so their outer borders have equal
height. Each card is also a vertical flex container with its chip group pinned
to the bottom, aligning the method-count and fact-sheet badges despite the
different description lengths. On tablet the third card is centred beneath the
first two; on mobile all three become full-width cards.

Finally, the student requested equal sizing for the four **How Stockist Funds
works** cards. The four separate Streamlit containers were replaced with one
four-column grid whose cards share equal height, padding, title spacing and body
alignment. It becomes a two-by-two grid on tablet and a single column on mobile.

## Validation

- Added a Streamlit test proving that the new section follows the asset-family
  section and precedes the evidence section.
- The test confirms that all five approved method cards render.
- The test also confirms that one grid contains exactly five method cards.
- The test confirms that one family grid contains exactly three cards and that
  all three include a separately bottom-aligned chip group.
- The test confirms that one process grid contains exactly four step cards.
- App, app-logic and chart tests: 23 passed.
- Ruff passed for all changed Python files.
- No portfolio backtests, VADER processing, or generated analytical artifacts
  were rerun because this is an app-copy and layout change only.
