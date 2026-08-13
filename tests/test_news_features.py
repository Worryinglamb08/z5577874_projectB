"""Headline alignment, no-news, confidence, and leakage tests."""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.news_features import (  # noqa: E402
    align_headlines_to_trading_days,
    build_sector_day_news_panel,
    build_ticker_day_news_panel,
    coverage_confidence,
    prepare_news_coverage,
    trailing_attention_surprise,
)


def _equity_prices() -> pd.DataFrame:
    dates = pd.to_datetime(["2023-01-06", "2023-01-09", "2023-01-10"])
    tickers = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    return pd.DataFrame(
        [
            {"ticker": ticker, "sector": "Tech", "date": date}
            for date in dates
            for ticker in tickers
        ]
    )


def _headlines() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2023-01-06"),
                "ticker": "AAA",
                "sector": "Tech",
                "title": "Revenue growth forecast upgraded",
                "url": "https://example.test/1",
                "publisher": "Wire",
            },
            {
                "date": pd.Timestamp("2023-01-07"),
                "ticker": "BBB",
                "sector": "Tech",
                "title": "Debt risk and dividend guidance",
                "url": "https://example.test/2",
                "publisher": pd.NA,
            },
            {
                "date": pd.Timestamp("2023-01-11"),
                "ticker": "CCC",
                "sector": "Tech",
                "title": "Profit update after final date",
                "url": "https://example.test/3",
                "publisher": "Wire",
            },
        ]
    )


def test_alignment_retains_original_date_and_handles_all_statuses() -> None:
    aligned = align_headlines_to_trading_days(_headlines(), _equity_prices()).set_index(
        "ticker"
    )

    assert aligned.loc["AAA", "headline_date"] == pd.Timestamp("2023-01-06")
    assert aligned.loc["AAA", "alignment_status"] == "same_trading_day"
    assert aligned.loc["BBB", "aligned_trading_date"] == pd.Timestamp("2023-01-09")
    assert aligned.loc["BBB", "alignment_lag_calendar_days"] == 2
    assert aligned.loc["CCC", "alignment_status"] == "after_last_equity_date_unaligned"
    assert pd.isna(aligned.loc["CCC", "aligned_trading_date"])


def test_complete_panels_include_zero_news_and_correct_hhi() -> None:
    aligned = align_headlines_to_trading_days(_headlines(), _equity_prices())
    ticker = build_ticker_day_news_panel(aligned, _equity_prices())
    sector = build_sector_day_news_panel(ticker).set_index("date")

    assert len(ticker) == 15
    assert sector.loc[pd.Timestamp("2023-01-06"), "coverage_breadth"] == pytest.approx(
        0.2
    )
    assert sector.loc[pd.Timestamp("2023-01-06"), "ticker_coverage_hhi"] == 1.0
    assert sector.loc[pd.Timestamp("2023-01-10"), "coverage_confidence"] == 0.0
    assert np.isnan(sector.loc[pd.Timestamp("2023-01-10"), "ticker_coverage_hhi"])


def test_approved_confidence_formula_is_bounded_and_zero_on_no_news() -> None:
    result = coverage_confidence(
        pd.Series([0.0, 0.4, 1.0]),
        pd.Series([np.nan, 0.5, 0.2]),
        pd.Series([False, True, True]),
    )

    assert result.tolist() == pytest.approx([0.0, 0.25, 1.0])


def test_attention_surprise_uses_prior_counts_only() -> None:
    base = pd.Series(list(range(1, 23)), dtype="float64")
    changed_future = base.copy()
    changed_future.iloc[21] = 10_000

    first = trailing_attention_surprise(base, window=20, min_periods=20)
    second = trailing_attention_surprise(changed_future, window=20, min_periods=20)

    assert first.iloc[20] == pytest.approx(second.iloc[20])
    assert first.iloc[20] == pytest.approx(
        (21 - pd.Series(range(1, 21)).mean()) / pd.Series(range(1, 21)).std(ddof=1)
    )


def test_future_headline_cannot_change_earlier_coverage() -> None:
    past_headlines = _headlines().iloc[:2]
    future_headline = _headlines().iloc[[0]].assign(
        date=pd.Timestamp("2023-01-10"),
        ticker="CCC",
        title="New information on a later observed trading day",
    )
    base = prepare_news_coverage(past_headlines, _equity_prices()).sector_day_panel
    future = prepare_news_coverage(
        pd.concat([past_headlines, future_headline], ignore_index=True),
        _equity_prices(),
    ).sector_day_panel
    columns = [
        "date",
        "headline_count",
        "coverage_breadth",
        "ticker_coverage_hhi",
        "coverage_confidence",
    ]

    prior_dates = base["date"].lt("2023-01-10")
    pd.testing.assert_frame_equal(
        base.loc[prior_dates, columns].reset_index(drop=True),
        future.loc[prior_dates, columns].reset_index(drop=True),
    )
    assert future.loc[future["date"].eq("2023-01-10"), "headline_count"].item() == 1
