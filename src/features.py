"""Native-calendar return features and cross-asset calendar alignment.

Adjusted-close returns are calculated within ticker before any alignment. The
combined view then left-aligns already-computed crypto returns to observed
equity trading dates and never fills missing observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

EQUITY_ANNUALIZATION_DAYS: Final = 252
CRYPTO_ANNUALIZATION_DAYS: Final = 365


class FeatureValidationError(ValueError):
    """Raised when clean prices cannot support a return calculation."""


@dataclass(frozen=True)
class ReturnFeatures:
    """Long native returns, an equity-calendar panel, and audit evidence."""

    equity_returns: pd.DataFrame
    crypto_returns_native: pd.DataFrame
    combined_returns: pd.DataFrame
    return_hand_checks: pd.DataFrame
    model_input_schema: pd.DataFrame
    combined_returns_sample: pd.DataFrame


def _validate_prices(prices: pd.DataFrame, price_col: str) -> None:
    required = {"ticker", "date", price_col}
    missing = sorted(required.difference(prices.columns))
    if missing:
        raise FeatureValidationError(f"prices are missing required columns: {missing}")
    if prices.empty:
        raise FeatureValidationError("prices are empty")
    if prices[["ticker", "date", price_col]].isna().any().any():
        raise FeatureValidationError("ticker, date, and adjusted price must be complete")
    if prices.duplicated(["ticker", "date"]).any():
        raise FeatureValidationError("prices must be unique on ticker and date")
    if prices[price_col].le(0).any():
        raise FeatureValidationError("adjusted prices must be positive")


def daily_returns(prices: pd.DataFrame, price_col: str = "adjClose") -> pd.DataFrame:
    """Calculate ``adjClose_t / adjClose_(t-1) - 1`` within each ticker."""
    _validate_prices(prices, price_col)
    result = prices.copy(deep=True).sort_values(
        ["ticker", "date"], kind="stable"
    ).reset_index(drop=True)
    result["simple_return"] = result.groupby("ticker", sort=False)[price_col].pct_change(
        fill_method=None
    )
    return result


def combine_returns_on_equity_calendar(
    equity_returns: pd.DataFrame,
    crypto_returns_native: pd.DataFrame,
) -> pd.DataFrame:
    """Left-align precomputed native returns to the observed equity calendar.

    A Monday crypto value is the native Sunday-to-Monday return. Weekend rows
    remain available in ``crypto_returns_native`` but are not rolled into the
    Monday value. Missing returns remain missing.
    """
    required = {"ticker", "date", "simple_return"}
    for label, frame in (
        ("equity_returns", equity_returns),
        ("crypto_returns_native", crypto_returns_native),
    ):
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise FeatureValidationError(f"{label} is missing required columns: {missing}")
        if frame.duplicated(["ticker", "date"]).any():
            raise FeatureValidationError(f"{label} must be unique on ticker and date")

    equity_wide = equity_returns.pivot(
        index="date", columns="ticker", values="simple_return"
    ).sort_index()
    crypto_wide = crypto_returns_native.pivot(
        index="date", columns="ticker", values="simple_return"
    ).sort_index()
    equity_wide.columns = [f"equity__{ticker}" for ticker in equity_wide.columns]
    crypto_wide.columns = [f"crypto__{ticker}" for ticker in crypto_wide.columns]
    combined = equity_wide.join(crypto_wide, how="left")
    combined.index.name = "date"
    return combined.reset_index()


def _hand_check(
    returns: pd.DataFrame, *, asset_class: str, preferred_ticker: str
) -> dict[str, object]:
    tickers = set(returns["ticker"])
    ticker = preferred_ticker if preferred_ticker in tickers else sorted(tickers)[0]
    sample = returns.loc[returns["ticker"].eq(ticker)].sort_values("date", kind="stable")
    valid = sample.loc[sample["simple_return"].notna()]
    if valid.empty:
        raise FeatureValidationError(f"{asset_class} has no return available for hand check")
    row = valid.iloc[0]
    previous = sample.loc[sample["date"].lt(row["date"])].iloc[-1]
    formula_return = row["adjClose"] / previous["adjClose"] - 1
    difference = formula_return - row["simple_return"]
    return {
        "asset_class": asset_class,
        "ticker": ticker,
        "previous_date": previous["date"].date().isoformat(),
        "date": row["date"].date().isoformat(),
        "previous_adjClose": previous["adjClose"],
        "adjClose": row["adjClose"],
        "formula": "adjClose_t / adjClose_t-1 - 1",
        "hand_calculated_return": formula_return,
        "function_return": row["simple_return"],
        "difference": difference,
        "check_passed": bool(np.isclose(formula_return, row["simple_return"], atol=1e-12)),
    }


def build_return_hand_checks(
    equity_returns: pd.DataFrame, crypto_returns_native: pd.DataFrame
) -> pd.DataFrame:
    """Independently recompute the first NVDA and BTC-USD returns."""
    return pd.DataFrame.from_records(
        [
            _hand_check(
                equity_returns, asset_class="Equity", preferred_ticker="NVDA"
            ),
            _hand_check(
                crypto_returns_native,
                asset_class="Crypto",
                preferred_ticker="BTC-USD",
            ),
        ]
    )


def _model_input_schema(
    equity_returns: pd.DataFrame,
    crypto_returns_native: pd.DataFrame,
    combined_returns: pd.DataFrame,
) -> pd.DataFrame:
    """Describe the full in-memory return inputs without persisting price data."""
    specs = (
        (
            "equity_returns",
            equity_returns,
            "ticker-date",
            "observed equity trading days",
            "Adjusted-close simple returns calculated within equity ticker.",
        ),
        (
            "crypto_returns_native",
            crypto_returns_native,
            "ticker-date",
            "native seven-day calendar",
            "Adjusted-close simple returns calculated within crypto ticker.",
        ),
        (
            "combined_returns",
            combined_returns,
            "date",
            "observed equity trading days",
            "Native returns pivoted wide; crypto left-aligned without filling.",
        ),
    )
    records: list[dict[str, object]] = []
    for name, frame, key, calendar, transformation in specs:
        records.append(
            {
                "dataset": name,
                "unit_of_observation": key,
                "row_count": len(frame),
                "column_count": len(frame.columns),
                "date_start": frame["date"].min().date().isoformat(),
                "date_end": frame["date"].max().date().isoformat(),
                "calendar": calendar,
                "source": "clean Project B frames from src/etl.py",
                "transformation": transformation,
                "purpose": "Phase 2 walk-forward portfolio model input",
            }
        )
    return pd.DataFrame.from_records(records)


def prepare_return_features(
    equities: pd.DataFrame,
    crypto: pd.DataFrame,
    *,
    sample_rows: int = 10,
) -> ReturnFeatures:
    """Build all Phase 1 return inputs and compact validation evidence."""
    if sample_rows <= 0:
        raise FeatureValidationError("sample_rows must be positive")
    equity_returns = daily_returns(equities)
    crypto_returns_native = daily_returns(crypto)
    combined_returns = combine_returns_on_equity_calendar(
        equity_returns, crypto_returns_native
    )
    return ReturnFeatures(
        equity_returns=equity_returns,
        crypto_returns_native=crypto_returns_native,
        combined_returns=combined_returns,
        return_hand_checks=build_return_hand_checks(
            equity_returns, crypto_returns_native
        ),
        model_input_schema=_model_input_schema(
            equity_returns, crypto_returns_native, combined_returns
        ),
        combined_returns_sample=combined_returns.tail(sample_rows).reset_index(drop=True),
    )


def save_return_evidence(
    result: ReturnFeatures, *, tables_dir: Path, data_dir: Path
) -> list[Path]:
    """Save return validation tables and a small combined-panel sample."""
    tables_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        tables_dir / "return_hand_checks.csv": result.return_hand_checks,
        tables_dir / "model_input_schema.csv": result.model_input_schema,
        data_dir / "combined_returns_sample.csv": result.combined_returns_sample,
    }
    paths: list[Path] = []
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


def assemble_headline_panel(headlines: pd.DataFrame) -> pd.DataFrame:
    """Compatibility guard: headline assembly also requires an equity calendar."""
    raise FeatureValidationError(
        "headline assembly requires equity prices; use src.news_features"
    )


__all__ = [
    "CRYPTO_ANNUALIZATION_DAYS",
    "EQUITY_ANNUALIZATION_DAYS",
    "FeatureValidationError",
    "ReturnFeatures",
    "assemble_headline_panel",
    "build_return_hand_checks",
    "combine_returns_on_equity_calendar",
    "daily_returns",
    "prepare_return_features",
    "save_return_evidence",
]
