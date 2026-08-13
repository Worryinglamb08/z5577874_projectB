# Prompt log — Phase 4 expansion blind panel

**Date:** 13 August 2026  
**Scope:** Ten-agent blind scoring of 19 researched finance families, exact
averaging, expanded VADER scoring, validation cases, and artifact regeneration

## What I wanted

Apply the same independent score-blind process used for the initial compact
finance lexicon to the 19 research-screened candidate families.

## Prompt(s)

The student instructed:

> Yes, send the 19 recommended families through the same blinded ten-agent
> scoring process

## What the assistant produced

- Created `ai/FINANCE_LEXICON_EXPANSION_BLIND_REVIEW.md` with the VADER `[-4, 4]`
  scale, explicit `0.0 = exclude/too ambiguous` instruction, 19 families and
  variants, supplied-corpus frequencies, intended contexts, and representative
  real headlines.
- Sent the brief to ten separate sub-agents with different review perspectives.
  Each was barred from inspecting the production lexicon, prior scores, source
  code, generated artifacts, other reviewers, or other scorecards.
- Collected all 190 requested numeric scores without editing or rejecting any
  response.
- Stored the raw second-round scores beside the original 150 scores. Production
  family values are calculated in code as the unweighted mean of all ten values,
  including any zero/exclusion votes.
- Propagated each family mean to its explicit variants. The production lexicon
  now has 34 canonical families and 77 explicit variants.
- Rescored the full headline corpus, rebuilt the ticker-day and sector-day
  indices, regenerated the report figure, and created a 38-row review sheet with
  two real supplied headlines per expansion family.

## Averaged expansion scores

| Family | Mean | Sample SD | Range | Zero votes |
|---|---:|---:|---:|---:|
| rebound | 1.67 | 0.116 | 1.5 to 1.8 | 0 |
| surpass | 1.91 | 0.191 | 1.6 to 2.1 | 0 |
| upside | 1.76 | 0.165 | 1.5 to 2.0 | 0 |
| blowout | 2.05 | 0.425 | 1.3 to 2.5 | 0 |
| outperforming | 1.90 | 0.189 | 1.6 to 2.2 | 0 |
| slump | -1.99 | 0.185 | -2.3 to -1.8 | 0 |
| selloff | -2.20 | 0.176 | -2.5 to -2.0 | 0 |
| rout | -2.29 | 0.831 | -2.8 to 0.0 | 1 |
| headwind | -1.41 | 0.129 | -1.6 to -1.2 | 0 |
| slowdown | -1.54 | 0.117 | -1.7 to -1.4 | 0 |
| overvalued | -1.65 | 0.127 | -1.8 to -1.5 | 0 |
| downturn | -1.91 | 0.137 | -2.2 to -1.8 | 0 |
| contraction | -1.54 | 0.171 | -1.8 to -1.3 | 0 |
| antitrust | -1.06 | 0.389 | -1.4 to 0.0 | 1 |
| recall | -1.39 | 0.743 | -1.9 to 0.0 | 2 |
| breach | -2.04 | 0.151 | -2.3 to -1.8 | 0 |
| outage | -1.95 | 0.135 | -2.2 to -1.7 | 0 |
| fine_penalty | -1.80 | 0.156 | -2.1 to -1.5 | 0 |
| delist | -2.35 | 0.207 | -2.7 to -2.0 | 0 |

## What was wrong or risky

- `0.0` was defined as an exclusion recommendation, but the student's requested
  aggregation rule was the average rather than unanimity or veto. Therefore,
  zero votes remain numerically in the mean instead of automatically removing a
  family. This materially raises dispersion for `rout`, `recall`, and to a lesser
  extent `antitrust`.
- The panel is prompt-independent but not institutionally or model-family
  independent: all reviewers are AI sub-agents in the same environment. Agreement
  is useful evidence, not a replacement for the student's real-headline labels.
- `blowout` has no exclusion vote but wider score dispersion than most ordinary
  families. It should not be described as precisely calibrated.
- The candidate set was frozen using text evidence before the Phase 5 fusion
  test. It must not be narrowed later because some term makes returns look worse.
- Adding 46 explicit variants expands model reach. Lower neutrality is not itself
  evidence of better classification or return predictability.

## Checks performed

- Ten reviewers, 19 families, and 190 raw second-round scores are present.
- Every score lies in `[-4, 4]`; all zero votes are retained.
- A regression test independently recalculates all 19 means, verifies selected
  exact results and zero-vote counts, and confirms variants share family values.
- Combined evidence contains 340 raw scores and 34 family summaries across the
  two blind rounds.
- All 146,836 clean headlines are rescored; 146,830 aligned rows reconcile to the
  ticker-day panel and six post-sample headlines remain excluded from the index.
- All eight unique-key, count, no-news, bounded-score, equal-weight-sector, and
  prior-observed-day-lag identities pass.
- The expansion review sheet contains two deterministic real-headline cases for
  every family, or 38 rows total.
- Selected Phase 4 source and tests pass Ruff. The report figure passes automated
  checks and was visually inspected after regeneration.
- The complete Project B suite passes 43 tests, including both exact panel-mean
  regressions and the earlier real-data portfolio/frequency reconstructions.

## Current model effect

- Plain neutral count/share: 72,790 / 49.57%.
- Expanded finance neutral count/share: 68,487 / 46.64%.
- Expanded finance scores differ from plain VADER for 9,564 headlines and change
  5,778 polarity classifications.
- These are classification-coverage changes, not evidence that the index predicts
  returns or improves a fund. That question remains Phase 5.

## Student review still required

- Label all rows in
  `results/tables/finance_lexicon_expansion_validation_cases.csv`, especially the
  families with exclusion votes or higher dispersion.
- Decide whether any zero vote should become a human veto despite the arithmetic-
  mean rule used for this run.
- Confirm the expanded production lexicon before Phase 4 is closed and Phase 5
  uses its one-day-lagged signal.
