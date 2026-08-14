# AI prompting log 041 — overview inspectability restructure

## Request

Replace the bottom `What makes the evidence inspectable` section with a clearer
`What you can inspect` structure organised around four user tasks.

## Implementation

- Replaced the three technical evidence notes with four equal visual cards.
- Arranged the cards in one four-card desktop row, two columns at medium widths
  and a single column on narrow screens.
- Used the requested categories and copy:
  - Performance & risk;
  - Portfolio construction;
  - Implementation; and
  - News signal experiment.
- Updated the overview smoke test to verify the new hierarchy, all four cards
  and the coverage-aware sentiment-tilt wording.
- Updated the overview hierarchy in the visual-system documentation.

## Design rationale

The revised headings describe what an investor can examine instead of asking
them to interpret the internal meaning of `inspectable evidence`. The four
categories also provide a clearer mental map of the app's pages and analytical
outputs.
