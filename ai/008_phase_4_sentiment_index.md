# Prompt log — Phase 4 finance sentiment and sector index

**Date:** 13 August 2026  
**Scope:** Plain and finance-adjusted VADER, ticker-day aggregation, the
standalone sector index, tradable lagging, validation, and the report exhibit

## What I wanted

Move from the verified headline-alignment and coverage foundation to a validated
standalone equity-sector sentiment index, without allowing same-day or future
headlines into a tradable signal.

## Prompt(s)

The student instructed:

> Move to phase 4

The project roadmap and brief already required a plain-VADER baseline, a small
auditable finance lexicon, ticker-first and equal-weight sector aggregation,
explicit no-news treatment, and at least a one-observed-trading-day lag.

## What the assistant produced

- Replaced the sentiment placeholder with a typed headline-to-sector pipeline.
- Scored every preserved headline with independent plain and finance-adjusted
  NLTK VADER analysers; neither text cleaning nor lowercasing is applied to the
  scored string.
- Initially proposed a 31-token finance lexicon covering earnings beats/misses,
  upgrades/downgrades, outperform/underperform, bullish/bearish language,
  buybacks, default/distress, impairments, writedowns, and layoffs. Variants are
  explicit because VADER does not stem terms. A later student-requested blind
  panel replaced every initial score; see the multi-agent revision below.
- Created an audit containing the plain score, proposed finance score, add versus
  override status, observed token count, rationale, scale, and review status.
- Averaged headline compound scores within ticker-day, assigned neutral zero to
  no-news ticker-days without carrying stale information, and retained
  `has_news` so no information is distinguishable from neutral language.
- Equal-weighted all five ticker-day values within each sector, retained
  covered-only diagnostics and existing coverage features, and created plain and
  finance one-day lags within sector.
- Exported the required app-readable sector index, compact model/sector/
  validation evidence, and a balanced real-headline review sheet.
- Added a ten-panel Stockist Funds sector time-series exhibit with faint daily
  values and a 21-day rolling mean.
- Added synthetic tests for finance-language corrections, duplicate rejection,
  no-news neutrality, exact five-ticker equal weighting, prior-day lagging, and
  future-headline leakage.

## What was wrong or risky

- Plain VADER originally scores `beating` at `-2.0`, which can classify financial
  headlines such as “beating estimates” as negative. The finance lexicon
  overrides this context-specific false negative, but a token rule can still be
  wrong in a non-financial use of the word.
- Terms such as `default` and `layoffs` are context-dependent. The assistant must
  not present the proposed scores as student-approved or objectively correct.
  Both the lexicon and real-headline cases remain marked for student review.
- Treating no news as zero can dilute the sector index when coverage is thin.
  Carry-forward was rejected because it would make stale information appear
  current; the existing breadth, concentration, and confidence fields remain
  available for Phase 5 to qualify thin-coverage values.
- A score of zero can mean either observed neutral text or no news. Separate
  `has_news`, count, covered-only score, and no-news-policy fields preserve that
  distinction.
- The first validation-case selector overrepresented positive “beating” examples.
  It was changed to select one positive and one negative finance-adjusted case per
  sector rather than create a flattering audit sheet.
- NLTK and its VADER lexicon are build-only resources. They were installed and
  downloaded locally for reproduction but remain outside app requirements; the
  deployed app must read the committed CSV.
- Automated figure validation passed while the legend still touched a panel
  title and repeated y-axis labels dominated the page. Manual visual inspection
  caught both issues; space was reserved for the legend and shared axis labels
  replaced repeated ones.

## Checks performed

- 146,836 clean headlines scored; 146,830 aligned headlines reconcile exactly to
  ticker-day counts; six post-sample rows remain excluded from the index.
- Plain neutral count/share: 72,790 / 49.57%; the current expanded finance-neutral
  count/share is 68,487 / 46.64% after two ten-reviewer rounds.
- The current 77-token, 34-family finance lexicon changes 9,564 compound scores
  and 5,778 polarity labels. The initial compact 31-token round remains separately
  identifiable in the raw panel evidence.
- Ticker-day panel: 50,300 unique `(date, ticker)` rows. Sector index: 10,060
  unique `(date, sector)` rows across 1,006 dates and ten sectors.
- Every no-news ticker-day has plain and finance score zero, without a carry-
  forward value.
- Every sector score reconciles to the equal-weight mean of its five ticker-day
  scores to numerical tolerance.
- Every lagged score equals the previous observed equity date's raw score within
  sector; changing a future headline cannot alter an earlier lag.
- All compound scores remain in `[-1, 1]` and all selected Phase 4 identities
  report `pass`.
- The targeted Phase 4 test file passes four tests before the full-suite run.
- The complete Project B suite passes 43 tests in the real-data environment;
  selected Phase 4 files pass Ruff. A full-project Ruff run still reports ten
  pre-existing starter/helper issues in the supplied `data_access.py`,
  `check_handin.py`, and starter `streamlit_app.py`; these are outside the Phase 4
  code and remain visible for the later app/reproducibility phases.
- The figure passes the selected context, label, tick, readability, and image
  checks and was manually inspected after the layout correction.

## Key observed results

- Plain VADER leaves nearly half of the supplied financial headlines neutral.
  The compact finance adjustment reduces, but does not eliminate, that limitation.
- Finance adjustment raises mean sector sentiment modestly in every sector; that
  direction alone is not evidence that the extension predicts returns.
- Coverage differs materially: mean covered-ticker breadth is about 53% for
  Materials and 94% for Consumer. Phase 5 therefore needs to keep sentiment and
  evidence quality separate rather than treating every sector-day equally.
- The sector paths are noisy at daily frequency, so the report exhibit shows the
  underlying daily index faintly and a 21-day rolling mean prominently. The
  app-facing artifact still stores the un-smoothed daily values and lagged signal.

## What I changed and why

The assistant selected explicit neutral-zero handling instead of carry-forward:
it preserves the complete five-ticker denominator and avoids presenting stale
sentiment as current. Coverage fields and covered-only diagnostics make the
dilution auditable and prepare the independent confidence layer for Phase 5.

The build-figure workflow shaped the final exhibit: ten small multiples avoid an
unreadable ten-line overlay, use one common scale, retain the daily index, add a
readability-only rolling mean, and include self-contained source, sample, units,
and timing context. Manual inspection overrode the first automated pass.

## Student review still required

- Review every row of `results/tables/finance_lexicon_audit.csv`; approve or
  revise the term set and scores rather than treating the AI proposal as fact.
- Label the balanced real cases in
  `results/tables/sentiment_validation_cases.csv` using the student's own reading
  of each headline, then record disagreements and any lexicon revisions.
- Confirm the neutral-zero no-news policy and the decision not to carry sentiment
  forward.
- Rewrite any report interpretation in the student's own words. Do not claim
  predictive value until the separately controlled Phase 5 fusion test exists.

## Follow-up event audit accepted before Phase 5

The student inspected the Utilities spike ending 15 February 2022 and the Tech
decline ending 25 October 2022 before moving to fusion. The exact decompositions,
model limitations, and agreed robustness treatment are recorded in
`ai/SENTIMENT_EVENT_AUDIT.md`. The primary index is retained to prevent hindsight
editing; cross-ticker repetition and mixed-language classification are explicit
sensitivities and interpretation limits.

## Multi-agent score revision

### Follow-up prompt

The student asked:

> Were the scores created by 1 agent only?

After the assistant confirmed they were, the student instructed:

> Yes can you do it with 10 sub agents and use the average

### Review design

- The assistant created `ai/FINANCE_LEXICON_BLIND_REVIEW.md` with the VADER
  `[-4, 4]` scale, 15 canonical families, their 31 explicit variants, corpus
  frequencies, intended financial context, representative supplied headlines,
  and an explicit `0.0 = exclude` rule.
- Ten separate sub-agents received only that brief. They were explicitly barred
  from inspecting the former lexicon, code, output tables, other scorecards, or
  other agents' work.
- Each agent returned all 15 numeric values. The responses were collected before
  any aggregation; no score was rejected or edited.
- The production value for each family is the unweighted arithmetic mean of its
  ten scores. Each reviewer therefore has weight `0.1`. Word variants inherit the
  family mean instead of being averaged as separate votes.
- The original single-agent values no longer influence scoring. All 150 raw
  scores, reviewer roles, weights, means, standard deviations, minima, maxima,
  and exclusion-vote counts are saved in the panel evidence tables.

### Averaged canonical scores

| Family | Mean | Sample SD | Range |
|---|---:|---:|---:|
| beat | 2.06 | 0.190 | 1.8 to 2.4 |
| upgrade | 2.22 | 0.123 | 2.0 to 2.4 |
| outperform | 2.04 | 0.190 | 1.7 to 2.3 |
| bullish | 2.36 | 0.126 | 2.1 to 2.5 |
| buyback | 1.32 | 0.123 | 1.1 to 1.5 |
| miss | -2.05 | 0.184 | -2.4 to -1.8 |
| downgrade | -2.30 | 0.156 | -2.5 to -2.0 |
| underperform | -2.05 | 0.196 | -2.3 to -1.7 |
| bearish | -2.36 | 0.126 | -2.5 to -2.1 |
| default | -3.18 | 0.132 | -3.4 to -3.0 |
| bankruptcy | -3.49 | 0.074 | -3.6 to -3.4 |
| insolvency | -3.39 | 0.099 | -3.5 to -3.2 |
| impairment | -2.05 | 0.118 | -2.2 to -1.8 |
| writedown | -2.21 | 0.110 | -2.4 to -2.0 |
| layoff | -2.07 | 0.149 | -2.3 to -1.8 |

### Risks and checks

- The review was independent with respect to prompts and information flow, but
  all reviewers were AI sub-agents from the same assistant environment. This is
  not human validation, and model-family similarity can explain some agreement.
- Giving reviewers different professional perspectives adds useful framing but
  does not make the panel statistically representative of finance practitioners.
- No reviewer chose the allowed zero/exclusion option. This unanimity supports
  inclusion but may also reflect shared model priors, so the real-headline student
  review remains the important external check.
- A new test recalculates every family mean directly from the ten saved
  scorecards, checks the reviewer count, checks selected exact means, and confirms
  variants inherit one family value.
- Rescoring and index generation passed all eight existing reconciliation and
  leakage identities. The refreshed report figure passed automated checks and
  visual inspection.
