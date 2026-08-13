# Finance-adjusted VADER sentiment across equity sectors

## Note
The daily index first averages headlines within ticker-day, assigns zero to ticker-days without news, then equal-weights the five tickers in each sector. The solid line is a 21-observed-day rolling mean shown for readability; the faint line is the underlying daily index. Trading uses the separately stored one-day-lagged value, never the same-day score.

## Sample
2020-01-02 to 2023-12-29

## Units
VADER compound score on [-1, 1]

## Source
Course-provided project_data.zip; Stockist Funds calculations
