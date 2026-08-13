# Finance lexicon expansion research

**Date:** 13 August 2026  
**Purpose:** Identify finance-relevant terms beyond the current 31-token,
15-family VADER extension without importing a large external dictionary blindly.

> **Follow-up status:** The student subsequently approved sending the 19
> `test_now` families through a second ten-agent blind scoring round. Their
> nonzero arithmetic means are now applied. The research classifications remain
> the frozen candidate-selection evidence; see
> `ai/010_phase_4_expansion_blind_panel.md` for the later scoring and model effect.

## Outcome

The strongest next step is a controlled expansion, not wholesale adoption of
FinVADER or another dictionary. Nineteen additional families are suitable for a
second scoring and headline-validation round, five movement-verb families need
subject-aware phrase rules, three event families require more manual review, one
generic term should not be added, and volatility belongs in a separate risk or
uncertainty measure.

No candidate in this memo has been added to the production lexicon. The current
ten-reviewer scores and Phase 4 index therefore remain unchanged pending student
approval and validation.

## Sources inspected

### FinVADER

[FinVADER](https://github.com/PetrKorab/FinVADER) combines two external resources:

- Henry's earnings-press-release word list; and
- SentiBigNomics, an economic and financial aspect-based lexicon.

Its implementation does not simply apply the published SentiBigNomics values:
it multiplies them by `0.1` before updating VADER and merges Henry afterward.
Therefore, FinVADER's bundled values cannot be copied into this project's VADER
scale without a new calibration decision.

### SentiBigNomics

The original [SentiBigNomics repository](https://github.com/consose/SentiBigNomics)
describes a fine-grained `[-1, 1]` lexicon used inside an aspect-based system.
That system extracts text chunks related to a token of interest and includes
negation, tense, location, and exclusion rules. Using its unigrams alone inside
plain VADER removes that context and changes the model substantially.

### Henry

Henry's list was designed for earnings press releases, which is closer to this
project's corporate-news domain than a general dictionary. The list is exposed
through FinVADER and traces to Elaine Henry's 2008 study,
[*Are Investors Influenced by How Earnings Press Releases Are Written?*](https://journals.sagepub.com/doi/10.1177/0021943608319388).
Its FinVADER representation assigns most included words a common `+1.5` or
`-1.5`, which provides direction rather than fine calibration.

### Loughran-McDonald

The official [Loughran-McDonald Master Dictionary](https://sraf.nd.edu/loughranmcdonald-master-dictionary/)
was downloaded in its 1993--2025 CSV form. Its sentiment fields identify
category membership and the year a word entered a category; values such as
`2009` are not valence magnitudes. It is primarily based on financial filings,
so it is useful for candidate provenance but not automatically calibrated to
short news headlines.

### Project corpus and plain VADER

Every external candidate was intersected with the project's 146,836 clean
headlines, compared with NLTK VADER and the existing 31-token extension, and
screened using actual supplied headline contexts. Counts below are headline
matches, not forecasts or performance claims.

## Recommended second-round candidates

These terms are absent from plain VADER and the current extension, appear in the
supplied corpus, and have relatively clear finance meaning. They should still go
through the same blind ten-reviewer scoring process and balanced real-headline
review before production use.

### Positive

| Family | Headline matches | Plain-neutral cases | Why it is promising |
|---|---:|---:|---|
| rebound | 836 | 324 | Recovery language; supported by SentiBigNomics and Loughran-McDonald. |
| surpass | 313 | 245 | Usually results above estimates; supported by both sources. |
| upside | 726 | 421 | Finance-specific favourable potential. |
| blowout | 58 | 41 | Strong earnings or launch descriptor in this corpus. |
| outperforming | 79 | 60 | Missing variant of the already-approved `outperform` family. |

### Negative market and operating conditions

| Family | Headline matches | Plain-neutral cases | Why it is promising |
|---|---:|---:|---|
| slump | 337 | 133 | Supported by Henry and SentiBigNomics. |
| selloff | 512 | 220 | Highly finance-specific decline language found directly in the corpus. |
| rout | 114 | 50 | Acute adverse market decline in the supplied headlines. |
| headwind | 92 | 47 | Finance-specific obstacle language. |
| slowdown | 155 | 26 | Supported by SentiBigNomics and Loughran-McDonald. |
| overvalued | 51 | 36 | Clear negative valuation assessment. |
| downturn | 94 | 42 | Supported by Henry, SentiBigNomics, and Loughran-McDonald. |
| contraction | 28 | 22 | Adverse economic or top-line contraction. |

### Negative corporate and regulatory events

| Family | Headline matches | Plain-neutral cases | Important boundary |
|---|---:|---:|---|
| antitrust | 137 | 51 | A rejected lawsuit or approval despite concerns can reverse sentence meaning. |
| recall | 44 | 24 | Usually product-quality or safety risk. |
| breach | 35 | 18 | Usually covenant, contract, rules, or data failure. |
| outage | 58 | 28 | Operational disruption. |
| fined / fines | 50 | 25 | Add penalty variants only; never override ambiguous word `fine`. |
| delist | 13 | 9 | Low-frequency but highly finance-specific listing failure. |

Full variants, source agreement, and recommendations are saved in
`results/tables/finance_lexicon_candidate_research.csv`.

## Terms requiring phrase or subject context

Movement words appear often and plain VADER frequently misses them, but a fixed
polarity can be wrong:

| Family | Matches | Problem |
|---|---:|---|
| surge | 1,066 | A price or revenue surge is positive; a cost or volatility surge is negative. |
| soar | 864 | Shares soaring is positive; losses or inflation soaring is negative. |
| plunge | 340 | Price or revenue plunging is negative; costs plunging can be positive. |
| tumble | 328 | Direction depends on what tumbles. |
| sink | 593 | Often adverse price language, but still subject-dependent. |

Rather than unconditional unigram scores, a later extension could recognise
limited, disclosed patterns such as:

- `shares|stock|price|revenue|profit + surge|soar` as favourable;
- `shares|stock|price|revenue|profit + plunge|tumble|sink` as adverse;
- `costs|expenses|losses + surge|soar` as adverse; and
- `costs|expenses|losses + plunge|tumble` as favourable.

This would be a new phrase-rule model and must be separately tested; it should
not be hidden inside a word-score update.

## Candidates needing caution

- `undervalued` appears in 498 headlines and plain VADER leaves 387 neutral.
  Financially it is generally favourable, but SentiBigNomics assigns it a
  negative value and many supplied headlines ask whether a stock is undervalued.
  It needs human-labelled cases before inclusion.
- `probe` and `investigation` describe adverse scrutiny, but sentences about a
  settlement, closure, rejection, or external event can change the net meaning.
- `halt` should not be added as an unconditional negative word. Many of the 141
  matched headlines describe neutral exchange circuit breakers or news-
  dissemination halts.
- `volatility`, `volatile`, and `choppy` match 581 headlines. Loughran-McDonald
  marks the first two as both negative and uncertainty. For this project, they
  are better treated as evidence of risk or uncertainty than as directional
  positive/negative sentiment.

## External terms rejected for unconditional use

The screening rejected several high-frequency words despite their appearance in
external lexicons:

- Henry: `up`, `down`, `higher`, `high`, `more`, `most`, `record`, `above`,
  `under`, and `below` are too dependent on what changed.
- SentiBigNomics: `cash`, `income`, `revenue`, `money`, `guidance`, `option`,
  `inflation`, `right`, `open`, and `large` are concepts or quantities, not
  reliable standalone polarity.
- Loughran-McDonald: `despite`, `claims`, `questions`, and `discloses` reflect
  dictionary/document context but are unsafe as unconditional headline valence.
- `raise`, `cut`, and `record` require phrase context: raising guidance differs
  from raising capital; cutting costs differs from cutting a dividend; a record
  profit differs from a record loss.

## Proposed validation before adding anything

1. Freeze the candidate set before looking at investment returns.
2. Have ten score-blind sub-agents score only the `test_now` families, retaining
   all raw scores and their unweighted means.
3. Draw balanced real headlines for every family, including negation, questions,
   mixed clauses, and counterexamples.
4. Require student labels and record disagreements.
5. Compare plain VADER, the current compact lexicon, and the expanded lexicon on
   those held-out cases.
6. Add phrase rules as a separate model variant, not as invisible preprocessing.
7. Rebuild Phase 4 and then carry only the approved, one-day-lagged index into
   Phase 5. Do not choose terms using fusion backtest performance.

## Conclusion

The most defensible immediate expansion pool is:

`rebound`, `surpass`, `upside`, `blowout`, `outperforming`, `slump`, `selloff`,
`rout`, `headwind`, `slowdown`, `overvalued`, `downturn`, `contraction`,
`antitrust`, `recall`, `breach`, `outage`, `fined/fines`, and `delist`.

The high-frequency movement words are potentially valuable but should be a
separate subject-aware experiment. This keeps the production signal auditable
and avoids converting every finance-related noun or movement verb into assumed
sentiment.
