"""Return and calendar-alignment tests for Project B."""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.features import (  # noqa: E402
    combine_returns_on_equity_calendar,
    daily_returns,
    prepare_return_features,
)


def _prices(ticker: str, dates: list[str], closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"ticker": ticker, "date": pd.to_datetime(dates), "adjClose": closes}
    )


def _equity_crypto() -> tuple[pd.DataFrame, pd.DataFrame]:
    equities = _prices(
        "NVDA", ["2023-01-06", "2023-01-09", "2023-01-10"], [100, 110, 121]
    )
    crypto = _prices(
        "BTC-USD",
        ["2023-01-06", "2023-01-07", "2023-01-08", "2023-01-09", "2023-01-10"],
        [100, 110, 121, 133.1, 146.41],
    )
    return equities, crypto


def test_returns_sort_and_use_adjusted_close_within_ticker() -> None:
    first = _prices("AAA", ["2023-01-03", "2023-01-02"], [110, 100])
    first["close"] = [200, 100]
    second = _prices("BBB", ["2023-01-02", "2023-01-03"], [200, 180])

    result = daily_returns(pd.concat([first, second], ignore_index=True))
    valid = result.dropna(subset=["simple_return"]).set_index("ticker")

    assert valid.loc["AAA", "simple_return"] == pytest.approx(0.10)
    assert valid.loc["BBB", "simple_return"] == pytest.approx(-0.10)


def test_crypto_is_calculated_natively_before_equity_calendar_alignment() -> None:
    equities, crypto = _equity_crypto()
    crypto_returns = daily_returns(crypto)

    combined = combine_returns_on_equity_calendar(
        daily_returns(equities), crypto_returns
    )

    monday = combined.loc[combined["date"].eq("2023-01-09"), "crypto__BTC-USD"].item()
    assert monday == pytest.approx(0.10)
    assert monday != pytest.approx(133.1 / 100 - 1)
    assert crypto_returns["date"].dt.dayofweek.isin([5, 6]).sum() == 2
    assert not combined["date"].dt.dayofweek.isin([5, 6]).any()


def test_calendar_alignment_never_fills_missing_crypto_return() -> None:
    equities, crypto = _equity_crypto()
    crypto = crypto.loc[~crypto["date"].eq("2023-01-09")]

    combined = combine_returns_on_equity_calendar(
        daily_returns(equities), daily_returns(crypto)
    )

    monday = combined.loc[combined["date"].eq("2023-01-09"), "crypto__BTC-USD"].item()
    assert np.isnan(monday)


def test_return_bundle_has_hand_checks_and_traceable_model_schema() -> None:
    equities, crypto = _equity_crypto()

    result = prepare_return_features(equities, crypto, sample_rows=2)

    assert result.return_hand_checks["check_passed"].all()
    assert result.return_hand_checks["difference"].abs().max() < 1e-12
    assert result.model_input_schema["dataset"].tolist() == [
        "equity_returns",
        "crypto_returns_native",
        "combined_returns",
    ]
    crypto_schema = result.model_input_schema.set_index("dataset").loc[
        "crypto_returns_native"
    ]
    assert crypto_schema["calendar"] == "native seven-day calendar"
