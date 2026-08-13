# Phase 9 — Word report Version 1

## Goal

Create the first complete Project B report as a Word document only. The draft
must lead with the results, reconcile to generated artifacts, include and
interpret every required exhibit, and avoid formulaic AI prose.

## Student prompt

> Do phase 9, only make a word report, start with V1 of it, avoid typical AI
> patterns when writing

## What the assistant produced

- Created `report/report.docx` as a 3.4 MB editable Word source labelled
  **Version 1** and **AI-assisted first draft for student revision**.
- Carried the Part A visual language into Word: Aptos typography, dark ink,
  restrained teal headings, pale evidence notes, A4 portrait narrative pages,
  and a landscape evidence appendix.
- Wrote 3,621 narrative words, below the brief's approximate 5,000-word limit.
- Embedded all nine validated report figures at their 300 dpi source quality.
- Added four evidence tables covering model design, all 15 fund results, fusion,
  and the frozen frequency experiment.
- Added Word `SEQ` fields, bookmarks, and `REF` fields for table and figure
  numbering and cross-references; fields are set to update when Word opens.
- Added alt text to every embedded figure and repeating table headers.
- Added four verified references: ASIC Moneysmart, Markowitz (1952), Hutto and
  Gilbert (2014), and López de Prado (2016).
- Kept one explicit human-review flag for the finance-lexicon validation cases.
- Did not create a PDF, following the student's instruction.

## Writing decisions

- The abstract starts with the result rather than market motivation.
- The report does not describe one method as the universal winner. It states
  that Combined Risk Parity leads combined Sharpe, Equal Weight leads combined
  return, and Minimum Variance has the shallowest combined drawdown.
- Crypto Minimum Variance's 69.5% annualised return is placed beside 76.9%
  volatility and a 72.9% drawdown.
- The finance-sentiment extension is reported as a negative result: the primary
  coverage-aware tilt reduces Sharpe from 0.504 to 0.453 while making drawdown
  0.77 percentage points shallower.
- The Utilities and Technology 2022 event audits distinguish credible direction
  from uncertain magnitude and do not claim causality.
- Three recommendations are specific: narrow the customer-facing combined-fund
  comparison, keep sentiment outside the fund menu pending review and holdout
  evidence, and run a longer shadow product with executable costs and user tests.

## Checks performed

- Repository Word report workflow: pass.
- Outline check: all intended headings use Word Heading 1 or Heading 2 styles.
- Proofread helper: zero doubled words, spacing findings, unresolved ordinary
  placeholders, or broken reference findings.
- Hard-banned AI phrase scan: zero matches.
- Document structure: two sections, nine embedded images, four evidence tables
  plus styled note components, Word captions, cross-references, footer page
  fields, hyperlinks, and document metadata.
- Every quantitative claim was drawn from the current validated CSV artifacts.
- No `report.pdf` was produced.

## Risks and student review still required

- The finance-lexicon family scores were averaged from ten blinded AI reviews.
  The student must complete the logged validation-headline review before removing
  the human-review flag.
- The draft is not yet the student's final voice. The student must rewrite any
  sentence that does not match their understanding and confirm the economic
  explanations.
- No local Word-compatible renderer was available for a page-image inspection.
  Open the DOCX in Microsoft Word, update all fields, inspect every page, run
  Accessibility Checker, and check the narrative page count.
- PDF export remains deferred until the Word draft is approved.
