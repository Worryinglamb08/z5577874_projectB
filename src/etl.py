"""Validated local ETL foundation for Stockist Funds Project B.

The transformations deliberately reproduce the student's Project A rules while
remaining independently runnable from this project. Raw frames enter only via
``src.data_access`` and are copied before any transformation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd
from pandas.api.types import is_numeric_dtype

from src import data_access

SAMPLE_END: Final = pd.Timestamp("2023-12-31")
EXTREME_RETURN_THRESHOLD: Final = 0.20
SOURCE_LABEL: Final = "Course-hosted project_data.zip via src/data_access.py"

EQUITY_COLUMNS: Final = (
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjClose",
    "volume",
    "sector",
)
CRYPTO_COLUMNS: Final = EQUITY_COLUMNS[:-1]
NEWS_COLUMNS: Final = ("date", "ticker", "sector", "title", "url", "publisher")
PRICE_COLUMNS: Final = ("open", "high", "low", "close", "adjClose", "volume")

FIELD_DEFINITIONS: Final = {
    "ticker": "Asset ticker supplied by the course dataset.",
    "date": "Timezone-naive observation date at midnight.",
    "open": "Unadjusted opening price in quoted currency.",
    "high": "Unadjusted daily high price in quoted currency.",
    "low": "Unadjusted daily low price in quoted currency.",
    "close": "Unadjusted closing price in quoted currency.",
    "adjClose": "Adjusted closing price used for return calculations.",
    "volume": "Reported daily trading volume; units follow the source dataset.",
    "sector": "Course-provided equity sector classification.",
    "title": "Original headline text, preserved without text cleaning.",
    "url": "Source URL supplied with the headline.",
    "publisher": "Publisher supplied with the headline; blank values are missing.",
}


class DataValidationError(ValueError):
    """Raised when a source frame fails a required integrity rule."""


@dataclass(frozen=True)
class CleanData:
    """Clean inputs and their reproducible audit evidence."""

    equities: pd.DataFrame
    crypto: pd.DataFrame
    news: pd.DataFrame
    dataset_inventory: pd.DataFrame
    data_integrity_summary: pd.DataFrame
    data_schema: pd.DataFrame
    missing_dates_by_ticker: pd.DataFrame
    extreme_returns_screen: pd.DataFrame


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...], dataset: str) -> None:
    if frame.empty:
        raise DataValidationError(f"{dataset} is empty")
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise DataValidationError(f"{dataset} is missing required columns: {missing}")


def _normalise_dates(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Deep-copy a frame and convert dates to timezone-naive midnight values."""
    result = frame.copy(deep=True)
    try:
        parsed = pd.to_datetime(result["date"], errors="raise", utc=True)
    except (TypeError, ValueError) as exc:
        raise DataValidationError(f"{dataset} contains an invalid date") from exc
    if parsed.isna().any():
        raise DataValidationError(f"{dataset} contains a missing date")
    result["date"] = parsed.dt.tz_convert(None).dt.normalize().astype("datetime64[ns]")
    return result


def _validate_numeric_columns(
    frame: pd.DataFrame, columns: tuple[str, ...], dataset: str
) -> None:
    non_numeric = [column for column in columns if not is_numeric_dtype(frame[column])]
    if non_numeric:
        raise DataValidationError(f"{dataset} has non-numeric fields: {non_numeric}")


def _invalid_ohlc_mask(frame: pd.DataFrame) -> pd.Series:
    upper = frame[["open", "close", "low"]].max(axis=1)
    lower = frame[["open", "close", "high"]].min(axis=1)
    return frame["high"].lt(upper) | frame["low"].gt(lower)


def _validate_price_values(frame: pd.DataFrame, dataset: str) -> None:
    if frame[["ticker", "date", "adjClose"]].isna().any().any():
        raise DataValidationError(f"{dataset} has missing ticker, date, or adjClose values")
    if frame["adjClose"].le(0).any():
        raise DataValidationError(f"{dataset} has nonpositive adjusted prices")
    if frame["volume"].lt(0).any():
        raise DataValidationError(f"{dataset} has negative volume")
    invalid_ohlc = _invalid_ohlc_mask(frame)
    if invalid_ohlc.any():
        raise DataValidationError(
            f"{dataset} has {int(invalid_ohlc.sum())} rows with invalid OHLC ordering"
        )


def _validate_universe(
    frame: pd.DataFrame,
    dataset: str,
    expected_tickers: int | None,
    expected_sectors: int | None = None,
) -> None:
    ticker_count = int(frame["ticker"].nunique())
    if expected_tickers is not None and ticker_count != expected_tickers:
        raise DataValidationError(
            f"{dataset} has {ticker_count} tickers; expected {expected_tickers}"
        )
    if expected_sectors is not None:
        sector_count = int(frame["sector"].nunique())
        if sector_count != expected_sectors:
            raise DataValidationError(
                f"{dataset} has {sector_count} sectors; expected {expected_sectors}"
            )


def _clean_prices(
    raw: pd.DataFrame,
    *,
    dataset: str,
    required_columns: tuple[str, ...],
    expected_tickers: int | None,
    expected_sectors: int | None = None,
) -> pd.DataFrame:
    _require_columns(raw, required_columns, dataset)
    clean = _normalise_dates(raw, dataset)
    _validate_numeric_columns(clean, PRICE_COLUMNS, dataset)
    clean = clean.loc[clean["date"].le(SAMPLE_END)].copy()
    if clean.empty:
        raise DataValidationError(f"{dataset} has no observations inside the required sample")
    duplicate_rows = int(clean.duplicated(["ticker", "date"], keep="first").sum())
    if duplicate_rows:
        raise DataValidationError(f"{dataset} has {duplicate_rows} duplicate ticker-date rows")
    _validate_price_values(clean, dataset)
    _validate_universe(clean, dataset, expected_tickers, expected_sectors)
    return clean.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)


def clean_equity_prices(
    raw: pd.DataFrame, *, validate_expected_universe: bool = True
) -> pd.DataFrame:
    """Validate equities and enforce the 2020--2023 sample."""
    return _clean_prices(
        raw,
        dataset="equity_prices",
        required_columns=EQUITY_COLUMNS,
        expected_tickers=50 if validate_expected_universe else None,
        expected_sectors=10 if validate_expected_universe else None,
    )


def clean_crypto_prices(
    raw: pd.DataFrame, *, validate_expected_universe: bool = True
) -> pd.DataFrame:
    """Validate crypto and remove observations after 2023-12-31."""
    return _clean_prices(
        raw,
        dataset="crypto_prices",
        required_columns=CRYPTO_COLUMNS,
        expected_tickers=10 if validate_expected_universe else None,
    )


def clean_news_headlines(
    raw: pd.DataFrame, *, validate_expected_universe: bool = True
) -> pd.DataFrame:
    """Preserve headline text and remove exact ticker-date-title duplicates."""
    _require_columns(raw, NEWS_COLUMNS, "news_headlines")
    clean = _normalise_dates(raw, "news_headlines")
    required_values = ["ticker", "date", "sector", "title"]
    if clean[required_values].isna().any().any():
        raise DataValidationError(
            "news_headlines has missing ticker, date, sector, or title values"
        )
    clean = clean.loc[clean["date"].le(SAMPLE_END)].copy()
    blank_publishers = clean["publisher"].astype("string").str.strip().eq("")
    clean.loc[blank_publishers, "publisher"] = pd.NA
    clean = clean.drop_duplicates(["ticker", "date", "title"], keep="first")
    _validate_universe(
        clean,
        "news_headlines",
        50 if validate_expected_universe else None,
        10 if validate_expected_universe else None,
    )
    return clean.sort_values(["date", "ticker", "title"], kind="stable").reset_index(
        drop=True
    )


def load_clean_equities() -> pd.DataFrame:
    """Load equities through the protected helper and return a clean copy."""
    return clean_equity_prices(data_access.load_equity_prices())


def load_clean_crypto() -> pd.DataFrame:
    """Load crypto through the protected helper and return a clean copy."""
    return clean_crypto_prices(data_access.load_crypto_prices())


def load_clean_news() -> pd.DataFrame:
    """Load headlines through the protected helper and return a clean copy."""
    return clean_news_headlines(data_access.load_news_headlines())


def _calendar_audit(equities: pd.DataFrame, crypto: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    equity_dates = pd.DatetimeIndex(equities["date"].drop_duplicates().sort_values())
    crypto_dates = pd.date_range(crypto["date"].min(), crypto["date"].max(), freq="D")
    calendar_specs = (
        (
            "equity_prices",
            equities,
            equity_dates,
            "shared observed equity trading calendar",
        ),
        ("crypto_prices", crypto, crypto_dates, "daily calendar"),
    )
    for dataset, frame, expected_dates, basis in calendar_specs:
        expected_count = len(expected_dates)
        for ticker, group in frame.groupby("ticker", sort=True):
            observed_count = int(group["date"].nunique())
            records.append(
                {
                    "dataset": dataset,
                    "ticker": ticker,
                    "calendar_basis": basis,
                    "expected_dates": expected_count,
                    "observed_dates": observed_count,
                    "missing_dates": expected_count - observed_count,
                    "coverage_pct": round(100 * observed_count / expected_count, 4),
                }
            )
    return pd.DataFrame.from_records(records)


def _extreme_return_screen(
    equities: pd.DataFrame, crypto: pd.DataFrame
) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    for dataset, frame in (("equity_prices", equities), ("crypto_prices", crypto)):
        work = frame[["ticker", "date", "adjClose"]].copy()
        work["previous_adjClose"] = work.groupby("ticker", sort=False)["adjClose"].shift()
        work["simple_return"] = work.groupby("ticker", sort=False)["adjClose"].pct_change(
            fill_method=None
        )
        flagged = work.loc[
            work["simple_return"].abs().ge(EXTREME_RETURN_THRESHOLD)
        ].copy()
        flagged.insert(0, "dataset", dataset)
        flagged["absolute_return"] = flagged["simple_return"].abs()
        flagged["threshold"] = EXTREME_RETURN_THRESHOLD
        flagged["treatment"] = "retained; no internal price-rule failure"
        records.append(flagged)
    return pd.concat(records, ignore_index=True).sort_values(
        ["dataset", "absolute_return"], ascending=[True, False], kind="stable"
    ).reset_index(drop=True)


def _coverage_rate(calendar_audit: pd.DataFrame, dataset: str) -> float:
    subset = calendar_audit.loc[calendar_audit["dataset"].eq(dataset)]
    return round(100 * subset["observed_dates"].sum() / subset["expected_dates"].sum(), 4)


def _build_inventory(
    raw_frames: dict[str, pd.DataFrame],
    clean_frames: dict[str, pd.DataFrame],
    calendar_audit: pd.DataFrame,
) -> pd.DataFrame:
    metadata = {
        "equity_prices": (
            "equity trading days",
            "shared observed equity trading calendar by ticker",
            "deep copy; date normalisation; cap at 2023-12-31; validation; stable sort",
        ),
        "crypto_prices": (
            "calendar days",
            "daily calendar by ticker",
            "deep copy; date normalisation; cap at 2023-12-31; validation; stable sort",
        ),
        "news_headlines": (
            "event-driven headlines",
            "ticker and sector universe; no daily-completeness assumption",
            "deep copy; date normalisation; cap; publisher blanks to missing; "
            "deduplicate ticker-date-title; stable sort",
        ),
    }
    records: list[dict[str, object]] = []
    for dataset in ("equity_prices", "crypto_prices", "news_headlines"):
        clean = clean_frames[dataset]
        frequency, coverage_basis, transformations = metadata[dataset]
        records.append(
            {
                "dataset": dataset,
                "source": SOURCE_LABEL,
                "raw_rows": len(raw_frames[dataset]),
                "clean_rows": len(clean),
                "rows_removed": len(raw_frames[dataset]) - len(clean),
                "date_start": clean["date"].min().date().isoformat(),
                "date_end": clean["date"].max().date().isoformat(),
                "frequency": frequency,
                "ticker_count": int(clean["ticker"].nunique()),
                "sector_count": (
                    int(clean["sector"].nunique()) if "sector" in clean.columns else pd.NA
                ),
                "calendar_coverage_pct": (
                    _coverage_rate(calendar_audit, dataset)
                    if dataset != "news_headlines"
                    else pd.NA
                ),
                "coverage_basis": coverage_basis,
                "transformations": transformations,
            }
        )
    return pd.DataFrame.from_records(records)


def _build_schema(clean_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for dataset, frame in clean_frames.items():
        for position, column in enumerate(frame.columns, start=1):
            missing_count = int(frame[column].isna().sum())
            transformation = "source field retained"
            if column == "date":
                transformation = "converted to timezone-naive midnight date"
            elif dataset == "news_headlines" and column == "publisher":
                transformation = "blank strings represented as missing"
            elif dataset == "news_headlines" and column == "title":
                transformation = "original text preserved"
            records.append(
                {
                    "dataset": dataset,
                    "column_position": position,
                    "column": column,
                    "dtype": str(frame[column].dtype),
                    "missing_count": missing_count,
                    "missing_pct": round(100 * missing_count / len(frame), 4),
                    "definition": FIELD_DEFINITIONS[column],
                    "transformation": transformation,
                }
            )
    return pd.DataFrame.from_records(records)


def _integrity_row(
    dataset: str, check: str, value: object, status: str, treatment: str
) -> dict[str, object]:
    return {
        "dataset": dataset,
        "check": check,
        "value": value,
        "status": status,
        "treatment": treatment,
    }


def _build_integrity_summary(
    raw_frames: dict[str, pd.DataFrame],
    clean_frames: dict[str, pd.DataFrame],
    calendar_audit: pd.DataFrame,
    extreme_returns: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    expected_tickers = {"equity_prices": 50, "crypto_prices": 10, "news_headlines": 50}
    expected_sectors = {"equity_prices": 10, "news_headlines": 10}
    for dataset, clean in clean_frames.items():
        ticker_count = int(clean["ticker"].nunique())
        rows.append(
            _integrity_row(
                dataset,
                "ticker_count",
                ticker_count,
                "pass" if ticker_count == expected_tickers[dataset] else "fail",
                f"Required universe: {expected_tickers[dataset]} tickers.",
            )
        )
        if dataset in expected_sectors:
            sector_count = int(clean["sector"].nunique())
            rows.append(
                _integrity_row(
                    dataset,
                    "sector_count",
                    sector_count,
                    "pass" if sector_count == expected_sectors[dataset] else "fail",
                    f"Required universe: {expected_sectors[dataset]} sectors.",
                )
            )
        missing = int(clean.isna().sum().sum())
        rows.extend(
            [
                _integrity_row(
                    dataset,
                    "missing_values_clean",
                    missing,
                    "documented" if missing else "pass",
                    "Retained where allowed and reported by field in data_schema.csv.",
                ),
                _integrity_row(
                    dataset,
                    "timezone_aware_dates_clean",
                    int(clean["date"].dt.tz is not None),
                    "pass" if clean["date"].dt.tz is None else "fail",
                    "Converted to timezone-naive midnight dates before joins.",
                ),
            ]
        )

    for dataset in ("equity_prices", "crypto_prices"):
        raw = _normalise_dates(raw_frames[dataset], dataset)
        clean = clean_frames[dataset]
        duplicate_rows = int(raw.duplicated(["ticker", "date"], keep="first").sum())
        rows.extend(
            [
                _integrity_row(
                    dataset,
                    "duplicate_ticker_date_rows_raw",
                    duplicate_rows,
                    "pass" if duplicate_rows == 0 else "fail",
                    "Price keys must be unique; duplicates stop the pipeline.",
                ),
                _integrity_row(
                    dataset,
                    "nonpositive_adjusted_prices_clean",
                    int(clean["adjClose"].le(0).sum()),
                    "pass",
                    "Nonpositive adjusted prices stop the pipeline.",
                ),
                _integrity_row(
                    dataset,
                    "negative_volume_rows_clean",
                    int(clean["volume"].lt(0).sum()),
                    "pass",
                    "Negative volume stops the pipeline.",
                ),
                _integrity_row(
                    dataset,
                    "invalid_ohlc_rows_clean",
                    int(_invalid_ohlc_mask(clean).sum()),
                    "pass",
                    "Invalid high/low ordering stops the pipeline.",
                ),
            ]
        )
        calendar = calendar_audit.loc[calendar_audit["dataset"].eq(dataset)]
        missing_dates = int(calendar["missing_dates"].sum())
        rows.append(
            _integrity_row(
                dataset,
                "missing_native_calendar_dates",
                missing_dates,
                "pass" if missing_dates == 0 else "review",
                "Retained and detailed in missing_dates_by_ticker.csv.",
            )
        )
        extreme_count = int(extreme_returns["dataset"].eq(dataset).sum())
        rows.append(
            _integrity_row(
                dataset,
                "absolute_returns_at_least_20_pct",
                extreme_count,
                "documented" if extreme_count else "pass",
                "Retained unless an internal validation rule shows a data error.",
            )
        )

    raw_crypto = _normalise_dates(raw_frames["crypto_prices"], "crypto_prices")
    crypto_after_end = int(raw_crypto["date"].gt(SAMPLE_END).sum())
    rows.append(
        _integrity_row(
            "crypto_prices",
            "rows_after_2023_12_31_raw",
            crypto_after_end,
            "resolved" if crypto_after_end else "pass",
            "Removed to enforce the supplied 2020--2023 analysis sample.",
        )
    )
    raw_news = _normalise_dates(raw_frames["news_headlines"], "news_headlines")
    duplicate_headlines = int(
        raw_news.duplicated(["ticker", "date", "title"], keep="first").sum()
    )
    publisher_missing = int(clean_frames["news_headlines"]["publisher"].isna().sum())
    rows.extend(
        [
            _integrity_row(
                "news_headlines",
                "duplicate_ticker_date_title_rows_raw",
                duplicate_headlines,
                "resolved" if duplicate_headlines else "pass",
                "Removed exact key duplicates only; different same-day titles retained.",
            ),
            _integrity_row(
                "news_headlines",
                "publisher_missing_clean",
                publisher_missing,
                "documented" if publisher_missing else "pass",
                "Retained as missing; not interpreted as low publisher diversity.",
            ),
            _integrity_row(
                "news_headlines",
                "daily_calendar_gaps",
                "not_applicable",
                "pass",
                "Headlines are event-driven; no article is required every ticker-day.",
            ),
        ]
    )
    return pd.DataFrame.from_records(rows)


def prepare_clean_data(
    raw_equities: pd.DataFrame,
    raw_crypto: pd.DataFrame,
    raw_news: pd.DataFrame,
    *,
    validate_expected_universe: bool = True,
) -> CleanData:
    """Clean supplied frames and construct local audit evidence."""
    raw_frames = {
        "equity_prices": raw_equities.copy(deep=True),
        "crypto_prices": raw_crypto.copy(deep=True),
        "news_headlines": raw_news.copy(deep=True),
    }
    equities = clean_equity_prices(
        raw_equities, validate_expected_universe=validate_expected_universe
    )
    crypto = clean_crypto_prices(
        raw_crypto, validate_expected_universe=validate_expected_universe
    )
    news = clean_news_headlines(
        raw_news, validate_expected_universe=validate_expected_universe
    )
    clean_frames = {
        "equity_prices": equities,
        "crypto_prices": crypto,
        "news_headlines": news,
    }
    calendar_audit = _calendar_audit(equities, crypto)
    extreme_returns = _extreme_return_screen(equities, crypto)
    return CleanData(
        equities=equities,
        crypto=crypto,
        news=news,
        dataset_inventory=_build_inventory(raw_frames, clean_frames, calendar_audit),
        data_integrity_summary=_build_integrity_summary(
            raw_frames, clean_frames, calendar_audit, extreme_returns
        ),
        data_schema=_build_schema(clean_frames),
        missing_dates_by_ticker=calendar_audit,
        extreme_returns_screen=extreme_returns,
    )


def load_clean_data() -> CleanData:
    """Load all three raw inputs through ``data_access`` and clean them."""
    return prepare_clean_data(
        data_access.load_equity_prices(),
        data_access.load_crypto_prices(),
        data_access.load_news_headlines(),
    )


def save_etl_tables(result: CleanData, output_dir: Path) -> list[Path]:
    """Save audit tables without persisting the protected raw or clean frames."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "dataset_inventory.csv": result.dataset_inventory,
        "data_integrity_summary.csv": result.data_integrity_summary,
        "data_schema.csv": result.data_schema,
        "missing_dates_by_ticker.csv": result.missing_dates_by_ticker,
        "extreme_returns_screen.csv": result.extreme_returns_screen,
    }
    paths: list[Path] = []
    for filename, frame in outputs.items():
        path = output_dir / filename
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


__all__ = [
    "CRYPTO_COLUMNS",
    "EQUITY_COLUMNS",
    "EXTREME_RETURN_THRESHOLD",
    "NEWS_COLUMNS",
    "SAMPLE_END",
    "CleanData",
    "DataValidationError",
    "clean_crypto_prices",
    "clean_equity_prices",
    "clean_news_headlines",
    "load_clean_crypto",
    "load_clean_data",
    "load_clean_equities",
    "load_clean_news",
    "prepare_clean_data",
    "save_etl_tables",
]
