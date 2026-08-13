"""ETL integrity tests for the independently runnable Project B foundation."""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.etl import (  # noqa: E402
    DataValidationError,
    clean_crypto_prices,
    clean_equity_prices,
    clean_news_headlines,
    prepare_clean_data,
)


def _prices(*, crypto: bool = False) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "ticker": "AAA-USD" if crypto else "AAA",
                "date": "2023-12-30",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 104.0,
                "adjClose": 100.0,
                "volume": 1_000.0,
                "sector": "Tech",
            },
            {
                "ticker": "AAA-USD" if crypto else "AAA",
                "date": "2023-12-31",
                "open": 104.0,
                "high": 131.0,
                "low": 103.0,
                "close": 130.0,
                "adjClose": 125.0,
                "volume": 1_200.0,
                "sector": "Tech",
            },
        ]
    )
    return frame.drop(columns="sector") if crypto else frame


def _news() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2023-12-30 14:00", tz="UTC"),
                "ticker": "AAA",
                "sector": "Tech",
                "title": "Original headline",
                "url": "https://example.test/1",
                "publisher": "",
            },
            {
                "date": pd.Timestamp("2023-12-30 14:00", tz="UTC"),
                "ticker": "AAA",
                "sector": "Tech",
                "title": "Original headline",
                "url": "https://example.test/duplicate",
                "publisher": "Wire",
            },
            {
                "date": pd.Timestamp("2023-12-30 14:00", tz="UTC"),
                "ticker": "AAA",
                "sector": "Tech",
                "title": "Different same-day headline",
                "url": "https://example.test/2",
                "publisher": "Wire",
            },
        ]
    )


def test_cleaners_copy_sources_normalise_dates_and_cap_sample() -> None:
    raw = pd.concat(
        [_prices(crypto=True), _prices(crypto=True).assign(date="2024-01-01")],
        ignore_index=True,
    )
    original = raw.copy(deep=True)

    clean = clean_crypto_prices(raw, validate_expected_universe=False)

    assert_frame_equal(raw, original)
    assert clean["date"].dtype == "datetime64[ns]"
    assert clean["date"].dt.tz is None
    assert clean["date"].max() == pd.Timestamp("2023-12-31")


def test_duplicate_price_key_stops_the_pipeline() -> None:
    raw = pd.concat([_prices(), _prices().iloc[[0]]], ignore_index=True)

    with pytest.raises(DataValidationError, match="duplicate ticker-date"):
        clean_equity_prices(raw, validate_expected_universe=False)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("high", 98.0, "invalid OHLC"),
        ("adjClose", 0.0, "nonpositive adjusted prices"),
        ("volume", -1.0, "negative volume"),
    ],
)
def test_invalid_price_values_stop_the_pipeline(
    column: str, value: float, message: str
) -> None:
    raw = _prices()
    raw.loc[0, column] = value

    with pytest.raises(DataValidationError, match=message):
        clean_equity_prices(raw, validate_expected_universe=False)


def test_news_deduplication_preserves_distinct_text_and_source_frame() -> None:
    raw = _news()
    original = raw.copy(deep=True)

    clean = clean_news_headlines(raw, validate_expected_universe=False)

    assert_frame_equal(raw, original)
    assert clean["title"].tolist() == ["Different same-day headline", "Original headline"]
    assert pd.isna(clean.loc[clean["title"].eq("Original headline"), "publisher"]).all()


def test_audit_outputs_document_provenance_calendar_and_extremes() -> None:
    equities = pd.concat(
        [_prices(), _prices().assign(ticker="BBB").iloc[[0]]], ignore_index=True
    )
    result = prepare_clean_data(
        equities,
        _prices(crypto=True),
        _news(),
        validate_expected_universe=False,
    )

    assert result.dataset_inventory["dataset"].tolist() == [
        "equity_prices",
        "crypto_prices",
        "news_headlines",
    ]
    assert result.dataset_inventory["source"].str.contains("data_access.py").all()
    missing = result.missing_dates_by_ticker.query(
        "dataset == 'equity_prices' and ticker == 'BBB'"
    )
    assert missing["missing_dates"].item() == 1
    assert result.extreme_returns_screen["simple_return"].tolist() == pytest.approx(
        [0.25, 0.25]
    )
