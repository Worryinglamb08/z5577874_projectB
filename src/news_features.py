"""Headline trading-day alignment and coverage features for Project B.

This module structures headline text but does not score sentiment. It retains
the original event date, aligns to the same or next observed equity date, and
builds complete ticker-day and sector-day coverage grids including no-news days.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

ATTENTION_WINDOW: Final = 60
ATTENTION_MIN_PERIODS: Final = 20
EQUAL_SECTOR_SHARE: Final = 0.20


class NewsFeatureValidationError(ValueError):
    """Raised when headline inputs cannot support an alignment or coverage feature."""


@dataclass(frozen=True)
class NewsCoverageFeatures:
    """Full in-memory panels and compact Phase 1 evidence."""

    aligned_headlines: pd.DataFrame
    ticker_day_panel: pd.DataFrame
    sector_day_panel: pd.DataFrame
    headline_alignment_summary: pd.DataFrame
    coverage_summary: pd.DataFrame
    headline_panel_sample: pd.DataFrame
    coverage_features_sample: pd.DataFrame


def _require_columns(frame: pd.DataFrame, required: set[str], dataset: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise NewsFeatureValidationError(f"{dataset} is missing required columns: {missing}")
    if frame.empty:
        raise NewsFeatureValidationError(f"{dataset} is empty")


def _equity_calendar(equity_prices: pd.DataFrame) -> pd.DatetimeIndex:
    _require_columns(equity_prices, {"ticker", "date", "sector"}, "equity_prices")
    calendar = pd.DatetimeIndex(
        pd.to_datetime(equity_prices["date"], errors="raise").drop_duplicates()
    ).sort_values()
    if calendar.empty:
        raise NewsFeatureValidationError("equity calendar is empty")
    return calendar


def _ticker_sector_universe(equity_prices: pd.DataFrame) -> pd.DataFrame:
    universe = (
        equity_prices[["ticker", "sector"]]
        .drop_duplicates()
        .sort_values(["sector", "ticker"], kind="stable")
        .reset_index(drop=True)
    )
    if universe.duplicated("ticker", keep=False).any():
        raise NewsFeatureValidationError("an equity ticker maps to multiple sectors")
    return universe


def align_headlines_to_trading_days(
    headlines: pd.DataFrame,
    equity_prices: pd.DataFrame,
) -> pd.DataFrame:
    """Map each headline to the same or next observed equity trading date.

    Rows after the final equity date remain explicitly unaligned. They are not
    mapped backward because that would introduce future information.
    """
    _require_columns(
        headlines,
        {"date", "ticker", "sector", "title", "url", "publisher"},
        "headlines",
    )
    universe = _ticker_sector_universe(equity_prices)
    supplied_pairs = headlines[["ticker", "sector"]].drop_duplicates()
    unmatched = supplied_pairs.merge(
        universe, on=["ticker", "sector"], how="left", indicator=True
    )
    if unmatched["_merge"].ne("both").any():
        raise NewsFeatureValidationError(
            "headline ticker-sector pairs must match the equity universe"
        )

    calendar = _equity_calendar(equity_prices)
    result = headlines.copy(deep=True).rename(columns={"date": "headline_date"})
    result["headline_date"] = pd.to_datetime(
        result["headline_date"], errors="raise"
    ).astype("datetime64[ns]")
    calendar_values = calendar.to_numpy(dtype="datetime64[ns]")
    headline_values = result["headline_date"].to_numpy(dtype="datetime64[ns]")
    positions = np.searchsorted(calendar_values, headline_values, side="left")
    within_calendar = positions < len(calendar_values)
    aligned_values = np.full(
        len(result), np.datetime64("NaT", "ns"), dtype="datetime64[ns]"
    )
    aligned_values[within_calendar] = calendar_values[positions[within_calendar]]
    result["aligned_trading_date"] = pd.to_datetime(aligned_values)
    same_day = result["aligned_trading_date"].eq(result["headline_date"])
    result["alignment_status"] = np.select(
        [~within_calendar, same_day],
        ["after_last_equity_date_unaligned", "same_trading_day"],
        default="next_trading_day",
    )
    result["alignment_lag_calendar_days"] = (
        result["aligned_trading_date"] - result["headline_date"]
    ).dt.days.astype("Int64")
    return result.sort_values(
        ["headline_date", "ticker", "title"], kind="stable"
    ).reset_index(drop=True)


def trailing_attention_surprise(
    counts: pd.Series,
    *,
    window: int = ATTENTION_WINDOW,
    min_periods: int = ATTENTION_MIN_PERIODS,
) -> pd.Series:
    """Standardise today's count against prior observations only."""
    if window < 2 or min_periods < 2 or min_periods > window:
        raise NewsFeatureValidationError("attention window settings are invalid")
    history = counts.shift(1)
    trailing_mean = history.rolling(window=window, min_periods=min_periods).mean()
    trailing_std = history.rolling(window=window, min_periods=min_periods).std(ddof=1)
    surprise = (counts - trailing_mean) / trailing_std
    return surprise.mask(trailing_std.eq(0))


def build_ticker_day_news_panel(
    aligned_headlines: pd.DataFrame,
    equity_prices: pd.DataFrame,
) -> pd.DataFrame:
    """Build a complete equity-date by ticker panel including zero-news days."""
    required = {
        "aligned_trading_date",
        "ticker",
        "sector",
        "title",
    }
    _require_columns(aligned_headlines, required, "aligned_headlines")
    calendar = _equity_calendar(equity_prices)
    universe = _ticker_sector_universe(equity_prices)
    grid = pd.MultiIndex.from_product(
        [calendar, universe["ticker"]], names=["date", "ticker"]
    ).to_frame(index=False)
    grid = grid.merge(universe, on="ticker", how="left", validate="many_to_one")
    valid = aligned_headlines.loc[aligned_headlines["aligned_trading_date"].notna()]
    aggregated = (
        valid.groupby(["aligned_trading_date", "ticker"], sort=True)
        .agg(
            headline_count=("title", "size"),
            headline_text=("title", lambda values: " || ".join(values)),
        )
        .reset_index()
        .rename(columns={"aligned_trading_date": "date"})
    )
    panel = grid.merge(
        aggregated, on=["date", "ticker"], how="left", validate="one_to_one"
    )
    panel["headline_count"] = panel["headline_count"].fillna(0).astype("int64")
    panel["headline_text"] = panel["headline_text"].fillna("")
    panel["has_news"] = panel["headline_count"].gt(0)
    panel = panel.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)
    panel["attention_surprise_60d"] = panel.groupby(
        "ticker", sort=False
    )["headline_count"].transform(trailing_attention_surprise)
    return panel.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)


def _hhi(counts: pd.Series) -> float:
    total = counts.sum()
    if total <= 0:
        return float("nan")
    shares = counts / total
    return float((shares**2).sum())


def coverage_confidence(
    breadth: pd.Series,
    hhi: pd.Series,
    has_news: pd.Series,
) -> pd.Series:
    """Apply the approved breadth/concentration confidence equation.

    ``confidence = breadth * (1 - HHI) / (1 - 0.20)``. Values are clipped
    to ``[0, 1]`` and no-news observations are exactly zero.
    """
    confidence = breadth * (1 - hhi) / (1 - EQUAL_SECTOR_SHARE)
    return confidence.clip(lower=0.0, upper=1.0).where(has_news, 0.0).fillna(0.0)


def build_sector_day_news_panel(ticker_day_panel: pd.DataFrame) -> pd.DataFrame:
    """Aggregate coverage to sector-day with a fixed constituent denominator."""
    required = {"date", "ticker", "sector", "headline_count", "has_news"}
    _require_columns(ticker_day_panel, required, "ticker_day_panel")
    grouped = ticker_day_panel.groupby(["date", "sector"], sort=True)
    panel = grouped.agg(
        headline_count=("headline_count", "sum"),
        covered_tickers=("has_news", "sum"),
        constituent_count=("ticker", "nunique"),
    ).reset_index()
    concentration = (
        grouped["headline_count"].apply(_hhi).rename("ticker_coverage_hhi").reset_index()
    )
    panel = panel.merge(concentration, on=["date", "sector"], validate="one_to_one")
    panel["coverage_breadth"] = panel["covered_tickers"] / panel["constituent_count"]
    panel["has_news"] = panel["headline_count"].gt(0)
    panel["coverage_confidence"] = coverage_confidence(
        panel["coverage_breadth"], panel["ticker_coverage_hhi"], panel["has_news"]
    )
    panel = panel.sort_values(["sector", "date"], kind="stable").reset_index(drop=True)
    panel["attention_surprise_60d"] = panel.groupby(
        "sector", sort=False
    )["headline_count"].transform(trailing_attention_surprise)
    return panel.sort_values(["date", "sector"], kind="stable").reset_index(drop=True)


def _alignment_summary(aligned_headlines: pd.DataFrame) -> pd.DataFrame:
    total = len(aligned_headlines)
    counts = aligned_headlines["alignment_status"].value_counts()
    treatments = {
        "same_trading_day": "included on original date",
        "next_trading_day": "included on next observed equity trading date",
        "after_last_equity_date_unaligned": (
            "excluded from trading-day features; retained in alignment audit"
        ),
    }
    return pd.DataFrame(
        [
            {
                "alignment_status": status,
                "headline_count": int(counts.get(status, 0)),
                "headline_share_pct": 100 * counts.get(status, 0) / total,
                "treatment": treatment,
            }
            for status, treatment in treatments.items()
        ]
    )


def _coverage_summary(
    ticker_day_panel: pd.DataFrame, sector_day_panel: pd.DataFrame
) -> pd.DataFrame:
    return pd.DataFrame.from_records(
        [
            {
                "panel": "ticker_day",
                "row_count": len(ticker_day_panel),
                "key": "date,ticker",
                "date_count": int(ticker_day_panel["date"].nunique()),
                "entity_count": int(ticker_day_panel["ticker"].nunique()),
                "headline_count": int(ticker_day_panel["headline_count"].sum()),
                "zero_news_rows": int((~ticker_day_panel["has_news"]).sum()),
                "nonzero_confidence_rows": pd.NA,
                "mean_coverage_confidence": pd.NA,
                "purpose": "ticker-first text aggregation and no-news policy",
            },
            {
                "panel": "sector_day",
                "row_count": len(sector_day_panel),
                "key": "date,sector",
                "date_count": int(sector_day_panel["date"].nunique()),
                "entity_count": int(sector_day_panel["sector"].nunique()),
                "headline_count": int(sector_day_panel["headline_count"].sum()),
                "zero_news_rows": int((~sector_day_panel["has_news"]).sum()),
                "nonzero_confidence_rows": int(
                    sector_day_panel["coverage_confidence"].gt(0).sum()
                ),
                "mean_coverage_confidence": float(
                    sector_day_panel["coverage_confidence"].mean()
                ),
                "purpose": "coverage confidence and later sector sentiment index",
            },
        ]
    )


def _headline_sample(
    aligned_headlines: pd.DataFrame, rows_per_status: int = 5
) -> pd.DataFrame:
    columns = [
        "headline_date",
        "aligned_trading_date",
        "alignment_status",
        "alignment_lag_calendar_days",
        "ticker",
        "sector",
        "title",
        "publisher",
        "url",
    ]
    return (
        aligned_headlines.sort_values(
            ["alignment_status", "headline_date", "ticker", "title"], kind="stable"
        )
        .groupby("alignment_status", sort=True, group_keys=False)
        .head(rows_per_status)[columns]
        .reset_index(drop=True)
    )


def prepare_news_coverage(
    headlines: pd.DataFrame,
    equity_prices: pd.DataFrame,
    *,
    sample_rows: int = 20,
) -> NewsCoverageFeatures:
    """Build aligned headlines and complete coverage panels."""
    if sample_rows <= 0:
        raise NewsFeatureValidationError("sample_rows must be positive")
    aligned = align_headlines_to_trading_days(headlines, equity_prices)
    ticker_day = build_ticker_day_news_panel(aligned, equity_prices)
    sector_day = build_sector_day_news_panel(ticker_day)
    return NewsCoverageFeatures(
        aligned_headlines=aligned,
        ticker_day_panel=ticker_day,
        sector_day_panel=sector_day,
        headline_alignment_summary=_alignment_summary(aligned),
        coverage_summary=_coverage_summary(ticker_day, sector_day),
        headline_panel_sample=_headline_sample(aligned),
        coverage_features_sample=sector_day.tail(sample_rows).reset_index(drop=True),
    )


def save_news_coverage_evidence(
    result: NewsCoverageFeatures, *, tables_dir: Path, data_dir: Path
) -> list[Path]:
    """Save compact alignment and coverage evidence, not the full text corpus."""
    tables_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        tables_dir / "headline_alignment_summary.csv": result.headline_alignment_summary,
        tables_dir / "coverage_panel_summary.csv": result.coverage_summary,
        data_dir / "headline_panel_sample.csv": result.headline_panel_sample,
        data_dir / "coverage_features_sample.csv": result.coverage_features_sample,
    }
    paths: list[Path] = []
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


__all__ = [
    "ATTENTION_MIN_PERIODS",
    "ATTENTION_WINDOW",
    "EQUAL_SECTOR_SHARE",
    "NewsCoverageFeatures",
    "NewsFeatureValidationError",
    "align_headlines_to_trading_days",
    "build_sector_day_news_panel",
    "build_ticker_day_news_panel",
    "coverage_confidence",
    "prepare_news_coverage",
    "save_news_coverage_evidence",
    "trailing_attention_surprise",
]
