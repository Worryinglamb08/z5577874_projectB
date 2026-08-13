# Prompt log — Phase 4 finance-lexicon expansion research

**Date:** 13 August 2026  
**Scope:** External lexicon comparison, project-corpus intersection, and candidate
governance before any production score changes

## What I wanted

Find finance-related words beyond the existing compact lexicon, using FinVADER
as a starting point, while determining whether the words are actually suitable
for this project's short equity-news headlines.

## Prompt(s)

The student asked:

> Can you research words that are related to finance and see if they are worth
> adding? For example this one already has a list of words related to finance
> https://github.com/PetrKorab/FinVADER What other words can you find?

## What the assistant produced

- Inspected FinVADER's source and bundled Henry and SentiBigNomics dictionaries.
- Inspected the original SentiBigNomics repository and its intended aspect-based
  processing rather than treating its dictionary as a standalone VADER list.
- Downloaded the official 1993--2025 Loughran-McDonald Master Dictionary to a
  temporary research location and interpreted its category fields correctly as
  category-entry years, not sentiment magnitudes.
- Intersected external candidates with all 146,836 clean supplied headlines and
  removed terms already handled by plain VADER or the current 31-token extension.
- Counted matching headlines and plain-VADER-neutral cases, inspected actual
  supplied contexts, and divided candidates into `test_now`, phrase/context rule,
  manual-review, do-not-add, and separate-risk-index groups.
- Saved the detailed research memo and a machine-readable 29-family candidate
  table. No candidate score or Phase 4 index was changed.

## What was wrong or risky

- A large finance lexicon is not automatically a better VADER extension.
  SentiBigNomics is designed for aspect extraction and extra semantic rules;
  FinVADER also rescales its values by 0.1. Copying values directly would silently
  create a different, poorly calibrated model.
- External dictionaries contain unsafe unconditional tokens. Examples include
  generic Henry words (`up`, `more`, `high`, `record`) and SentiBigNomics concepts
  (`cash`, `income`, `revenue`, `guidance`).
- Movement verbs are subject-dependent. `Revenue surged` and `costs surged` must
  not receive the same economic interpretation merely because both contain
  `surged`.
- Loughran-McDonald is filing-oriented, Henry is earnings-release-oriented, and
  SentiBigNomics is aspect-oriented. None is automatically calibrated to this
  short headline corpus.
- Researching candidate terms after seeing portfolio results could invite
  retrospective tuning. Candidate selection uses only lexicon provenance,
  corpus occurrence, plain-VADER coverage, and text context—not Phase 5 returns.

## Checks performed

- Compared plain NLTK VADER, the current production extension, Henry,
  SentiBigNomics, and Loughran-McDonald membership.
- Verified every reported count against the clean headline corpus.
- Inspected representative supplied headlines for all shortlisted and contextual
  families.
- Kept uncertainty terms separate from directional sentiment.
- Preserved the current production lexicon and regenerated no performance result.

## Student review still required

- Approve which `test_now` families enter a new blind scoring round.
- Decide whether subject-aware movement rules are worth their added complexity.
- Review the candidate table for missed contexts or words that should be removed.
- Do not select words based on whether the later fusion backtest improves.
