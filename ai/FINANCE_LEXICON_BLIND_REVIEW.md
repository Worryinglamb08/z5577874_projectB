# Finance lexicon blind-review brief

## Purpose

Independently assign lexical valence scores for a compact financial-headline
extension to plain VADER. Reviewers must not inspect the existing Phase 4
lexicon scores before responding.

Use VADER's approximate lexical scale:

- `-4`: extremely negative;
- `0`: neutral, too ambiguous, or recommend excluding the term;
- `+4`: extremely positive.

Score the term's usual meaning in a listed-company or market headline, not its
ability to predict returns. VADER separately handles negation, intensifiers, and
punctuation. Every reviewer must provide one numeric score for every family.

## Term families and observed corpus frequency

| Canonical family | Explicit variants | Occurrences | Intended financial context |
|---|---|---:|---|
| beat | beat, beats, beating | 3,036 | Results or performance above a benchmark |
| upgrade | upgrade, upgraded, upgrades | 658 | Upward analyst, issuer, or credit assessment |
| outperform | outperform, outperformed, outperforms | 493 | Performance above a benchmark |
| bullish | bullish | 414 | Positive market direction |
| buyback | buyback, buybacks | 201 | Issuer share repurchase |
| miss | miss, missed, misses | 964 | Results below a benchmark |
| downgrade | downgrade, downgraded, downgrades | 355 | Downward analyst, issuer, or credit assessment |
| underperform | underperform, underperformed, underperforms | 74 | Performance below a benchmark |
| bearish | bearish | 59 | Negative market direction |
| default | default, defaults | 52 | Failure to meet a financial obligation |
| bankruptcy | bankruptcy | 49 | Formal financial-distress process |
| insolvency | insolvency | 1 | Inability to meet obligations |
| impairment | impairment | 18 | Reduction in an asset's carrying value |
| writedown | writedown, writedowns | 21 | Reduction in an asset's carrying value |
| layoff | layoff, layoffs | 83 | Workforce reduction |

The 31 explicit variants occur 6,478 times in the 146,836-headline corpus.

## Representative supplied headlines

- `74% of Warren Buffett's Portfolio Is in 5 Stocks -- but Only This 1 Is Beating the Market`
- `B of A Securities Downgrades Dow to Underperform, Announces $37 Price Target`
- `Oppenheimer Bullish On Wireless Services, Upgrades American Tower, Crown Castle`
- `Bed Bath & Beyond shares sink over 40% after bankruptcy filing`
- `US offshore wind writedowns seen soaring with Orsted earnings`
- `NextEra Energy, Inc. Q4 Loss Increases, but beats estimates`
- `Comcast shares are trading lower following Q4 results. Despite beating EPS and sales estimates, the company announced a drop in TV subscribers for the quarter.`
- `Amgen shares are trading lower after ... guidance below estimates ... downgraded ... to Underperform.`

These examples illustrate why the lexicon supplies only token valence: the full
VADER sentence score must still combine positive and negative words and context.

## Required response

Return exactly one JSON object with these 15 keys and numeric values only:

`beat`, `upgrade`, `outperform`, `bullish`, `buyback`, `miss`, `downgrade`,
`underperform`, `bearish`, `default`, `bankruptcy`, `insolvency`, `impairment`,
`writedown`, `layoff`.

Use `0.0` where the family should be excluded because it is neutral or too
context-dependent. Do not edit project files.
