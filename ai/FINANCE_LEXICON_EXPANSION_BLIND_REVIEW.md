# Finance lexicon expansion blind-review brief

## Purpose

Independently score 19 candidate financial-headline term families for a compact
extension to plain VADER. Reviewers must not inspect the production lexicon,
earlier finance scores, other reviewers, or generated sentiment outputs.

Use VADER's approximate lexical valence scale:

- `-4`: extremely negative;
- `0`: neutral, too ambiguous, or recommend exclusion;
- `+4`: extremely positive.

Score the term's usual meaning in a listed-company or market headline, not its
ability to predict future returns. VADER separately handles negation,
intensifiers, punctuation, and the rest of the sentence. Use `0.0` where an
unconditional unigram family would be too context-dependent even if it is
finance-related.

## Candidate families and supplied-corpus frequency

| Canonical family | Explicit variants | Matching headlines | Intended financial context |
|---|---|---:|---|
| rebound | rebound, rebounds, rebounded, rebounding | 836 | Recovery in price, activity, or results |
| surpass | surpass, surpasses, surpassed, surpassing | 313 | Results or performance above a benchmark |
| upside | upside, upsides | 726 | Favourable valuation or return potential |
| blowout | blowout, blowouts | 58 | Exceptionally strong results or launch |
| outperforming | outperforming | 79 | Performance above a benchmark |
| slump | slump, slumps, slumped, slumping | 337 | Adverse decline or weak activity |
| selloff | selloff, selloffs, sell-off, sell-offs | 512 | Broad or security-level selling decline |
| rout | rout | 114 | Severe market or security decline |
| headwind | headwind, headwinds | 92 | Obstacle to operating or financial performance |
| slowdown | slowdown, slowdowns | 155 | Adverse deceleration in activity or growth |
| overvalued | overvalued | 51 | Valuation viewed as too high |
| downturn | downturn, downturns | 94 | Negative economic, industry, or company cycle |
| contraction | contraction, contractions | 28 | Reduction in economic activity, revenue, or demand |
| antitrust | antitrust | 137 | Competition-law scrutiny or action |
| recall | recall, recalls, recalled, recalling | 44 | Product withdrawal for quality or safety reasons |
| breach | breach, breaches, breached | 35 | Covenant, data, contract, or rules failure |
| outage | outage, outages | 58 | Operational or service disruption |
| fine_penalty | fined, fines | 50 | Monetary regulatory or legal penalty; excludes ambiguous word `fine` |
| delist | delist, delisted, delisting | 13 | Loss or threatened loss of exchange listing |

Counts are headline matches and can overlap across families.

## Representative supplied headlines

- `After Lackluster 2019, Pfizer Stock Could Rebound in 2020`
- `Intel (INTC) Q4 Earnings and Revenues Surpass Estimates`
- `5 Dividend Growth Stocks With Upside To Analyst Targets`
- `5 Biggest Takeaways From Walmart's Blowout First Quarter`
- `Why Mattel Stock Was Slumping Today`
- `No Rebound to This Morning's Selloff`
- `Dow Jones Dives 450 Points In Stock Market Rout As Deadly China Virus Spreads`
- `Dow Jones News: American Express Hit by Valuation Concerns; Intel Faces Headwinds in 2020`
- `Walmart Gets Caught in the Late 2019 Retail Slowdown`
- `There's No Doubt Anymore: Buffett Thinks Stocks Are Grossly Overvalued`
- `Advanced Micro Devices Stock Will Survive the Downturn`
- `Will Top-Line Contraction Hurt Intel (INTC) Q1 Earnings?`
- `Walmart's Flipkart Faces Antitrust Probe in India`
- `Abbott Labs Recalls Some Catheters Due to Possible Defects`
- `Spirit says it may breach financial covenants after deeper 737 production cut`
- `T-Mobile Users Suffered 12-Hour Voice and Text Outage On Monday`
- `T-Mobile Fined $200 Mln In Sprint Lifeline Investigation`

The full sentence may contain mitigating or mixed information. The requested
score concerns only the listed token family; use zero when that family is not
reliably polar enough to include unconditionally.

## Required response

Return exactly one JSON object with these 19 keys and numeric values only:

`rebound`, `surpass`, `upside`, `blowout`, `outperforming`, `slump`, `selloff`,
`rout`, `headwind`, `slowdown`, `overvalued`, `downturn`, `contraction`,
`antitrust`, `recall`, `breach`, `outage`, `fine_penalty`, `delist`.

Do not add prose and do not edit project files.
