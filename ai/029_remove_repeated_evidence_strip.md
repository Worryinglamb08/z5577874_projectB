# AI prompting log 040 — remove repeated evidence strip

## Request

Remove the repeated page-level message:

> Historical out-of-sample simulation · Monthly primary specification · Data
> through 2023 · Educational prototype, not financial advice

The information is already established and the persistent strip consumes
valuable page space.

## Implementation

- Removed the shared evidence-strip renderer from every application page.
- Removed the now-unused evidence-strip CSS.
- Retained the concise page title and purpose sentence.
- Retained contextual methodology, historical-performance and educational-use
  language where it directly explains a chart, table or footer.
- Updated the visual system and the every-page smoke test so the strip is not
  accidentally restored.

## Design rationale

Repeated known information weakens the visual hierarchy and delays access to
the page-specific controls and evidence. Disclosures remain available in
context without occupying the same prominent location on every view.
