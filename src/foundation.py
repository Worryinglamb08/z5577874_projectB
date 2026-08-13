"""Deterministic Phase 1 orchestration and Project A reconciliation evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from src.etl import CleanData, load_clean_data, save_etl_tables
from src.features import ReturnFeatures, prepare_return_features, save_return_evidence
from src.news_features import (
    NewsCoverageFeatures,
    prepare_news_coverage,
    save_news_coverage_evidence,
)

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
TABLES_DIR: Final = PROJECT_ROOT / "results" / "tables"
DATA_DIR: Final = PROJECT_ROOT / "results" / "data"

# Frozen reconciliation targets from the student's final Project A audit.
PROJECT_A_TARGETS: Final = {
    "clean_equity_rows": 50_300,
    "clean_crypto_rows": 14_610,
    "clean_news_rows": 146_836,
    "crypto_rows_removed": 10,
    "news_exact_duplicates_removed": 2_847,
    "publisher_missing": 137_447,
    "equity_valid_returns": 50_250,
    "crypto_valid_returns": 14_600,
    "combined_equity_dates": 1_006,
    "ticker_day_rows": 50_300,
    "sector_day_rows": 10_060,
    "aligned_same_day": 134_279,
    "aligned_next_day": 12_551,
    "aligned_after_last": 6,
    "aligned_headlines_in_panels": 146_830,
    "nvda_2020_01_03_return": -0.01600591028787468,
    "btc_2020_01_02_return": -0.029819292162590716,
}


class FoundationValidationError(ValueError):
    """Raised when the local Project B foundation fails reconciliation."""


@dataclass(frozen=True)
class FoundationResult:
    """All reusable foundation frames and their reconciliation table."""

    clean: CleanData
    returns: ReturnFeatures
    news: NewsCoverageFeatures
    input_catalog: pd.DataFrame
    reconciliation: pd.DataFrame


def _alignment_count(news: NewsCoverageFeatures, status: str) -> int:
    match = news.headline_alignment_summary.loc[
        news.headline_alignment_summary["alignment_status"].eq(status),
        "headline_count",
    ]
    return int(match.item())


def _observed_values(
    clean: CleanData, returns: ReturnFeatures, news: NewsCoverageFeatures
) -> dict[str, int | float]:
    inventory = clean.dataset_inventory.set_index("dataset")
    hand_checks = returns.return_hand_checks.set_index("ticker")
    return {
        "clean_equity_rows": len(clean.equities),
        "clean_crypto_rows": len(clean.crypto),
        "clean_news_rows": len(clean.news),
        "crypto_rows_removed": int(inventory.loc["crypto_prices", "rows_removed"]),
        "news_exact_duplicates_removed": int(
            inventory.loc["news_headlines", "rows_removed"]
        ),
        "publisher_missing": int(clean.news["publisher"].isna().sum()),
        "equity_valid_returns": int(returns.equity_returns["simple_return"].notna().sum()),
        "crypto_valid_returns": int(
            returns.crypto_returns_native["simple_return"].notna().sum()
        ),
        "combined_equity_dates": len(returns.combined_returns),
        "ticker_day_rows": len(news.ticker_day_panel),
        "sector_day_rows": len(news.sector_day_panel),
        "aligned_same_day": _alignment_count(news, "same_trading_day"),
        "aligned_next_day": _alignment_count(news, "next_trading_day"),
        "aligned_after_last": _alignment_count(
            news, "after_last_equity_date_unaligned"
        ),
        "aligned_headlines_in_panels": int(news.ticker_day_panel["headline_count"].sum()),
        "nvda_2020_01_03_return": float(
            hand_checks.loc["NVDA", "function_return"]
        ),
        "btc_2020_01_02_return": float(
            hand_checks.loc["BTC-USD", "function_return"]
        ),
    }


def build_reconciliation_table(
    clean: CleanData, returns: ReturnFeatures, news: NewsCoverageFeatures
) -> pd.DataFrame:
    """Compare Project B results to frozen values from the final Project A audit."""
    observed = _observed_values(clean, returns, news)
    records: list[dict[str, object]] = []
    for check, expected in PROJECT_A_TARGETS.items():
        actual = observed[check]
        passed = (
            bool(np.isclose(actual, expected, atol=1e-12, rtol=0))
            if isinstance(expected, float)
            else actual == expected
        )
        records.append(
            {
                "check": check,
                "project_a_expected": expected,
                "project_b_observed": actual,
                "difference": actual - expected,
                "status": "pass" if passed else "fail",
                "evidence_basis": "frozen target from student's final Project A outputs",
            }
        )
    return pd.DataFrame.from_records(records)


def _frame_date_span(frame: pd.DataFrame, date_column: str) -> tuple[str, str]:
    dates = frame[date_column].dropna()
    return dates.min().date().isoformat(), dates.max().date().isoformat()


def build_input_catalog(
    returns: ReturnFeatures, news: NewsCoverageFeatures
) -> pd.DataFrame:
    """Document every full in-memory model input and its timing convention."""
    specs = (
        (
            "equity_returns",
            returns.equity_returns,
            "date",
            "ticker,date",
            "observed equity trading days",
            "Adjusted-close return calculated within equity ticker.",
            "Phase 2 equity and combined fund estimation",
        ),
        (
            "crypto_returns_native",
            returns.crypto_returns_native,
            "date",
            "ticker,date",
            "native seven-day calendar",
            "Adjusted-close return calculated within crypto ticker.",
            "Phase 2 crypto fund and combined-sleeve estimation",
        ),
        (
            "combined_returns",
            returns.combined_returns,
            "date",
            "date",
            "observed equity trading days",
            "Native returns pivoted wide; crypto left-aligned without filling.",
            "Phase 2 combined fund estimation",
        ),
        (
            "aligned_headlines",
            news.aligned_headlines,
            "headline_date",
            "headline event row",
            "same or next observed equity date; post-sample rows unaligned",
            "Original date/text retained; no sentiment score assigned.",
            "Phase 4 sentiment scoring audit",
        ),
        (
            "ticker_day_news_panel",
            news.ticker_day_panel,
            "date",
            "date,ticker",
            "observed equity trading days",
            "Complete date-ticker grid with explicit zero-news rows.",
            "Phase 4 ticker-first sentiment aggregation",
        ),
        (
            "sector_day_coverage_panel",
            news.sector_day_panel,
            "date",
            "date,sector",
            "observed equity trading days",
            "Ticker-day counts aggregated to breadth, HHI, and confidence.",
            "Phase 5 coverage-aware signal construction",
        ),
    )
    records: list[dict[str, object]] = []
    for name, frame, date_column, key, calendar, transformation, purpose in specs:
        date_start, date_end = _frame_date_span(frame, date_column)
        records.append(
            {
                "dataset": name,
                "unit_key": key,
                "row_count": len(frame),
                "column_count": len(frame.columns),
                "date_start": date_start,
                "date_end": date_end,
                "calendar_or_alignment": calendar,
                "source": "Project B src/data_access.py via validated local transforms",
                "transformation": transformation,
                "intended_purpose": purpose,
            }
        )
    return pd.DataFrame.from_records(records)


def prepare_foundation(clean: CleanData) -> FoundationResult:
    """Create returns, coverage panels, and reconciliation from cleaned inputs."""
    returns = prepare_return_features(clean.equities, clean.crypto)
    news = prepare_news_coverage(clean.news, clean.equities)
    reconciliation = build_reconciliation_table(clean, returns, news)
    return FoundationResult(
        clean=clean,
        returns=returns,
        news=news,
        input_catalog=build_input_catalog(returns, news),
        reconciliation=reconciliation,
    )


def run_foundation(*, require_reconciliation: bool = True) -> FoundationResult:
    """Load, build, and optionally require exact Project A reconciliation."""
    result = prepare_foundation(load_clean_data())
    failures = result.reconciliation.loc[result.reconciliation["status"].eq("fail")]
    if require_reconciliation and not failures.empty:
        checks = ", ".join(failures["check"])
        raise FoundationValidationError(f"Project A reconciliation failed: {checks}")
    return result


def save_foundation_outputs(result: FoundationResult) -> list[Path]:
    """Write all Phase 1 audit evidence under the Project B results tree."""
    paths = save_etl_tables(result.clean, TABLES_DIR)
    paths.extend(
        save_return_evidence(result.returns, tables_dir=TABLES_DIR, data_dir=DATA_DIR)
    )
    paths.extend(
        save_news_coverage_evidence(
            result.news, tables_dir=TABLES_DIR, data_dir=DATA_DIR
        )
    )
    reconciliation_path = TABLES_DIR / "foundation_reconciliation.csv"
    result.reconciliation.to_csv(reconciliation_path, index=False)
    paths.append(reconciliation_path.resolve())
    catalog_path = TABLES_DIR / "foundation_input_catalog.csv"
    result.input_catalog.to_csv(catalog_path, index=False)
    paths.append(catalog_path.resolve())
    return paths


__all__ = [
    "DATA_DIR",
    "PROJECT_A_TARGETS",
    "PROJECT_ROOT",
    "TABLES_DIR",
    "FoundationResult",
    "FoundationValidationError",
    "build_input_catalog",
    "build_reconciliation_table",
    "prepare_foundation",
    "run_foundation",
    "save_foundation_outputs",
]
