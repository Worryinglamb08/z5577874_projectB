"""External benchmark acquisition and provenance tests."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
from src.benchmarks import BenchmarkDataError, build_external_benchmarks


def _fixture_download(ticker: str, start: str, end: str) -> pd.DataFrame:
    del start, end
    dates = pd.bdate_range("2020-01-01", periods=760)
    slope = 0.0004 if ticker == "SPY" else 0.0006
    return pd.DataFrame(
        {"Close": 100 * np.cumprod(np.repeat(1 + slope, len(dates)))},
        index=dates,
    )


def test_external_benchmarks_are_adjusted_return_panels_with_provenance() -> None:
    result = build_external_benchmarks(
        downloader=_fixture_download,
        retrieved_on=date(2026, 8, 13),
    )

    assert set(result["benchmark_id"]) == {"sp500_spy", "nasdaq_composite_oneq"}
    assert result.groupby("benchmark_id").size().eq(759).all()
    assert result["daily_return"].gt(0).all()
    assert result["growth_of_1"].gt(0).all()
    assert result["retrieved_on"].eq("2026-08-13").all()
    assert not result.duplicated(["benchmark_id", "date"]).any()


def test_external_benchmark_download_rejects_incomplete_history() -> None:
    def incomplete(ticker: str, start: str, end: str) -> pd.DataFrame:
        del ticker, start, end
        return pd.DataFrame(
            {"Close": [100.0, 101.0]},
            index=pd.bdate_range("2023-01-02", periods=2),
        )

    with pytest.raises(BenchmarkDataError, match="incomplete"):
        build_external_benchmarks(downloader=incomplete)
