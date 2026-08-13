"""Deterministic monthly Project B build and complete artifact contract."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Final

import pandas as pd

from src.app_data import ARTIFACT_SPECS
from src.benchmarks import build_external_benchmarks, save_external_benchmarks
from src.config import DEFAULT_CONFIG
from src.coverage_exhibits import generate_coverage_exhibit
from src.evidence_reconciliation import build_phase6_evidence, save_phase6_evidence
from src.foundation import run_foundation, save_foundation_outputs
from src.fusion import build_fusion_analysis, save_fusion_outputs
from src.fusion_exhibits import generate_fusion_exhibit
from src.portfolio_exhibits import generate_portfolio_exhibits
from src.portfolios import build_portfolio_suite, save_portfolio_outputs
from src.rebalance_experiments import RebalanceExperimentResult
from src.sentiment import prepare_sentiment, save_sentiment_outputs
from src.sentiment_exhibits import generate_sentiment_exhibit

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
MANIFEST_RELATIVE_PATH: Final = "results/tables/artifact_manifest.csv"

DATA_ARTIFACTS: Final = (
    "results/data/combined_returns_sample.csv",
    "results/data/coverage_adjusted_sentiment.csv",
    "results/data/coverage_features_sample.csv",
    "results/data/external_benchmarks.csv",
    "results/data/fund_returns.csv",
    "results/data/fund_weights.csv",
    "results/data/fusion_returns.csv",
    "results/data/fusion_weights.csv",
    "results/data/headline_panel_sample.csv",
    "results/data/market_news_index.csv",
    "results/data/rebalance_frequency_returns.csv",
    "results/data/sector_sentiment_index.csv",
    "results/data/ticker_sentiment_sample.csv",
)
FIGURE_STEMS: Final = (
    "combined_fund_drawdowns",
    "combined_weight_history",
    "coverage_confidence_index",
    "fund_growth",
    "fund_risk_return",
    "fund_sharpe_by_family",
    "fusion_growth_comparison",
    "rebalance_frequency_tradeoff",
    "sector_sentiment_index",
)
FIGURE_ARTIFACTS: Final = tuple(
    path
    for stem in FIGURE_STEMS
    for path in (
        f"results/figures/{stem}.caption.md",
        f"results/figures/{stem}.png",
    )
)
TABLE_ARTIFACTS: Final = (
    "results/tables/claim_to_artifact_findings.csv",
    "results/tables/coverage_confidence_summary.csv",
    "results/tables/coverage_figure_validation.csv",
    "results/tables/coverage_panel_summary.csv",
    "results/tables/data_integrity_summary.csv",
    "results/tables/data_schema.csv",
    "results/tables/dataset_inventory.csv",
    "results/tables/exhibit_catalog.csv",
    "results/tables/extreme_returns_screen.csv",
    "results/tables/fact_sheet_validation.csv",
    "results/tables/finance_lexicon_audit.csv",
    "results/tables/finance_lexicon_expansion_validation_cases.csv",
    "results/tables/finance_lexicon_panel_scores.csv",
    "results/tables/finance_lexicon_panel_summary.csv",
    "results/tables/foundation_input_catalog.csv",
    "results/tables/foundation_reconciliation.csv",
    "results/tables/fund_fact_sheets.csv",
    "results/tables/fusion_figure_validation.csv",
    "results/tables/fusion_performance_comparison.csv",
    "results/tables/fusion_tilt_sensitivity.csv",
    "results/tables/fusion_validation_summary.csv",
    "results/tables/headline_alignment_summary.csv",
    "results/tables/method_distinctness.csv",
    "results/tables/missing_dates_by_ticker.csv",
    "results/tables/model_configuration.csv",
    "results/tables/model_input_schema.csv",
    "results/tables/performance_metrics.csv",
    "results/tables/phase6_validation_summary.csv",
    "results/tables/plain_vs_finance_validation.csv",
    "results/tables/portfolio_figure_validation.csv",
    "results/tables/portfolio_validation_summary.csv",
    "results/tables/rebalance_diagnostics.csv",
    "results/tables/rebalance_frequency_cost_sensitivity.csv",
    "results/tables/rebalance_frequency_decision_support.csv",
    "results/tables/rebalance_frequency_figure_validation.csv",
    "results/tables/rebalance_frequency_metrics.csv",
    "results/tables/rebalance_frequency_rebalances.csv",
    "results/tables/rebalance_frequency_validation.csv",
    "results/tables/report_performance_table.csv",
    "results/tables/return_hand_checks.csv",
    "results/tables/sector_sentiment_summary.csv",
    "results/tables/sentiment_figure_validation.csv",
    "results/tables/sentiment_model_summary.csv",
    "results/tables/sentiment_validation_cases.csv",
    "results/tables/sentiment_validation_summary.csv",
)
CANONICAL_ARTIFACTS: Final = tuple(
    sorted((*DATA_ARTIFACTS, *FIGURE_ARTIFACTS, *TABLE_ARTIFACTS))
)
FROZEN_FREQUENCY_ARTIFACTS: Final = (
    "results/data/rebalance_frequency_returns.csv",
    "results/figures/rebalance_frequency_tradeoff.caption.md",
    "results/figures/rebalance_frequency_tradeoff.png",
    "results/tables/rebalance_frequency_cost_sensitivity.csv",
    "results/tables/rebalance_frequency_decision_support.csv",
    "results/tables/rebalance_frequency_figure_validation.csv",
    "results/tables/rebalance_frequency_metrics.csv",
    "results/tables/rebalance_frequency_rebalances.csv",
    "results/tables/rebalance_frequency_validation.csv",
)
MONTHLY_BUILD_ARTIFACTS: Final = tuple(
    relative
    for relative in CANONICAL_ARTIFACTS
    if relative not in FROZEN_FREQUENCY_ARTIFACTS
)
PASS_STATUS_ARTIFACTS: Final = (
    "results/tables/coverage_figure_validation.csv",
    "results/tables/exhibit_catalog.csv",
    "results/tables/fact_sheet_validation.csv",
    "results/tables/foundation_reconciliation.csv",
    "results/tables/fusion_figure_validation.csv",
    "results/tables/fusion_validation_summary.csv",
    "results/tables/phase6_validation_summary.csv",
    "results/tables/portfolio_figure_validation.csv",
    "results/tables/portfolio_validation_summary.csv",
    "results/tables/rebalance_frequency_figure_validation.csv",
    "results/tables/rebalance_frequency_validation.csv",
    "results/tables/sentiment_figure_validation.csv",
    "results/tables/sentiment_validation_summary.csv",
)
REQUIRED_CAPTION_SECTIONS: Final = ("## Note", "## Sample", "## Units", "## Source")


class PipelineValidationError(ValueError):
    """Raised when generated outputs violate the fixed build contract."""


@dataclass(frozen=True)
class BuildSummary:
    """Compact facts reported by the thin command-line entrypoint."""

    artifact_count: int
    equity_rows: int
    crypto_rows: int
    headline_rows: int
    fund_count: int
    rebalance_count: int
    frequency_path_count: int
    sector_day_rows: int
    fusion_sharpe_change: float
    exhibit_count: int
    fact_sheet_count: int


def _validated_pinned_benchmarks(project_root: Path) -> pd.DataFrame | None:
    """Read the committed external snapshot before managed outputs are replaced."""
    path = project_root / "results/data/external_benchmarks.csv"
    if not path.is_file():
        return None
    frame = pd.read_csv(path)
    required = ARTIFACT_SPECS["results/data/external_benchmarks.csv"]
    if frame.empty or not required.issubset(frame.columns):
        raise PipelineValidationError("Pinned external benchmark snapshot is malformed")
    if set(frame["benchmark_id"]) != {"sp500_spy", "nasdaq_composite_oneq"}:
        raise PipelineValidationError("Pinned benchmark snapshot must contain SPY and ONEQ")
    return frame


def _load_frozen_frequency_evidence(project_root: Path) -> RebalanceExperimentResult:
    """Load the completed faster-schedule experiment without recomputing it."""
    root = Path(project_root).resolve()
    paths = {
        "experiment_returns": "results/data/rebalance_frequency_returns.csv",
        "rebalance_diagnostics": "results/tables/rebalance_frequency_rebalances.csv",
        "frequency_metrics": "results/tables/rebalance_frequency_metrics.csv",
        "cost_sensitivity": "results/tables/rebalance_frequency_cost_sensitivity.csv",
        "decision_support": "results/tables/rebalance_frequency_decision_support.csv",
        "validation_summary": "results/tables/rebalance_frequency_validation.csv",
    }
    missing = [relative for relative in paths.values() if not (root / relative).is_file()]
    if missing:
        raise PipelineValidationError(
            "Frozen frequency evidence is missing; restore the committed diagnostic "
            f"artifacts instead of rerunning them in the monthly build: {missing}"
        )
    frames = {name: pd.read_csv(root / relative) for name, relative in paths.items()}
    if any(frame.empty for frame in frames.values()):
        raise PipelineValidationError("Frozen frequency evidence contains an empty table")
    if not frames["validation_summary"]["status"].eq("pass").all():
        raise PipelineValidationError("Frozen frequency evidence failed validation")
    return RebalanceExperimentResult(**frames)


def clean_managed_outputs(project_root: Path = PROJECT_ROOT) -> list[Path]:
    """Remove monthly-build files while preserving prototypes and frozen diagnostics."""
    root = Path(project_root).resolve()
    removed: list[Path] = []
    for relative in (*MONTHLY_BUILD_ARTIFACTS, MANIFEST_RELATIVE_PATH):
        path = (root / relative).resolve()
        if root not in path.parents:
            raise PipelineValidationError(f"Managed artifact escapes project root: {path}")
        if path.is_file():
            path.unlink()
            removed.append(path)
    return removed


def validate_output_contract(project_root: Path = PROJECT_ROOT) -> None:
    """Require every declared artifact, app schema, caption, and validation pass."""
    root = Path(project_root).resolve()
    missing = [relative for relative in CANONICAL_ARTIFACTS if not (root / relative).is_file()]
    if missing:
        raise PipelineValidationError(f"Canonical build artifacts are missing: {missing}")
    empty = [relative for relative in CANONICAL_ARTIFACTS if (root / relative).stat().st_size == 0]
    if empty:
        raise PipelineValidationError(f"Canonical build artifacts are empty: {empty}")
    for relative, required_columns in ARTIFACT_SPECS.items():
        frame = pd.read_csv(root / relative)
        missing_columns = sorted(required_columns.difference(frame.columns))
        if frame.empty or missing_columns:
            raise PipelineValidationError(
                f"{relative} failed its app schema; missing columns: {missing_columns}"
            )
    for stem in FIGURE_STEMS:
        caption = (root / f"results/figures/{stem}.caption.md").read_text(
            encoding="utf-8"
        )
        missing_sections = [
            section for section in REQUIRED_CAPTION_SECTIONS if section not in caption
        ]
        if missing_sections:
            raise PipelineValidationError(
                f"{stem} caption is missing sections: {missing_sections}"
            )
    for relative in PASS_STATUS_ARTIFACTS:
        frame = pd.read_csv(root / relative)
        if "status" not in frame or frame.empty or not frame["status"].eq("pass").all():
            raise PipelineValidationError(f"Validation evidence failed: {relative}")


def artifact_manifest(project_root: Path = PROJECT_ROOT) -> pd.DataFrame:
    """Return stable content metadata without timestamps or machine-specific paths."""
    root = Path(project_root).resolve()
    validate_output_contract(root)
    records: list[dict[str, object]] = []
    for relative in CANONICAL_ARTIFACTS:
        path = root / relative
        payload = path.read_bytes()
        rows: int | None = None
        columns: int | None = None
        if path.suffix == ".csv":
            frame = pd.read_csv(path)
            rows, columns = frame.shape
        records.append(
            {
                "relative_path": relative,
                "file_type": path.suffix.removeprefix("."),
                "bytes": len(payload),
                "sha256": sha256(payload).hexdigest(),
                "rows": rows,
                "columns": columns,
            }
        )
    return pd.DataFrame.from_records(records)


def write_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    """Write the timestamp-free manifest after the output contract passes."""
    root = Path(project_root).resolve()
    path = root / MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    artifact_manifest(root).to_csv(path, index=False)
    return path.resolve()


def compare_manifests(first: pd.DataFrame, second: pd.DataFrame) -> None:
    """Require exact paths, sizes, dimensions, and hashes across two builds."""
    columns = ["relative_path", "file_type", "bytes", "sha256", "rows", "columns"]
    left = first[columns].sort_values("relative_path").reset_index(drop=True)
    right = second[columns].sort_values("relative_path").reset_index(drop=True)
    if not left.equals(right):
        merged = left.merge(
            right,
            on="relative_path",
            how="outer",
            suffixes=("_first", "_second"),
            indicator=True,
        )
        comparison_columns = [column for column in columns if column != "relative_path"]
        changed_mask = merged["_merge"].ne("both")
        for column in comparison_columns:
            changed_mask |= merged[f"{column}_first"].ne(merged[f"{column}_second"])
        changed = merged.loc[changed_mask]
        raise PipelineValidationError(
            "Build artifacts are not deterministic: "
            f"{changed['relative_path'].astype(str).tolist()}"
        )


def run_full_build(
    project_root: Path = PROJECT_ROOT,
    *,
    refresh_external_benchmarks: bool = False,
) -> BuildSummary:
    """Rebuild monthly/core outputs, then validate and manifest all evidence."""
    root = Path(project_root).resolve()
    data_dir = root / "results/data"
    tables_dir = root / "results/tables"
    figures_dir = root / "results/figures"
    pinned_benchmarks = _validated_pinned_benchmarks(root)
    frequency = _load_frozen_frequency_evidence(root)
    foundation = run_foundation(require_reconciliation=True)
    clean_managed_outputs(root)
    save_foundation_outputs(foundation)
    portfolios = build_portfolio_suite(foundation.returns, DEFAULT_CONFIG)
    save_portfolio_outputs(portfolios, data_dir=data_dir, tables_dir=tables_dir)
    benchmarks = (
        build_external_benchmarks()
        if refresh_external_benchmarks or pinned_benchmarks is None
        else pinned_benchmarks
    )
    save_external_benchmarks(benchmarks, data_dir / "external_benchmarks.csv")
    generate_portfolio_exhibits(
        portfolios,
        figures_dir,
        tables_dir,
        foundation.clean.equities[["ticker", "sector"]].drop_duplicates(),
    )

    sentiment = prepare_sentiment(foundation.news)
    save_sentiment_outputs(sentiment, data_dir=data_dir, tables_dir=tables_dir)
    generate_sentiment_exhibit(
        sentiment,
        output_dir=figures_dir,
        tables_dir=tables_dir,
    )
    ticker_sectors = foundation.clean.equities[["ticker", "sector"]].drop_duplicates()
    fusion = build_fusion_analysis(
        foundation.returns,
        portfolios,
        sentiment,
        ticker_sectors,
        DEFAULT_CONFIG,
    )
    save_fusion_outputs(fusion, data_dir=data_dir, tables_dir=tables_dir)
    generate_fusion_exhibit(fusion, output_dir=figures_dir, tables_dir=tables_dir)
    generate_coverage_exhibit(
        sentiment,
        output_dir=figures_dir,
        tables_dir=tables_dir,
    )
    phase6 = build_phase6_evidence(
        portfolios,
        frequency,
        sentiment,
        fusion,
        project_root=root,
    )
    save_phase6_evidence(phase6, tables_dir=tables_dir)
    validate_output_contract(root)
    write_artifact_manifest(root)

    primary_fusion = fusion.performance_comparison.loc[
        fusion.performance_comparison["variant"].eq("coverage_aware_finance")
    ].iloc[0]
    return BuildSummary(
        artifact_count=len(CANONICAL_ARTIFACTS),
        equity_rows=len(foundation.clean.equities),
        crypto_rows=len(foundation.clean.crypto),
        headline_rows=len(foundation.clean.news),
        fund_count=portfolios.performance_metrics["fund_id"].nunique(),
        rebalance_count=len(portfolios.rebalance_diagnostics),
        frequency_path_count=len(frequency.frequency_metrics),
        sector_day_rows=len(sentiment.sector_index),
        fusion_sharpe_change=float(primary_fusion["delta_net_sharpe_ratio_vs_base"]),
        exhibit_count=len(phase6.exhibit_catalog),
        fact_sheet_count=len(phase6.fact_sheet_validation),
    )


__all__ = [
    "CANONICAL_ARTIFACTS",
    "FROZEN_FREQUENCY_ARTIFACTS",
    "MANIFEST_RELATIVE_PATH",
    "MONTHLY_BUILD_ARTIFACTS",
    "BuildSummary",
    "PipelineValidationError",
    "artifact_manifest",
    "clean_managed_outputs",
    "compare_manifests",
    "run_full_build",
    "validate_output_contract",
    "write_artifact_manifest",
]
