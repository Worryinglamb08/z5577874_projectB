"""Controlled rebalance-frequency and transaction-cost experiments.

Daily, every-five-observation, and every-ten-observation schedules are diagnostic
only. Monthly remains the assignment-compliant primary product specification.
Within each selected method, all settings other than rebalance frequency remain
fixed, including eligible assets, trailing window, constraints, and live sample.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from src.config import (
    CovarianceEstimator,
    ModelConfig,
    PortfolioMethod,
    RebalanceSchedule,
)
from src.features import ReturnFeatures
from src.portfolios import (
    METHOD_LABELS,
    FundBacktest,
    PortfolioSuite,
    WeightSolution,
    build_family_panels,
    fund_id,
    oos_backtest,
    performance_metrics,
)

SCHEDULE_ORDER: Final = ("daily", "weekly", "biweekly", "monthly")
SCHEDULE_LABELS: Final = {
    "daily": "Daily",
    "weekly": "Every 5 days",
    "biweekly": "Every 10 days",
    "monthly": "Monthly",
}


class RebalanceExperimentError(ValueError):
    """Raised when the controlled frequency experiment fails validation."""


@dataclass(frozen=True)
class RebalanceExperimentResult:
    """Frequency paths, metric comparisons, and audit evidence."""

    experiment_returns: pd.DataFrame
    rebalance_diagnostics: pd.DataFrame
    frequency_metrics: pd.DataFrame
    cost_sensitivity: pd.DataFrame
    decision_support: pd.DataFrame
    validation_summary: pd.DataFrame


def experiment_id(method: PortfolioMethod, schedule: RebalanceSchedule) -> str:
    """Return a stable identifier for one diagnostic path."""
    return f"combined_{method}__{schedule}"


def _schedule_interval(schedule: str, config: ModelConfig) -> int | pd.NA:
    if schedule == "monthly":
        return pd.NA
    mapping = dict(
        zip(config.diagnostic_schedules, config.diagnostic_intervals, strict=True)
    )
    return mapping[schedule]


def _cost_scenarios(config: ModelConfig) -> tuple[float, ...]:
    return tuple(
        sorted(
            {
                config.transaction_cost_bps,
                *config.transaction_cost_sensitivities_bps,
            }
        )
    )


def _prefix_metrics(metrics: dict[str, object], prefix: str) -> dict[str, object]:
    return {f"{prefix}_{key}": value for key, value in metrics.items()}


def _metric_records(
    backtest: FundBacktest,
    method: PortfolioMethod,
    schedule: RebalanceSchedule,
    config: ModelConfig,
) -> list[dict[str, object]]:
    daily = backtest.fund_returns
    diagnostics = backtest.diagnostics
    gross = performance_metrics(
        daily["gross_return"],
        252,
        risk_free_rate_annual=config.risk_free_rate_annual,
    )
    live_years = len(daily) / 252
    records: list[dict[str, object]] = []
    for cost_bps in _cost_scenarios(config):
        transaction_cost = daily["turnover"] * cost_bps / 10_000
        net_returns = daily["gross_return"] - transaction_cost
        net = performance_metrics(
            net_returns,
            252,
            risk_free_rate_annual=config.risk_free_rate_annual,
        )
        records.append(
            {
                "experiment_id": experiment_id(method, schedule),
                "fund_id": fund_id("combined", method),
                "fund_name": f"Combined {METHOD_LABELS[method]}",
                "asset_family": "combined",
                "method": method,
                "method_label": METHOD_LABELS[method],
                "rebalance_schedule": schedule,
                "schedule_label": SCHEDULE_LABELS[schedule],
                "schedule_role": (
                    "primary" if schedule == "monthly" else "diagnostic experiment"
                ),
                "interval_observations": _schedule_interval(schedule, config),
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "estimation_window": int(diagnostics["estimation_observations"].iloc[0]),
                "eligible_asset_count": int(diagnostics["eligible_asset_count"].iloc[0]),
                "annualization_days": 252,
                "risk_free_rate_annual": config.risk_free_rate_annual,
                "transaction_cost_bps": cost_bps,
                **_prefix_metrics(gross, "gross"),
                **_prefix_metrics(net, "net"),
                "annualized_return": net["annualized_return"],
                "annualized_volatility": net["annualized_volatility"],
                "sharpe_ratio": net["sharpe_ratio"],
                "maximum_drawdown": net["maximum_drawdown"],
                "rebalance_count": len(diagnostics),
                "average_rebalance_turnover": float(diagnostics["turnover"].mean()),
                "cumulative_turnover": float(diagnostics["turnover"].sum()),
                "annualized_turnover": float(diagnostics["turnover"].sum() / live_years),
                "average_target_weight_hhi": float(diagnostics["weight_hhi"].mean()),
                "maximum_target_weight_hhi": float(diagnostics["weight_hhi"].max()),
                "average_crypto_sleeve_weight": float(
                    diagnostics["crypto_sleeve_weight"].mean()
                ),
                "total_transaction_cost_rate": float(transaction_cost.sum()),
                "cost_drag_ending_growth": (
                    gross["ending_growth_of_1"] - net["ending_growth_of_1"]
                ),
            }
        )
    return records


def _experiment_return_frame(
    backtest: FundBacktest,
    method: PortfolioMethod,
    schedule: RebalanceSchedule,
    config: ModelConfig,
) -> pd.DataFrame:
    result = backtest.fund_returns.copy()
    result.insert(0, "experiment_id", experiment_id(method, schedule))
    result["method_label"] = METHOD_LABELS[method]
    result["schedule_label"] = SCHEDULE_LABELS[schedule]
    result["schedule_role"] = (
        "primary" if schedule == "monthly" else "diagnostic experiment"
    )
    result["transaction_cost_bps"] = config.transaction_cost_bps
    return result


def _experiment_diagnostic_frame(
    backtest: FundBacktest,
    method: PortfolioMethod,
    schedule: RebalanceSchedule,
) -> pd.DataFrame:
    result = backtest.diagnostics.copy()
    result.insert(0, "experiment_id", experiment_id(method, schedule))
    result["method_label"] = METHOD_LABELS[method]
    result["schedule_label"] = SCHEDULE_LABELS[schedule]
    result["schedule_role"] = (
        "primary" if schedule == "monthly" else "diagnostic experiment"
    )
    return result


def _monthly_differences(
    backtests: dict[tuple[PortfolioMethod, RebalanceSchedule], FundBacktest],
    primary_suite: PortfolioSuite,
    config: ModelConfig,
) -> tuple[float, float]:
    return_differences: list[float] = []
    weight_differences: list[float] = []
    for method in config.frequency_experiment_methods:
        experiment = backtests[(method, "monthly")]
        primary_id = fund_id("combined", method)
        primary_returns = primary_suite.fund_returns.loc[
            primary_suite.fund_returns["fund_id"].eq(primary_id),
            ["date", "gross_return", "net_return"],
        ]
        compared_returns = experiment.fund_returns[
            ["date", "gross_return", "net_return"]
        ].merge(
            primary_returns,
            on="date",
            suffixes=("_experiment", "_primary"),
            validate="one_to_one",
        )
        for column in ("gross_return", "net_return"):
            return_differences.append(
                float(
                    (
                        compared_returns[f"{column}_experiment"]
                        - compared_returns[f"{column}_primary"]
                    ).abs().max()
                )
            )
        primary_weights = primary_suite.fund_weights.loc[
            primary_suite.fund_weights["fund_id"].eq(primary_id),
            ["rebalance_date", "asset", "target_weight"],
        ]
        compared_weights = experiment.fund_weights[
            ["rebalance_date", "asset", "target_weight"]
        ].merge(
            primary_weights,
            on=["rebalance_date", "asset"],
            suffixes=("_experiment", "_primary"),
            validate="one_to_one",
        )
        weight_differences.append(
            float(
                (
                    compared_weights["target_weight_experiment"]
                    - compared_weights["target_weight_primary"]
                ).abs().max()
            )
        )
    return max(return_differences), max(weight_differences)


def _cost_order_violations(cost_sensitivity: pd.DataFrame) -> int:
    violations = 0
    for _, group in cost_sensitivity.groupby("experiment_id", sort=False):
        ordered = group.sort_values("transaction_cost_bps")
        if not ordered["net_ending_growth_of_1"].is_monotonic_decreasing:
            violations += 1
    return violations


def _rebalance_order_violations(frequency_metrics: pd.DataFrame) -> int:
    violations = 0
    for _, group in frequency_metrics.groupby("method", sort=False):
        counts = group.set_index("rebalance_schedule")["rebalance_count"]
        ordered = counts.loc[list(SCHEDULE_ORDER)].to_numpy()
        if not np.all(np.diff(ordered) < 0):
            violations += 1
    return violations


def _validation_summary(
    backtests: dict[tuple[PortfolioMethod, RebalanceSchedule], FundBacktest],
    frequency_metrics: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    primary_suite: PortfolioSuite,
    config: ModelConfig,
) -> pd.DataFrame:
    diagnostics = pd.concat(
        [backtest.diagnostics for backtest in backtests.values()], ignore_index=True
    )
    monthly_return_difference, monthly_weight_difference = _monthly_differences(
        backtests, primary_suite, config
    )
    checks = (
        ("experiment_path_count", len(backtests), 8, "equal"),
        (
            "unique_first_live_dates",
            int(frequency_metrics["first_live_date"].nunique()),
            1,
            "equal",
        ),
        (
            "unique_last_live_dates",
            int(frequency_metrics["last_live_date"].nunique()),
            1,
            "equal",
        ),
        (
            "unique_estimation_windows",
            int(frequency_metrics["estimation_window"].nunique()),
            1,
            "equal",
        ),
        (
            "unique_eligible_asset_counts",
            int(frequency_metrics["eligible_asset_count"].nunique()),
            1,
            "equal",
        ),
        (
            "temporal_order_violations",
            int(
                diagnostics["estimation_end"]
                .ge(diagnostics["first_held_return_date"])
                .sum()
            ),
            0,
            "equal",
        ),
        (
            "solver_failure_count",
            int(diagnostics["solver_success"].ne(True).sum()),
            0,
            "equal",
        ),
        (
            "maximum_weight_sum_residual",
            float(diagnostics["weight_sum_residual"].max()),
            config.weight_tolerance,
            "maximum",
        ),
        (
            "maximum_bound_residual",
            float(diagnostics["maximum_bound_residual"].max()),
            config.weight_tolerance,
            "maximum",
        ),
        (
            "maximum_crypto_sleeve",
            float(diagnostics["crypto_sleeve_weight"].max()),
            config.combined_crypto_sleeve_cap + config.weight_tolerance,
            "maximum",
        ),
        (
            "monthly_primary_return_difference",
            monthly_return_difference,
            1e-14,
            "maximum",
        ),
        (
            "monthly_primary_weight_difference",
            monthly_weight_difference,
            1e-14,
            "maximum",
        ),
        (
            "cost_order_violations",
            _cost_order_violations(cost_sensitivity),
            0,
            "equal",
        ),
        (
            "rebalance_count_order_violations",
            _rebalance_order_violations(frequency_metrics),
            0,
            "equal",
        ),
    )
    records: list[dict[str, object]] = []
    for check, observed, threshold, rule in checks:
        passed = observed == threshold if rule == "equal" else observed <= threshold
        records.append(
            {
                "check": check,
                "observed_value": observed,
                "pass_rule": f"{rule} {threshold}",
                "status": "pass" if passed else "fail",
            }
        )
    return pd.DataFrame.from_records(records)


def _decision_support(frequency_metrics: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for method, group in frequency_metrics.groupby("method", sort=True):
        monthly = group.loc[group["rebalance_schedule"].eq("monthly")].iloc[0]
        best_sharpe = group.loc[group["sharpe_ratio"].idxmax()]
        daily = group.loc[group["rebalance_schedule"].eq("daily")].iloc[0]
        records.append(
            {
                "method": method,
                "method_label": METHOD_LABELS[method],
                "best_net_sharpe_schedule": best_sharpe["rebalance_schedule"],
                "best_net_sharpe": best_sharpe["sharpe_ratio"],
                "monthly_net_sharpe": monthly["sharpe_ratio"],
                "monthly_minus_best_net_sharpe": (
                    monthly["sharpe_ratio"] - best_sharpe["sharpe_ratio"]
                ),
                "daily_annualized_turnover": daily["annualized_turnover"],
                "monthly_annualized_turnover": monthly["annualized_turnover"],
                "daily_to_monthly_turnover_ratio": (
                    daily["annualized_turnover"] / monthly["annualized_turnover"]
                ),
                "daily_cost_drag_ending_growth": daily["cost_drag_ending_growth"],
                "monthly_cost_drag_ending_growth": monthly["cost_drag_ending_growth"],
                "interpretation_scope": (
                    "diagnostic evidence; monthly remains the primary product schedule"
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def build_rebalance_experiments(
    features: ReturnFeatures,
    primary_suite: PortfolioSuite,
    config: ModelConfig,
) -> RebalanceExperimentResult:
    """Run two selected combined methods under four controlled schedules."""
    panel = build_family_panels(features, config)["combined"]
    solution_cache: dict[
        tuple[str, str, CovarianceEstimator, pd.Timestamp, int], WeightSolution
    ] = {}
    backtests: dict[tuple[PortfolioMethod, RebalanceSchedule], FundBacktest] = {}
    return_frames: list[pd.DataFrame] = []
    diagnostic_frames: list[pd.DataFrame] = []
    metric_records: list[dict[str, object]] = []
    for method in config.frequency_experiment_methods:
        for schedule in SCHEDULE_ORDER:
            backtest = oos_backtest(
                panel,
                method,
                config=config,
                rebalance_schedule=schedule,
                transaction_cost_bps=config.transaction_cost_bps,
                solution_cache=solution_cache,
            )
            backtests[(method, schedule)] = backtest
            return_frames.append(
                _experiment_return_frame(backtest, method, schedule, config)
            )
            diagnostic_frames.append(
                _experiment_diagnostic_frame(backtest, method, schedule)
            )
            metric_records.extend(_metric_records(backtest, method, schedule, config))

    experiment_returns = pd.concat(return_frames, ignore_index=True).sort_values(
        ["experiment_id", "date"], kind="stable"
    ).reset_index(drop=True)
    diagnostics = pd.concat(diagnostic_frames, ignore_index=True).sort_values(
        ["experiment_id", "rebalance_date"], kind="stable"
    ).reset_index(drop=True)
    cost_sensitivity = pd.DataFrame.from_records(metric_records).sort_values(
        ["method", "rebalance_schedule", "transaction_cost_bps"], kind="stable"
    ).reset_index(drop=True)
    frequency_metrics = cost_sensitivity.loc[
        cost_sensitivity["transaction_cost_bps"].eq(config.transaction_cost_bps)
    ].reset_index(drop=True)
    validation = _validation_summary(
        backtests, frequency_metrics, cost_sensitivity, primary_suite, config
    )
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise RebalanceExperimentError(f"frequency experiment validation failed: {failures}")
    return RebalanceExperimentResult(
        experiment_returns=experiment_returns,
        rebalance_diagnostics=diagnostics,
        frequency_metrics=frequency_metrics,
        cost_sensitivity=cost_sensitivity,
        decision_support=_decision_support(frequency_metrics),
        validation_summary=validation,
    )


def save_rebalance_experiment_outputs(
    result: RebalanceExperimentResult,
    *,
    data_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Write the controlled frequency experiment and supporting audit files."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "rebalance_frequency_returns.csv": result.experiment_returns,
        tables_dir / "rebalance_frequency_metrics.csv": result.frequency_metrics,
        tables_dir / "rebalance_frequency_cost_sensitivity.csv": result.cost_sensitivity,
        tables_dir / "rebalance_frequency_rebalances.csv": (
            result.rebalance_diagnostics
        ),
        tables_dir / "rebalance_frequency_decision_support.csv": (
            result.decision_support
        ),
        tables_dir / "rebalance_frequency_validation.csv": result.validation_summary,
    }
    paths: list[Path] = []
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


__all__ = [
    "SCHEDULE_LABELS",
    "SCHEDULE_ORDER",
    "RebalanceExperimentError",
    "RebalanceExperimentResult",
    "build_rebalance_experiments",
    "experiment_id",
    "save_rebalance_experiment_outputs",
]
