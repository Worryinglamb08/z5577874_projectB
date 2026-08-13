# Phase 6 final-figure review

**Date:** 13 August 2026  
**Review size:** Exported Word/A4 PNGs at their intended report aspect ratios  
**Scope:** All nine figures listed in `results/tables/exhibit_catalog.csv`

## Review outcome

| Figure | Manual checks | Outcome |
|---|---|---|
| `fund_growth` | Three panels, common method encoding, dollar ticks, legend, source note | Pass |
| `combined_fund_drawdowns` | Percentage scale, zero reference, four legible paths, legend and source note | Pass |
| `fund_risk_return` | Point-label association, panel axes, clipping and collisions | Pass after correction |
| `fund_sharpe_by_family` | Three family groups, five method bars, value labels, legend, source note | Pass |
| `combined_weight_history` | Five method panels, supplied-sector bands, one Crypto band, 100% stacks, dates and source note | Pass |
| `sector_sentiment_index` | Ten sector panels, common scale, raw/rolling distinction and date labels | Pass |
| `coverage_confidence_index` | Ten sector panels, bounded scale, raw/rolling distinction and date labels | Pass |
| `rebalance_frequency_tradeoff` | Turnover percentages, schedule labels, method separation and source note | Pass |
| `fusion_growth_comparison` | Dollar scale, base/tilt distinction, legend and source note | Pass |

## Correction made during review

The first `fund_risk_return` export placed two Maximum Sharpe labels against panel
edges and crowded nearby labels. Offsets are now specific to each asset-family
and method combination. The figure was regenerated, passed the automated checks,
and was visually inspected again. Every label is inside its panel and associated
with the intended point.

## Coverage-chart interpretation check

The rolling confidence lines fall together near the end of December 2023. This
is not a rendering or rolling-window bug. The market histories continue through
29 December while the supplied headline evidence stops producing covered
company-days after 18 December. The explicitly modelled no-news values are zero,
so they progressively lower the 21-observation rolling means. The caption states
that no-news days equal zero and that confidence measures evidence support, not
classification accuracy.

## Accepted limitations

- Dense daily paths are intentionally faint behind more legible 21-day rolling
  lines in the sentiment and confidence small multiples.
- The weight-history figure aggregates the supplied equity classifications by
  sector and all cryptoassets into one Crypto band; its caption explains that
  transformation.
- Growth and drawdown figures are historical simulations, not forecasts. Their
  captions and source notes preserve that context.
