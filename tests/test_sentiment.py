"""Finance VADER, equal-weight sector index, and timing tests."""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.finance_lexicon import (  # noqa: E402
    AVERAGED_FAMILY_SCORES,
    EXPANSION_AVERAGED_FAMILY_SCORES,
    EXPANSION_REVIEW_SCORES,
    FINANCE_LEXICON,
    REVIEW_SCORES,
    STUDENT_APPROVED_FAMILY_SCORES,
    STUDENT_EXCLUDED_FAMILIES,
)
from src.news_features import prepare_news_coverage  # noqa: E402
from src.sentiment import (  # noqa: E402
    SentimentValidationError,
    aggregate_ticker_day_scores,
    market_news_index,
    score_headlines,
    sector_sentiment_index,
)


def _equity_prices(dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"date": pd.Timestamp(date), "ticker": ticker, "sector": "Technology"}
            for date in dates
            for ticker in ("AAA", "BBB", "CCC", "DDD", "EEE")
        ]
    )


def _headline(date: str, ticker: str, title: str) -> dict[str, object]:
    return {
        "date": pd.Timestamp(date),
        "ticker": ticker,
        "sector": "Technology",
        "title": title,
        "url": f"https://example.test/{date}/{ticker}/{title}",
        "publisher": "Wire",
    }


def test_finance_lexicon_uses_unweighted_mean_of_ten_blind_reviews() -> None:
    assert len(REVIEW_SCORES) == 10
    for family, mean_score in AVERAGED_FAMILY_SCORES.items():
        expected = sum(scores[family] for scores in REVIEW_SCORES.values()) / 10
        assert mean_score == pytest.approx(expected)
    assert AVERAGED_FAMILY_SCORES["beat"] == pytest.approx(2.06)
    assert AVERAGED_FAMILY_SCORES["bankruptcy"] == pytest.approx(-3.49)
    assert FINANCE_LEXICON["beat"] == FINANCE_LEXICON["beats"]
    assert FINANCE_LEXICON["beat"] == FINANCE_LEXICON["beating"]


def test_expansion_lexicon_uses_all_ten_scores_including_exclusion_votes() -> None:
    assert len(EXPANSION_REVIEW_SCORES) == 10
    for family, mean_score in EXPANSION_AVERAGED_FAMILY_SCORES.items():
        expected = (
            sum(scores[family] for scores in EXPANSION_REVIEW_SCORES.values()) / 10
        )
        assert mean_score == pytest.approx(expected)
    assert EXPANSION_AVERAGED_FAMILY_SCORES["rout"] == pytest.approx(-2.29)
    assert EXPANSION_AVERAGED_FAMILY_SCORES["recall"] == pytest.approx(-1.39)
    assert sum(scores["recall"] == 0 for scores in EXPANSION_REVIEW_SCORES.values()) == 2
    assert FINANCE_LEXICON["rebound"] == FINANCE_LEXICON["rebounding"]
    assert FINANCE_LEXICON["fined"] == FINANCE_LEXICON["fines"]


def test_student_review_excludes_context_dependent_layoff_family() -> None:
    assert {"layoff"} == STUDENT_EXCLUDED_FAMILIES
    assert "layoff" not in STUDENT_APPROVED_FAMILY_SCORES
    assert "layoff" not in FINANCE_LEXICON
    assert "layoffs" not in FINANCE_LEXICON
    assert len(STUDENT_APPROVED_FAMILY_SCORES) == 33
    assert len(FINANCE_LEXICON) == 75


def test_finance_vader_preserves_text_and_corrects_earnings_beat() -> None:
    prices = _equity_prices(["2023-01-03", "2023-01-04"])
    news = prepare_news_coverage(
        pd.DataFrame(
            [
                _headline("2023-01-03", "AAA", "Company BEATS estimates!!!"),
                _headline(
                    "2023-01-03",
                    "BBB",
                    "Analyst downgrades stock to underperform",
                ),
            ]
        ),
        prices,
    )

    scored = score_headlines(news.aligned_headlines).set_index("ticker")

    assert scored.loc["AAA", "title"] == "Company BEATS estimates!!!"
    assert scored.loc["AAA", "plain_compound"] == pytest.approx(0.0)
    assert scored.loc["AAA", "finance_compound"] > 0.0
    assert scored.loc["AAA", "finance_label"] == "positive"
    assert scored.loc["BBB", "finance_compound"] < 0.0
    assert scored.loc["BBB", "finance_label"] == "negative"


def test_duplicate_headline_key_is_rejected_before_scoring() -> None:
    prices = _equity_prices(["2023-01-03", "2023-01-04"])
    news = prepare_news_coverage(
        pd.DataFrame([_headline("2023-01-03", "AAA", "Company beats estimates")]),
        prices,
    )
    duplicated = pd.concat(
        [news.aligned_headlines, news.aligned_headlines], ignore_index=True
    )

    with pytest.raises(SentimentValidationError, match="duplicate"):
        score_headlines(duplicated)


def test_no_news_is_neutral_and_sector_index_equal_weights_five_tickers() -> None:
    prices = _equity_prices(["2023-01-03", "2023-01-04"])
    news = prepare_news_coverage(
        pd.DataFrame([_headline("2023-01-03", "AAA", "Company beats estimates")]),
        prices,
    )
    headlines = score_headlines(news.aligned_headlines)
    ticker = aggregate_ticker_day_scores(headlines, news.ticker_day_panel)
    sector = sector_sentiment_index(ticker, news.sector_day_panel).set_index("date")

    first = ticker.loc[ticker["date"].eq("2023-01-03")]
    aaa_score = first.loc[first["ticker"].eq("AAA"), "finance_sentiment"].item()
    assert first.loc[first["ticker"].ne("AAA"), "finance_sentiment"].eq(0.0).all()
    assert sector.loc[pd.Timestamp("2023-01-03"), "finance_sentiment_index"] == pytest.approx(
        aaa_score / 5
    )
    assert sector.loc[pd.Timestamp("2023-01-04"), "finance_sentiment_index"] == 0.0


def test_lag_uses_prior_observed_day_and_future_headline_cannot_change_it() -> None:
    dates = ["2023-01-03", "2023-01-04", "2023-01-05"]
    prices = _equity_prices(dates)
    base_headlines = pd.DataFrame(
        [_headline("2023-01-03", "AAA", "Company beats estimates")]
    )
    future_headlines = pd.concat(
        [
            base_headlines,
            pd.DataFrame(
                [_headline("2023-01-05", "BBB", "Company misses estimates")]
            ),
        ],
        ignore_index=True,
    )

    def build(headlines: pd.DataFrame) -> pd.DataFrame:
        news = prepare_news_coverage(headlines, prices)
        scored = score_headlines(news.aligned_headlines)
        ticker = aggregate_ticker_day_scores(scored, news.ticker_day_panel)
        return sector_sentiment_index(ticker, news.sector_day_panel).set_index("date")

    base = build(base_headlines)
    future = build(future_headlines)
    first_score = base.loc[pd.Timestamp("2023-01-03"), "finance_sentiment_index"]

    assert pd.isna(base.loc[pd.Timestamp("2023-01-03"), "finance_sentiment_index_lag1"])
    assert base.loc[
        pd.Timestamp("2023-01-04"), "finance_sentiment_index_lag1"
    ] == pytest.approx(first_score)
    pd.testing.assert_series_equal(
        base.loc[:"2023-01-04", "finance_sentiment_index_lag1"],
        future.loc[:"2023-01-04", "finance_sentiment_index_lag1"],
    )


def test_market_news_index_is_constituent_weighted_and_standardized() -> None:
    dates = pd.to_datetime(["2023-01-03", "2023-01-04", "2023-01-05"])
    sector = pd.DataFrame(
        [
            {
                "date": date,
                "sector": name,
                "ticker_count": count,
                "covered_tickers": count - 1,
                "headline_count": count + day,
                "plain_sentiment_index": score - 0.01,
                "finance_sentiment_index": score,
            }
            for day, date in enumerate(dates)
            for name, count, score in (
                ("Large", 40, -0.10 + 0.10 * day),
                ("Small", 10, 0.30 + 0.10 * day),
            )
        ]
    )

    market = market_news_index(sector)

    assert market["ticker_count"].eq(50).all()
    assert market["finance_sentiment_index"].tolist() == pytest.approx(
        [-0.02, 0.08, 0.18]
    )
    assert market["finance_fear_greed_index"].tolist() == pytest.approx(
        [49.0, 54.0, 59.0]
    )
    assert market["finance_standardized_score"].mean() == pytest.approx(0)
    assert market["finance_standardized_score"].std(ddof=1) == pytest.approx(1)
    assert market["coverage_breadth"].eq(0.96).all()
    assert market["standardization_basis"].str.contains("descriptive only").all()
