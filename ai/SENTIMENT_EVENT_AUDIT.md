# Sentiment event audit and robustness decisions

**Date:** 13 August 2026  
**Scope:** Utilities in early 2022 and Tech in late 2022  
**Status:** Findings accepted as limitations before the Phase 5 fusion result was
inspected

## Why this audit was added

The 21-observed-day lines in the sector exhibit are descriptive rolling means,
not single-day event measures. The student asked what caused two visible moves
before deciding whether the sentiment model was credible. The audit therefore
traced each rolling endpoint back to its 21 trading dates, ticker-day inputs,
headline classifications, finance-lexicon increment, coverage, and repeated
cross-ticker titles.

## Utilities: early-2022 positive spike

- The rolling maximum is `0.234943` on 15 February 2022. It summarises the 21
  observed equity dates from 18 January to 15 February, rather than an event
  occurring only on the endpoint.
- The window contains 176 ticker-mapped headline rows: 121 positive, 50 neutral,
  and five negative. Mean breadth is 83.81%, or about 4.19 of five companies per
  day, and mean coverage confidence is 72.45%. Thin coverage is therefore not
  the explanation.
- The main news flow is the fourth-quarter reporting cycle: earnings beats and
  outlooks, renewable-energy and capital-investment plans, dividends, and
  bullish stock-selection articles. NextEra is the strongest contributor, but
  all five constituent ticker-day means are positive.
- Plain VADER produces `0.215108`; the expanded finance lexicon adds only
  `0.019835`. The direction therefore exists without the custom word scores.
- There are 22 excess repeated date-title rows across different Utilities
  tickers, or 12.5% of the mapped rows. Retaining one date-title instance lowers
  the rolling mean to roughly `0.211`–`0.215`, depending on which ticker mapping
  is retained. The spike remains.
- A mixed headline such as “Q4 Loss Increases, but beats estimates” is pushed
  strongly positive by `beats`, showing that token-level finance corrections can
  overstate tone even when their aggregate contribution is small.

### Utilities conclusion

The positive direction is credible as headline tone. The magnitude is mildly
inflated by cross-ticker repetition and a small number of finance-lexicon edge
cases. It is not evidence that utility returns or investor expectations moved by
the same amount.

## Tech: late-2022 loss of positivity

- The visible decline bottoms at `0.050730` on 25 October 2022 and covers 27
  September to 25 October. The rolling value remains positive; “more negative”
  means less positive than its usual level, not below zero. It is about `0.084`
  by 30 December.
- The window contains 571 ticker-mapped rows: 206 positive, 254 neutral, and 111
  negative. Mean breadth is 96.19%, or 4.81 of five companies, and mean coverage
  confidence is 88.15%.
- The main negative themes are AMD's weaker-than-expected third-quarter revenue
  warning and the PC inventory correction, Intel slowdown/job-cut coverage,
  advanced-chip export restrictions to China, persistent inflation and rate-hike
  fears, recession language, and the broad Nasdaq/semiconductor sell-off.
- Intel has the weakest 21-day constituent score (`0.007092`), followed by Nvidia
  (`0.029176`) and Qualcomm (`0.034869`). Adobe and AMD remain more positive.
- Plain VADER produces `0.049192`, almost identical to finance VADER. The custom
  finance lexicon did not create the decline.
- Cross-ticker repetition is more material than in Utilities: 137 excess
  date-title rows, or 23.99% of the mapped window. Retaining one instance per
  date-title raises the rolling mean to about `0.072`–`0.083`; removing every
  repeated group, an intentionally severe lower-information check, raises it to
  `0.098`.
- Several obvious language failures make the exact magnitude unreliable. For
  example, VADER scores “Qualcomm No Longer Fears Losing Its Largest Customer”
  at `-0.765`, “Buying Qualcomm Near its 52-Week Low Is a No-Brainer” at
  `-0.273`, and “Adobe Stock Still a Screaming Buy” at `-0.382`.

### Tech conclusion

The decline is supported by real macroeconomic and semiconductor-specific bad
news. Its magnitude is overstated by repeated broad-market headlines and false
negative readings of mixed or rhetorically bullish titles.

## Agreed treatment and suggested solution

The primary Phase 4 index is preserved. Rewriting it after seeing conspicuous
events or later portfolio performance would introduce discretionary hindsight.
The following solution is therefore a robustness layer rather than a silent
replacement:

1. Keep the assignment-compliant primary deduplication key
   `(ticker, original date, title)` and the required ticker-day then equal-sector
   aggregation.
2. Add a parallel cross-ticker repetition diagnostic keyed by
   `(aligned trading date, normalised title)`. Report the excess-row share and a
   one-title-one-instance sensitivity beside important sector moves.
3. Flag whether the tracked ticker or company is named directly, the headline is
   a related-company/industry story, or it is a broad-market story. Do not claim
   all mapped rows are company-specific news.
4. Hand-review the highest absolute weighted contributions and mixed-language
   cases. Corrections must be defined before any rerun used as confirmatory
   evidence; the original score remains available.
5. In the app and report, label the solid line as a 21-day rolling headline-tone
   measure and show the exact window, breadth, confidence, and repeated-title
   share on inspection.
6. Use the untouched primary finance index in Phase 5, multiplied by same-day
   coverage confidence and then lagged one observed trading day. Interpret any
   fusion result in light of these robustness limits and do not tune the
   lexicon, deduplication, or tilt after seeing performance.

## Interpretation boundary

The index measures the tone of supplied headlines under a disclosed aggregation
rule. It is not a survey of investors, an article-body model, a return forecast,
or proof of causality. Event explanations in the student's final report must be
rewritten in the student's own words and supported with verified citations.
