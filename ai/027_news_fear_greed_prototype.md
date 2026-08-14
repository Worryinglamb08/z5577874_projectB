# Prompt log - Stockist News Fear and Greed prototype

## What I wanted

Test whether the News Signal page could add a market-wide fear-and-greed level
and a standardized panel similar to the supplied reference figure.

## Prompt(s)

> Another improvement I wonder we can do is make the news a fear/greed index see
> attached. It has fear greed and the bottom one standardized. Possible?

> Lets try it

## What the assistant produced

- A precomputed 1,006-date market news artifact across all 50 supplied stocks.
- A two-panel Plotly figure with the selected 21- or 63-trading-day 0–100 level
  above daily full-sample standardized bars.
- Same-window headline metrics and an explicit distinction from the CNN Fear &
  Greed Index.
- The original sector sentiment, coverage and fusion evidence below the new
  market overview so the brief requirement remains satisfied.

## What was wrong or risky

Calling a VADER-only score a generic market Fear & Greed Index would overstate
what it measures. Directly rescaled finance-adjusted sentiment is above 50 on
99.304% of dates and every valid 21-day mean, so the raw level has a persistent
positive baseline. Full-sample standardization uses future observations from
the perspective of early dates and therefore cannot be treated as a live or
tradable signal. A low standardized score can also reflect sparse positive news:
the final sample dates contain news for only one of 50 stocks.

## What I changed and why

Named the feature **Stockist News Fear and Greed Index** and described it as
headline language only. Kept the upper panel's direct mapping transparent,
labelled its zoomed axis, and labelled the lower panel as fixed-sample and
descriptive. Added coverage detail to bar hovers and did not alter the lagged,
coverage-aware signal used by the fund experiment. The app loads the new CSV;
it does not run VADER or rebuild the index interactively.

## Validation

- The aggregation test verifies constituent weighting, 0–100 mapping,
  standardization, coverage breadth and descriptive labelling.
- The chart test verifies the rolling line, standardized bars, background
  bands, units and coverage hover fields.
- App tests verify market-first ordering, exact metric labels, artifact loading
  and preservation of the sector detail.
