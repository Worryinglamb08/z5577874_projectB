"""Validated, deployment-safe artifact loading for the Stockist Funds app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


class AppArtifactError(ValueError):
    """Raised when a required precomputed app artifact is missing or malformed."""


@dataclass(frozen=True)
class AppArtifacts:
    """All precomputed data required by the six-page investor journey."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    external_benchmarks: pd.DataFrame
    performance: pd.DataFrame
    fact_sheets: pd.DataFrame
    sentiment: pd.DataFrame
    market_sentiment: pd.DataFrame
    fusion_returns: pd.DataFrame
    fusion_comparison: pd.DataFrame
    fusion_weights: pd.DataFrame
    frequency_metrics: pd.DataFrame
    model_configuration: pd.DataFrame
    dataset_inventory: pd.DataFrame
    plain_finance_validation: pd.DataFrame
    coverage_summary: pd.DataFrame
    findings: pd.DataFrame
    phase6_validation: pd.DataFrame
    health: pd.DataFrame


ARTIFACT_SPECS: dict[str, set[str]] = {
    "results/data/fund_returns.csv": {
        "date",
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "net_return",
        "growth_of_1_net",
        "drawdown_net",
    },
    "results/data/fund_weights.csv": {
        "fund_id",
        "rebalance_date",
        "asset",
        "asset_class",
        "pretrade_weight",
        "target_weight",
    },
    "results/data/external_benchmarks.csv": {
        "date",
        "benchmark_id",
        "benchmark_name",
        "market_reference",
        "source_ticker",
        "adjusted_close",
        "daily_return",
        "source",
        "return_basis",
        "retrieved_on",
    },
    "results/tables/performance_metrics.csv": {
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "first_live_date",
        "last_live_date",
        "net_annualized_return",
        "net_annualized_volatility",
        "net_sharpe_ratio",
        "net_maximum_drawdown",
    },
    "results/tables/fund_fact_sheets.csv": {
        "fund_id",
        "latest_rebalance_date",
        "latest_all_nonzero_holdings",
        "benchmark_fund_id",
        "evidence_limit",
    },
    "results/data/sector_sentiment_index.csv": {
        "date",
        "sector",
        "headline_count",
        "covered_tickers",
        "constituent_count",
        "plain_sentiment_index",
        "finance_sentiment_index",
        "ticker_coverage_hhi",
        "coverage_confidence",
        "has_news",
    },
    "results/data/market_news_index.csv": {
        "date",
        "ticker_count",
        "covered_tickers",
        "headline_count",
        "coverage_breadth",
        "plain_sentiment_index",
        "finance_sentiment_index",
        "plain_fear_greed_index",
        "finance_fear_greed_index",
        "plain_standardized_score",
        "finance_standardized_score",
        "standardization_basis",
        "no_news_policy",
    },
    "results/data/fusion_returns.csv": {
        "date",
        "variant",
        "variant_label",
        "growth_of_1_net",
        "drawdown_net",
    },
    "results/tables/fusion_performance_comparison.csv": {
        "variant",
        "variant_label",
        "net_annualized_return",
        "net_annualized_volatility",
        "net_sharpe_ratio",
        "net_maximum_drawdown",
    },
    "results/data/fusion_weights.csv": {"asset", "sector"},
    "results/tables/rebalance_frequency_metrics.csv": {
        "method",
        "schedule_label",
        "schedule_role",
        "net_sharpe_ratio",
        "annualized_turnover",
    },
    "results/tables/model_configuration.csv": {"setting", "value", "configuration_role"},
    "results/tables/dataset_inventory.csv": {
        "dataset",
        "source",
        "clean_rows",
        "date_start",
        "date_end",
    },
    "results/tables/plain_vs_finance_validation.csv": {
        "measure",
        "plain_vader",
        "finance_vader",
        "difference_finance_minus_plain",
    },
    "results/tables/coverage_confidence_summary.csv": {
        "sector",
        "mean_coverage_confidence",
        "no_news_days",
        "thin_evidence_days",
        "broad_evidence_days",
    },
    "results/tables/claim_to_artifact_findings.csv": {
        "claim_id",
        "finding",
        "source_artifact",
        "status",
    },
    "results/tables/phase6_validation_summary.csv": {"check", "status", "detail"},
}


DATE_COLUMNS: dict[str, tuple[str, ...]] = {
    "results/data/fund_returns.csv": ("date",),
    "results/data/fund_weights.csv": (
        "rebalance_date",
        "estimation_start",
        "estimation_end",
        "first_held_return_date",
    ),
    "results/data/external_benchmarks.csv": ("date", "retrieved_on"),
    "results/tables/performance_metrics.csv": ("first_live_date", "last_live_date"),
    "results/tables/fund_fact_sheets.csv": (
        "first_live_date",
        "last_live_date",
        "latest_rebalance_date",
    ),
    "results/data/sector_sentiment_index.csv": ("date",),
    "results/data/market_news_index.csv": ("date",),
    "results/data/fusion_returns.csv": ("date",),
    "results/data/fusion_weights.csv": ("rebalance_date", "signal_source_date"),
    "results/tables/rebalance_frequency_metrics.csv": (
        "first_live_date",
        "last_live_date",
    ),
    "results/tables/dataset_inventory.csv": ("date_start", "date_end"),
}


def _read_artifact(project_root: Path, relative_path: str) -> pd.DataFrame:
    path = project_root / relative_path
    if not path.is_file():
        raise AppArtifactError(
            f"Required app artifact is missing: {relative_path}. "
            "Run python scripts/run_part_b.py and commit the generated results."
        )
    frame = pd.read_csv(path)
    missing = ARTIFACT_SPECS[relative_path].difference(frame.columns)
    if missing:
        raise AppArtifactError(
            f"{relative_path} is missing required columns: {sorted(missing)}"
        )
    if frame.empty:
        raise AppArtifactError(f"Required app artifact is empty: {relative_path}")
    for column in DATE_COLUMNS.get(relative_path, ()):
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], errors="raise")
    return frame


def load_app_artifacts(project_root: Path) -> AppArtifacts:
    """Load and validate only committed, precomputed Project B artifacts."""
    project_root = Path(project_root).resolve()
    frames = {
        path: _read_artifact(project_root, path)
        for path in ARTIFACT_SPECS
    }
    health = pd.DataFrame(
        [
            {
                "artifact": path,
                "rows": len(frame),
                "columns": len(frame.columns),
                "missing_cells": int(frame.isna().sum().sum()),
                "status": "Ready",
            }
            for path, frame in frames.items()
        ]
    )
    result = AppArtifacts(
        fund_returns=frames["results/data/fund_returns.csv"],
        fund_weights=frames["results/data/fund_weights.csv"],
        external_benchmarks=frames["results/data/external_benchmarks.csv"],
        performance=frames["results/tables/performance_metrics.csv"],
        fact_sheets=frames["results/tables/fund_fact_sheets.csv"],
        sentiment=frames["results/data/sector_sentiment_index.csv"],
        market_sentiment=frames["results/data/market_news_index.csv"],
        fusion_returns=frames["results/data/fusion_returns.csv"],
        fusion_comparison=frames[
            "results/tables/fusion_performance_comparison.csv"
        ],
        fusion_weights=frames["results/data/fusion_weights.csv"],
        frequency_metrics=frames[
            "results/tables/rebalance_frequency_metrics.csv"
        ],
        model_configuration=frames["results/tables/model_configuration.csv"],
        dataset_inventory=frames["results/tables/dataset_inventory.csv"],
        plain_finance_validation=frames[
            "results/tables/plain_vs_finance_validation.csv"
        ],
        coverage_summary=frames[
            "results/tables/coverage_confidence_summary.csv"
        ],
        findings=frames["results/tables/claim_to_artifact_findings.csv"],
        phase6_validation=frames[
            "results/tables/phase6_validation_summary.csv"
        ],
        health=health,
    )
    if result.performance["fund_id"].nunique() != 15:
        raise AppArtifactError("The primary app menu must contain exactly 15 funds")
    if set(result.external_benchmarks["benchmark_id"]) != {
        "sp500_spy",
        "nasdaq_composite_oneq",
    }:
        raise AppArtifactError("The external benchmark artifact must contain SPY and ONEQ")
    if not result.phase6_validation["status"].eq("pass").all():
        raise AppArtifactError("Phase 6 evidence validation contains a failed check")
    return result


__all__ = [
    "ARTIFACT_SPECS",
    "AppArtifactError",
    "AppArtifacts",
    "load_app_artifacts",
]
