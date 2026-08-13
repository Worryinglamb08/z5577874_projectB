"""Phase 6 report tables, fact-sheet checks, and claim-to-artifact mapping."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.fusion import FusionResult
from src.portfolios import PortfolioSuite
from src.rebalance_experiments import RebalanceExperimentResult
from src.sentiment import SentimentResult


class EvidenceReconciliationError(ValueError):
    """Raised when a displayed result cannot be reconciled to its source."""


@dataclass(frozen=True)
class Phase6Evidence:
    """Compact report tables and machine-readable reconciliation evidence."""

    report_performance_table: pd.DataFrame
    fact_sheet_validation: pd.DataFrame
    plain_vs_finance_validation: pd.DataFrame
    coverage_confidence_summary: pd.DataFrame
    exhibit_catalog: pd.DataFrame
    claim_to_artifact_findings: pd.DataFrame
    validation_summary: pd.DataFrame


def _report_performance_table(suite: PortfolioSuite) -> pd.DataFrame:
    columns = [
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "first_live_date",
        "last_live_date",
        "net_ending_growth_of_1",
        "net_annualized_return",
        "net_annualized_volatility",
        "net_sharpe_ratio",
        "net_maximum_drawdown",
        "average_rebalance_turnover",
        "cumulative_turnover",
        "latest_effective_number_of_assets",
        "annualized_return_vs_benchmark",
    ]
    table = suite.performance_metrics[columns].copy()
    return table.rename(
        columns={
            "net_ending_growth_of_1": "growth_of_1_net",
            "net_annualized_return": "annualized_return_net",
            "net_annualized_volatility": "annualized_volatility_net",
            "net_sharpe_ratio": "sharpe_ratio_net",
            "net_maximum_drawdown": "maximum_drawdown_net",
        }
    ).sort_values(["asset_family", "method"], kind="stable").reset_index(drop=True)


def _fact_sheet_validation(suite: PortfolioSuite) -> pd.DataFrame:
    metrics = suite.performance_metrics.set_index("fund_id")
    weights = suite.fund_weights.copy()
    weights["rebalance_date"] = pd.to_datetime(weights["rebalance_date"])
    required = {
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "first_live_date",
        "last_live_date",
        "latest_rebalance_date",
        "growth_of_1_net",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "maximum_drawdown",
        "average_rebalance_turnover",
        "cumulative_turnover",
        "total_transaction_cost",
        "latest_weight_hhi",
        "latest_effective_number_of_assets",
        "latest_nonzero_holding_count",
        "latest_top_10_holdings",
        "latest_all_nonzero_holdings",
        "benchmark_fund_id",
        "annualized_return_vs_benchmark",
        "evidence_limit",
    }
    missing_columns = sorted(required.difference(suite.fund_fact_sheets.columns))
    if missing_columns:
        raise EvidenceReconciliationError(
            f"fact sheets are missing required columns: {missing_columns}"
        )
    records: list[dict[str, object]] = []
    for row in suite.fund_fact_sheets.itertuples(index=False):
        source = metrics.loc[row.fund_id]
        fund_weights = weights.loc[weights["fund_id"].eq(row.fund_id)]
        latest_date = fund_weights["rebalance_date"].max()
        latest = fund_weights.loc[fund_weights["rebalance_date"].eq(latest_date)]
        latest_hhi = float(np.square(latest["target_weight"]).sum())
        metric_identity = bool(
            np.allclose(
                [
                    row.growth_of_1_net,
                    row.annualized_return,
                    row.annualized_volatility,
                    row.sharpe_ratio,
                    row.maximum_drawdown,
                    row.average_rebalance_turnover,
                    row.cumulative_turnover,
                    row.total_transaction_cost,
                    row.annualized_return_vs_benchmark,
                ],
                [
                    source.net_ending_growth_of_1,
                    source.net_annualized_return,
                    source.net_annualized_volatility,
                    source.net_sharpe_ratio,
                    source.net_maximum_drawdown,
                    source.average_rebalance_turnover,
                    source.cumulative_turnover,
                    source.total_transaction_cost,
                    source.annualized_return_vs_benchmark,
                ],
                atol=1e-12,
                equal_nan=True,
            )
        )
        holdings_identity = bool(
            np.isclose(latest["target_weight"].sum(), 1.0, atol=1e-10)
            and np.isclose(row.latest_weight_hhi, latest_hhi, atol=1e-12)
            and row.latest_nonzero_holding_count
            == int(latest["target_weight"].gt(1e-7).sum())
            and isinstance(row.latest_all_nonzero_holdings, str)
            and bool(row.latest_all_nonzero_holdings.strip())
        )
        dates_identity = pd.Timestamp(row.latest_rebalance_date) == latest_date
        complete = not any(pd.isna(getattr(row, column)) for column in required if column not in {
            "information_ratio"
        })
        passed = bool(metric_identity and holdings_identity and dates_identity and complete)
        records.append(
            {
                "fund_id": row.fund_id,
                "fund_name": row.fund_name,
                "required_fields_complete": complete,
                "metrics_match_performance_table": metric_identity,
                "latest_date_matches_weights": dates_identity,
                "latest_holdings_match_weights": holdings_identity,
                "latest_nonzero_holding_count": row.latest_nonzero_holding_count,
                "latest_weight_sum": float(latest["target_weight"].sum()),
                "status": "pass" if passed else "fail",
            }
        )
    return pd.DataFrame.from_records(records)


def _plain_vs_finance_validation(sentiment: SentimentResult) -> pd.DataFrame:
    model = sentiment.model_summary.set_index("metric")["value"]
    plain_share = float(model.loc["plain_neutral_share"])
    finance_share = float(model.loc["finance_neutral_share"])
    return pd.DataFrame.from_records(
        [
            {
                "measure": "neutral_headline_share",
                "plain_vader": plain_share,
                "finance_vader": finance_share,
                "difference_finance_minus_plain": finance_share - plain_share,
                "unit": "proportion",
                "interpretation_limit": (
                    "Lower neutrality is not automatically higher classification accuracy."
                ),
            },
            {
                "measure": "neutral_headline_count",
                "plain_vader": float(model.loc["plain_neutral_headlines"]),
                "finance_vader": float(model.loc["finance_neutral_headlines"]),
                "difference_finance_minus_plain": float(
                    model.loc["finance_neutral_headlines"]
                    - model.loc["plain_neutral_headlines"]
                ),
                "unit": "headlines",
                "interpretation_limit": "Every changed case remains reviewable.",
            },
            {
                "measure": "compound_scores_changed",
                "plain_vader": 0.0,
                "finance_vader": float(model.loc["finance_score_changed"]),
                "difference_finance_minus_plain": float(
                    model.loc["finance_score_changed"]
                ),
                "unit": "headlines",
                "interpretation_limit": "A score change can improve or worsen a case.",
            },
            {
                "measure": "polarity_labels_changed",
                "plain_vader": 0.0,
                "finance_vader": float(model.loc["sentiment_label_changed"]),
                "difference_finance_minus_plain": float(
                    model.loc["sentiment_label_changed"]
                ),
                "unit": "headlines",
                "interpretation_limit": "Labels use the disclosed +/-0.05 threshold.",
            },
        ]
    )


def _coverage_confidence_summary(sentiment: SentimentResult) -> pd.DataFrame:
    data = sentiment.sector_index.copy()
    return (
        data.groupby("sector", sort=True)
        .agg(
            trading_days=("date", "size"),
            days_with_news=("has_news", "sum"),
            mean_covered_companies=("covered_tickers", "mean"),
            mean_coverage_breadth=("coverage_breadth", "mean"),
            mean_coverage_confidence=("coverage_confidence", "mean"),
            median_coverage_confidence=("coverage_confidence", "median"),
            p10_coverage_confidence=(
                "coverage_confidence",
                lambda values: float(values.quantile(0.10)),
            ),
            p90_coverage_confidence=(
                "coverage_confidence",
                lambda values: float(values.quantile(0.90)),
            ),
            no_news_days=("has_news", lambda values: int((~values).sum())),
            thin_evidence_days=(
                "coverage_confidence",
                lambda values: int(values.lt(0.25).sum()),
            ),
            broad_evidence_days=(
                "coverage_confidence",
                lambda values: int(values.ge(0.75).sum()),
            ),
        )
        .reset_index()
        .assign(
            threshold_note=(
                "<0.25 and >=0.75 are descriptive audit bands, not trading thresholds"
            )
        )
    )


def _exhibit_specs() -> tuple[tuple[str, str, str, str], ...]:
    return (
        (
            "fund_growth",
            "How did the 15 primary monthly funds compound?",
            "results/tables/performance_metrics.csv; results/data/fund_returns.csv",
            "results/tables/portfolio_figure_validation.csv",
        ),
        (
            "combined_fund_drawdowns",
            "When and how deeply did the combined funds lose value?",
            "results/data/fund_returns.csv",
            "results/tables/portfolio_figure_validation.csv",
        ),
        (
            "fund_risk_return",
            "How did return and risk compare across funds and methods?",
            "results/tables/performance_metrics.csv",
            "results/tables/portfolio_figure_validation.csv",
        ),
        (
            "fund_sharpe_by_family",
            "How did out-of-sample Sharpe compare across fund families and methods?",
            "results/tables/performance_metrics.csv",
            "results/tables/portfolio_figure_validation.csv",
        ),
        (
            "combined_weight_history",
            "How did combined-fund sector allocations change over time?",
            "results/data/fund_weights.csv; results/data/fusion_weights.csv",
            "results/tables/portfolio_figure_validation.csv",
        ),
        (
            "sector_sentiment_index",
            "How did finance headline tone vary across equity sectors?",
            "results/data/sector_sentiment_index.csv",
            "results/tables/sentiment_figure_validation.csv",
        ),
        (
            "coverage_confidence_index",
            "When was sector sentiment broadly or weakly supported by news coverage?",
            "results/data/sector_sentiment_index.csv",
            "results/tables/coverage_figure_validation.csv",
        ),
        (
            "rebalance_frequency_tradeoff",
            "Did faster retraining improve Sharpe enough to justify turnover?",
            "results/tables/rebalance_frequency_metrics.csv",
            "results/tables/rebalance_frequency_figure_validation.csv",
        ),
        (
            "fusion_growth_comparison",
            "Did the coverage-aware sentiment tilt improve its base fund?",
            "results/tables/fusion_performance_comparison.csv; results/data/fusion_returns.csv",
            "results/tables/fusion_figure_validation.csv",
        ),
    )


def _exhibit_catalog(project_root: Path) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    required_caption_sections = ("## Note", "## Sample", "## Units", "## Source")
    for stem, question, backing, validation_relative in _exhibit_specs():
        png_relative = f"results/figures/{stem}.png"
        caption_relative = f"results/figures/{stem}.caption.md"
        png = project_root / png_relative
        caption = project_root / caption_relative
        validation_path = project_root / validation_relative
        caption_text = caption.read_text(encoding="utf-8") if caption.exists() else ""
        validation = pd.read_csv(validation_path) if validation_path.exists() else pd.DataFrame()
        validation_passed = bool(
            not validation.empty
            and validation.loc[validation["figure"].eq(stem), "status"].eq("pass").all()
            and validation["figure"].eq(stem).any()
        )
        complete_caption = all(section in caption_text for section in required_caption_sections)
        passed = bool(png.exists() and caption.exists() and complete_caption and validation_passed)
        records.append(
            {
                "figure": stem,
                "investor_question": question,
                "png_artifact": png_relative,
                "caption_artifact": caption_relative,
                "backing_artifacts": backing,
                "validation_artifact": validation_relative,
                "png_exists": png.exists(),
                "caption_context_complete": complete_caption,
                "automated_validation_passed": validation_passed,
                "manual_review_evidence": "ai/PHASE_6_FIGURE_REVIEW.md",
                "status": "pass" if passed else "fail",
            }
        )
    return pd.DataFrame.from_records(records)


def _claim_findings(
    suite: PortfolioSuite,
    frequency: RebalanceExperimentResult,
    sentiment: SentimentResult,
    fusion: FusionResult,
    coverage: pd.DataFrame,
) -> pd.DataFrame:
    metrics = suite.performance_metrics
    combined = metrics.loc[metrics["asset_family"].eq("combined")]
    best_sharpe = combined.loc[combined["net_sharpe_ratio"].idxmax()]
    best_return = combined.loc[combined["net_annualized_return"].idxmax()]
    decision = frequency.decision_support.set_index("method")
    sentiment_model = sentiment.model_summary.set_index("metric")["value"]
    fusion_primary = fusion.performance_comparison.set_index("variant").loc[
        "coverage_aware_finance"
    ]
    lowest_coverage = coverage.loc[coverage["mean_coverage_confidence"].idxmin()]
    highest_coverage = coverage.loc[coverage["mean_coverage_confidence"].idxmax()]
    records = [
        {
            "claim_id": "primary_fund_menu",
            "finding": f"The primary menu contains {metrics['fund_id'].nunique()} monthly funds.",
            "primary_value": metrics["fund_id"].nunique(),
            "comparison_value": np.nan,
            "difference": np.nan,
            "unit": "funds",
            "source_artifact": "results/tables/performance_metrics.csv",
            "source_filter": "all rows",
            "source_field": "fund_id distinct count",
        },
        {
            "claim_id": "combined_best_sharpe",
            "finding": (
                f"{best_sharpe.fund_name} has the highest combined-fund net Sharpe "
                f"({best_sharpe.net_sharpe_ratio:.3f})."
            ),
            "primary_value": best_sharpe.net_sharpe_ratio,
            "comparison_value": np.nan,
            "difference": np.nan,
            "unit": "Sharpe ratio",
            "source_artifact": "results/tables/performance_metrics.csv",
            "source_filter": "asset_family=combined; maximum net_sharpe_ratio",
            "source_field": "net_sharpe_ratio",
        },
        {
            "claim_id": "combined_best_return",
            "finding": (
                f"{best_return.fund_name} has the highest combined-fund net annualised "
                f"return ({best_return.net_annualized_return:.2%})."
            ),
            "primary_value": best_return.net_annualized_return,
            "comparison_value": np.nan,
            "difference": np.nan,
            "unit": "decimal annual return",
            "source_artifact": "results/tables/performance_metrics.csv",
            "source_filter": "asset_family=combined; maximum net_annualized_return",
            "source_field": "net_annualized_return",
        },
        {
            "claim_id": "maximum_sharpe_frequency_tradeoff",
            "finding": (
                "Daily Maximum Sharpe has higher diagnostic Sharpe than monthly but "
                f"{decision.loc['maximum_sharpe', 'daily_to_monthly_turnover_ratio']:.2f}x "
                "the annualised turnover."
            ),
            "primary_value": decision.loc["maximum_sharpe", "best_net_sharpe"],
            "comparison_value": decision.loc["maximum_sharpe", "monthly_net_sharpe"],
            "difference": decision.loc[
                "maximum_sharpe", "daily_to_monthly_turnover_ratio"
            ],
            "unit": "Sharpe ratios; turnover multiple in difference",
            "source_artifact": "results/tables/rebalance_frequency_decision_support.csv",
            "source_filter": "method=maximum_sharpe",
            "source_field": "best_net_sharpe; monthly_net_sharpe; turnover ratio",
        },
        {
            "claim_id": "risk_parity_monthly_frequency",
            "finding": "Monthly has the highest diagnostic net Sharpe for Risk Parity.",
            "primary_value": decision.loc["risk_parity", "monthly_net_sharpe"],
            "comparison_value": decision.loc["risk_parity", "best_net_sharpe"],
            "difference": decision.loc[
                "risk_parity", "monthly_minus_best_net_sharpe"
            ],
            "unit": "Sharpe ratio",
            "source_artifact": "results/tables/rebalance_frequency_decision_support.csv",
            "source_filter": "method=risk_parity",
            "source_field": "best_net_sharpe_schedule; monthly_net_sharpe",
        },
        {
            "claim_id": "finance_neutrality",
            "finding": (
                "The finance lexicon lowers neutral headline share from "
                f"{sentiment_model.loc['plain_neutral_share']:.2%} to "
                f"{sentiment_model.loc['finance_neutral_share']:.2%}."
            ),
            "primary_value": sentiment_model.loc["finance_neutral_share"],
            "comparison_value": sentiment_model.loc["plain_neutral_share"],
            "difference": (
                sentiment_model.loc["finance_neutral_share"]
                - sentiment_model.loc["plain_neutral_share"]
            ),
            "unit": "proportion",
            "source_artifact": "results/tables/sentiment_model_summary.csv",
            "source_filter": "neutral-share metrics",
            "source_field": "value",
        },
        {
            "claim_id": "coverage_dispersion",
            "finding": (
                f"Mean confidence ranges from {lowest_coverage['sector']} "
                f"({lowest_coverage['mean_coverage_confidence']:.2f}) to "
                f"{highest_coverage['sector']} "
                f"({highest_coverage['mean_coverage_confidence']:.2f})."
            ),
            "primary_value": lowest_coverage["mean_coverage_confidence"],
            "comparison_value": highest_coverage["mean_coverage_confidence"],
            "difference": (
                highest_coverage["mean_coverage_confidence"]
                - lowest_coverage["mean_coverage_confidence"]
            ),
            "unit": "confidence score",
            "source_artifact": "results/data/sector_sentiment_index.csv",
            "source_filter": "group by sector; minimum and maximum confidence means",
            "source_field": "coverage_confidence",
        },
        {
            "claim_id": "fusion_return",
            "finding": (
                "Coverage-aware fusion lowers net annualised return by "
                f"{abs(fusion_primary.delta_net_annualized_return_vs_base):.2%}."
            ),
            "primary_value": fusion_primary.net_annualized_return,
            "comparison_value": (
                fusion_primary.net_annualized_return
                - fusion_primary.delta_net_annualized_return_vs_base
            ),
            "difference": fusion_primary.delta_net_annualized_return_vs_base,
            "unit": "decimal annual return",
            "source_artifact": "results/tables/fusion_performance_comparison.csv",
            "source_filter": "variant=coverage_aware_finance",
            "source_field": "net_annualized_return; delta vs base",
        },
        {
            "claim_id": "fusion_drawdown",
            "finding": (
                "Coverage-aware fusion makes maximum drawdown "
                f"{fusion_primary.delta_net_maximum_drawdown_vs_base:.2%} shallower, "
                "but does not improve Sharpe."
            ),
            "primary_value": fusion_primary.net_maximum_drawdown,
            "comparison_value": (
                fusion_primary.net_maximum_drawdown
                - fusion_primary.delta_net_maximum_drawdown_vs_base
            ),
            "difference": fusion_primary.delta_net_sharpe_ratio_vs_base,
            "unit": "drawdown values; Sharpe change in difference",
            "source_artifact": "results/tables/fusion_performance_comparison.csv",
            "source_filter": "variant=coverage_aware_finance",
            "source_field": "maximum drawdown and Sharpe deltas",
        },
    ]
    return pd.DataFrame.from_records(records).assign(status="reconciled")


def _validation_summary(
    performance: pd.DataFrame,
    fact_sheets: pd.DataFrame,
    plain_finance: pd.DataFrame,
    coverage: pd.DataFrame,
    exhibits: pd.DataFrame,
    findings: pd.DataFrame,
    project_root: Path,
) -> pd.DataFrame:
    existing_validation_files = (
        "results/tables/portfolio_validation_summary.csv",
        "results/tables/rebalance_frequency_validation.csv",
        "results/tables/sentiment_validation_summary.csv",
        "results/tables/fusion_validation_summary.csv",
    )
    upstream_pass = all(
        pd.read_csv(project_root / path)["status"].eq("pass").all()
        for path in existing_validation_files
    )
    checks = {
        "compact_performance_has_15_funds": performance["fund_id"].nunique() == 15,
        "all_15_fact_sheets_reconcile": (
            len(fact_sheets) == 15 and fact_sheets["status"].eq("pass").all()
        ),
        "plain_finance_validation_complete": len(plain_finance) == 4,
        "coverage_summary_has_10_sectors": coverage["sector"].nunique() == 10,
        "all_9_exhibits_have_context_and_pass": (
            len(exhibits) == 9 and exhibits["status"].eq("pass").all()
        ),
        "all_claims_reconciled": findings["status"].eq("reconciled").all(),
        "all_claim_source_artifacts_exist": all(
            (project_root / path).exists() for path in findings["source_artifact"]
        ),
        "upstream_phase_validations_pass": upstream_pass,
        "displayed_numeric_values_are_finite": bool(
            np.isfinite(
                performance[
                    [
                        "growth_of_1_net",
                        "annualized_return_net",
                        "annualized_volatility_net",
                        "sharpe_ratio_net",
                        "maximum_drawdown_net",
                    ]
                ].to_numpy(dtype=float)
            ).all()
        ),
    }
    return pd.DataFrame(
        [
            {
                "check": check,
                "status": "pass" if passed else "fail",
                "detail": "Phase 6 evidence contract satisfied" if passed else "contract failed",
            }
            for check, passed in checks.items()
        ]
    )


def build_phase6_evidence(
    suite: PortfolioSuite,
    frequency: RebalanceExperimentResult,
    sentiment: SentimentResult,
    fusion: FusionResult,
    *,
    project_root: Path,
) -> Phase6Evidence:
    """Create compact report evidence and require exact artifact reconciliation."""
    performance = _report_performance_table(suite)
    fact_sheets = _fact_sheet_validation(suite)
    plain_finance = _plain_vs_finance_validation(sentiment)
    coverage = _coverage_confidence_summary(sentiment)
    exhibits = _exhibit_catalog(project_root)
    findings = _claim_findings(suite, frequency, sentiment, fusion, coverage)
    validation = _validation_summary(
        performance,
        fact_sheets,
        plain_finance,
        coverage,
        exhibits,
        findings,
        project_root,
    )
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail"), "check"].tolist()
        raise EvidenceReconciliationError(f"Phase 6 validation failed: {failures}")
    return Phase6Evidence(
        report_performance_table=performance,
        fact_sheet_validation=fact_sheets,
        plain_vs_finance_validation=plain_finance,
        coverage_confidence_summary=coverage,
        exhibit_catalog=exhibits,
        claim_to_artifact_findings=findings,
        validation_summary=validation,
    )


def save_phase6_evidence(result: Phase6Evidence, *, tables_dir: Path) -> list[Path]:
    """Save all Phase 6 report and reconciliation tables."""
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        tables_dir / "report_performance_table.csv": result.report_performance_table,
        tables_dir / "fact_sheet_validation.csv": result.fact_sheet_validation,
        tables_dir / "plain_vs_finance_validation.csv": result.plain_vs_finance_validation,
        tables_dir / "coverage_confidence_summary.csv": result.coverage_confidence_summary,
        tables_dir / "exhibit_catalog.csv": result.exhibit_catalog,
        tables_dir / "claim_to_artifact_findings.csv": result.claim_to_artifact_findings,
        tables_dir / "phase6_validation_summary.csv": result.validation_summary,
    }
    paths: list[Path] = []
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


__all__ = [
    "EvidenceReconciliationError",
    "Phase6Evidence",
    "build_phase6_evidence",
    "save_phase6_evidence",
]
