"""Build-only acquisition of external market-reference return series."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd

BENCHMARK_SPECS = {
    "sp500_spy": {
        "benchmark_name": "S&P 500 (SPY total-return proxy)",
        "source_ticker": "SPY",
        "market_reference": "S&P 500",
    },
    "nasdaq_composite_oneq": {
        "benchmark_name": "Nasdaq Composite (ONEQ total-return proxy)",
        "source_ticker": "ONEQ",
        "market_reference": "Nasdaq Composite",
    },
}


class BenchmarkDataError(ValueError):
    """Raised when an external benchmark download is incomplete or malformed."""


def _default_downloader(ticker: str, start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - environment guard
        raise BenchmarkDataError(
            "yfinance is required for the build; install requirements-dev.txt"
        ) from exc
    return yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True,
        actions=False,
        progress=False,
        threads=False,
        multi_level_index=False,
        timeout=30,
    )


def build_external_benchmarks(
    *,
    start: str = "2020-01-01",
    end: str = "2024-01-01",
    downloader: Callable[[str, str, str], pd.DataFrame] | None = None,
    retrieved_on: date | None = None,
) -> pd.DataFrame:
    """Download adjusted SPY/ONEQ closes and return a validated long panel."""
    fetch = downloader or _default_downloader
    retrieved = retrieved_on or date.today()
    frames: list[pd.DataFrame] = []
    for benchmark_id, spec in BENCHMARK_SPECS.items():
        raw = fetch(str(spec["source_ticker"]), start, end)
        if raw.empty or "Close" not in raw:
            raise BenchmarkDataError(
                f"{spec['source_ticker']} did not return an adjusted Close series"
            )
        close = pd.to_numeric(raw["Close"], errors="coerce")
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(raw.index, errors="coerce"),
                "adjusted_close": close.to_numpy(),
            }
        ).dropna()
        frame = frame.sort_values("date").drop_duplicates("date", keep="last")
        frame["daily_return"] = frame["adjusted_close"].pct_change()
        frame = frame.dropna(subset=["daily_return"]).reset_index(drop=True)
        if len(frame) < 700 or not frame["adjusted_close"].gt(0).all():
            raise BenchmarkDataError(
                f"{spec['source_ticker']} benchmark history is incomplete"
            )
        frame["growth_of_1"] = (1 + frame["daily_return"]).cumprod()
        frame.insert(1, "benchmark_id", benchmark_id)
        frame.insert(2, "benchmark_name", spec["benchmark_name"])
        frame.insert(3, "market_reference", spec["market_reference"])
        frame.insert(4, "source_ticker", spec["source_ticker"])
        frame["source"] = "Yahoo Finance via yfinance"
        frame["return_basis"] = (
            "Adjusted close; dividends, capital distributions and splits included"
        )
        frame["retrieved_on"] = retrieved.isoformat()
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    if result.duplicated(["benchmark_id", "date"]).any():
        raise BenchmarkDataError("External benchmark panel contains duplicate dates")
    return result


def save_external_benchmarks(frame: pd.DataFrame, output_path: Path) -> Path:
    """Persist the deployment-safe derived benchmark artifact."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return output_path.resolve()


__all__ = [
    "BENCHMARK_SPECS",
    "BenchmarkDataError",
    "build_external_benchmarks",
    "save_external_benchmarks",
]
