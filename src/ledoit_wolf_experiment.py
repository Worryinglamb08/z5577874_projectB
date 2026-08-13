"""Controlled sample-covariance versus Ledoit-Wolf robustness prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from src.config import (
    AssetFamily,
    CovarianceEstimator,
    ModelConfig,
    PortfolioMethod,
)
from src.features import ReturnFeatures
from src.portfolios import (
    FundBacktest,
    PortfolioValidationError,
    build_family_panels,
    oos_backtest,
    performance_metrics,
)

PROTOTYPE_METHODS: Final[tuple[PortfolioMethod, ...]] = (
    "minimum_variance",
    "risk_parity",
    "maximum_sharpe",
    "hierarchical_risk_parity",
)
PROTOTYPE_SPECS: Final[tuple[tuple[AssetFamily, PortfolioMethod], ...]] = (
    *((family, method) for family in ("equity", "combined") for method in PROTOTYPE_METHODS),
    ("crypto", "hierarchical_risk_parity"),
)
PROTOTYPE_ESTIMATORS: Final[tuple[CovarianceEstimator, ...]] = (
    "sample_ridge",
    "ledoit_wolf",
)


@dataclass(frozen=True)
class LedoitWolfExperiment:
    """Matched paths, diagnostics, metrics, comparisons, and validation."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    rebalance_diagnostics: pd.DataFrame
    performance_comparison: pd.DataFrame
    paired_comparison: pd.DataFrame
    validation_summary: pd.DataFrame


def _tag_backtest(
    backtest: FundBacktest,
    covariance_estimator: CovarianceEstimator,
) -> FundBacktest:
    frames: list[pd.DataFrame] = []
    for source in (
        backtest.fund_returns,
        backtest.fund_weights,
        backtest.diagnostics,
    ):
        frame = source.copy()
        frame["covariance_estimator"] = covariance_estimator
        frame["prototype_id"] = frame["fund_id"].astype(str) + "__" + covariance_estimator
        frames.append(frame)
    return FundBacktest(*frames)


def _average_target_change(weights: pd.DataFrame) -> float:
    targets = weights.pivot(
        index="rebalance_date", columns="asset", values="target_weight"
    ).sort_index()
    changes = 0.5 * targets.diff().abs().sum(axis=1).iloc[1:]
    return float(changes.mean()) if not changes.empty else 0.0


def _performance_rows(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    diagnostics: pd.DataFrame,
    config: ModelConfig,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for prototype_id, daily in returns.groupby("prototype_id", sort=True):
        first = daily.iloc[0]
        selected_weights = weights.loc[weights["prototype_id"].eq(prototype_id)]
        selected_diagnostics = diagnostics.loc[diagnostics["prototype_id"].eq(prototype_id)]
        annualization_days = 365 if first["asset_family"] == "crypto" else 252
        gross = performance_metrics(
            daily["gross_return"],
            annualization_days,
            risk_free_rate_annual=config.risk_free_rate_annual,
        )
        net = performance_metrics(
            daily["net_return"],
            annualization_days,
            risk_free_rate_annual=config.risk_free_rate_annual,
        )
        concentration = selected_weights.groupby("rebalance_date")["target_weight"].apply(
            lambda values: float(np.square(values).sum())
        )
        records.append(
            {
                "prototype_id": prototype_id,
                "fund_id": first["fund_id"],
                "fund_name": first["fund_name"],
                "asset_family": first["asset_family"],
                "method": first["method"],
                "covariance_estimator": first["covariance_estimator"],
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "annualization_days": annualization_days,
                "rebalance_count": len(selected_diagnostics),
                "gross_annualized_return": gross["annualized_return"],
                "net_annualized_return": net["annualized_return"],
                "net_annualized_volatility": net["annualized_volatility"],
                "net_sharpe_ratio": net["sharpe_ratio"],
                "net_maximum_drawdown": net["maximum_drawdown"],
                "ending_growth_of_1_net": net["ending_growth_of_1"],
                "average_rebalance_turnover": float(selected_diagnostics["turnover"].mean()),
                "cumulative_turnover": float(selected_diagnostics["turnover"].sum()),
                "total_transaction_cost": float(selected_diagnostics["transaction_cost"].sum()),
                "average_target_change": _average_target_change(selected_weights),
                "average_target_weight_hhi": float(concentration.mean()),
                "median_covariance_condition_number": float(
                    selected_diagnostics["covariance_condition_number"].median()
                ),
                "maximum_covariance_condition_number": float(
                    selected_diagnostics["covariance_condition_number"].max()
                ),
                "mean_covariance_shrinkage": float(
                    selected_diagnostics["covariance_shrinkage"].fillna(0).mean()
                ),
            }
        )
    return (
        pd.DataFrame.from_records(records)
        .sort_values(["asset_family", "method", "covariance_estimator"], kind="stable")
        .reset_index(drop=True)
    )


def _paired_comparison(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    metrics: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for family, method in PROTOTYPE_SPECS:
        pair = metrics.loc[
            metrics["asset_family"].eq(family) & metrics["method"].eq(method)
        ].set_index("covariance_estimator")
        sample = pair.loc["sample_ridge"]
        shrunk = pair.loc["ledoit_wolf"]
        selected_weights = weights.loc[
            weights["asset_family"].eq(family) & weights["method"].eq(method),
            [
                "covariance_estimator",
                "rebalance_date",
                "asset",
                "target_weight",
            ],
        ]
        sample_weights = selected_weights.loc[
            selected_weights["covariance_estimator"].eq("sample_ridge")
        ]
        shrunk_weights = selected_weights.loc[
            selected_weights["covariance_estimator"].eq("ledoit_wolf")
        ]
        joined_weights = sample_weights.merge(
            shrunk_weights,
            on=["rebalance_date", "asset"],
            suffixes=("_sample", "_ledoit_wolf"),
            validate="one_to_one",
        )
        l1 = (
            joined_weights.assign(
                distance=(
                    joined_weights["target_weight_ledoit_wolf"]
                    - joined_weights["target_weight_sample"]
                ).abs()
            )
            .groupby("rebalance_date")["distance"]
            .sum()
        )
        selected_returns = returns.loc[
            returns["asset_family"].eq(family) & returns["method"].eq(method),
            ["covariance_estimator", "date", "net_return"],
        ]
        joined_returns = selected_returns.loc[
            selected_returns["covariance_estimator"].eq("sample_ridge")
        ].merge(
            selected_returns.loc[selected_returns["covariance_estimator"].eq("ledoit_wolf")],
            on="date",
            suffixes=("_sample", "_ledoit_wolf"),
            validate="one_to_one",
        )
        condition_ratio = float(
            shrunk["median_covariance_condition_number"]
            / sample["median_covariance_condition_number"]
        )
        target_change_delta = float(
            shrunk["average_target_change"] - sample["average_target_change"]
        )
        turnover_delta = float(
            shrunk["average_rebalance_turnover"] - sample["average_rebalance_turnover"]
        )
        sharpe_delta = float(shrunk["net_sharpe_ratio"] - sample["net_sharpe_ratio"])
        drawdown_delta = float(shrunk["net_maximum_drawdown"] - sample["net_maximum_drawdown"])
        stability_tolerance = max(
            0.005,
            0.05 * float(sample["average_target_change"]),
        )
        turnover_tolerance = max(
            0.005,
            0.05 * float(sample["average_rebalance_turnover"]),
        )
        conditioning_improved = condition_ratio < 1.0
        target_stability_not_worse = target_change_delta <= stability_tolerance
        turnover_not_worse = turnover_delta <= turnover_tolerance
        sharpe_not_materially_worse = sharpe_delta >= -0.05
        drawdown_not_materially_worse = drawdown_delta >= -0.02
        records.append(
            {
                "asset_family": family,
                "method": method,
                "common_rebalance_count": len(l1),
                "mean_l1_weight_distance": float(l1.mean()),
                "maximum_l1_weight_distance": float(l1.max()),
                "net_return_correlation": float(
                    joined_returns["net_return_sample"].corr(
                        joined_returns["net_return_ledoit_wolf"]
                    )
                ),
                "condition_number_ratio_ledoit_to_sample": condition_ratio,
                "net_annualized_return_delta": float(
                    shrunk["net_annualized_return"] - sample["net_annualized_return"]
                ),
                "net_annualized_volatility_delta": float(
                    shrunk["net_annualized_volatility"] - sample["net_annualized_volatility"]
                ),
                "net_sharpe_ratio_delta": sharpe_delta,
                "net_maximum_drawdown_delta": drawdown_delta,
                "average_turnover_delta": turnover_delta,
                "average_target_change_delta": target_change_delta,
                "average_hhi_delta": float(
                    shrunk["average_target_weight_hhi"] - sample["average_target_weight_hhi"]
                ),
                "conditioning_improved": conditioning_improved,
                "target_stability_not_worse": target_stability_not_worse,
                "turnover_not_worse": turnover_not_worse,
                "sharpe_not_materially_worse": sharpe_not_materially_worse,
                "drawdown_not_materially_worse": drawdown_not_materially_worse,
                "candidate_for_adoption": bool(
                    conditioning_improved
                    and target_stability_not_worse
                    and turnover_not_worse
                    and sharpe_not_materially_worse
                    and drawdown_not_materially_worse
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def _validation(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    diagnostics: pd.DataFrame,
    config: ModelConfig,
) -> pd.DataFrame:
    expected_path_count = len(PROTOTYPE_SPECS) * len(PROTOTYPE_ESTIMATORS)
    rebalance_counts = diagnostics.groupby("prototype_id").size()
    weight_sums = weights.groupby(["prototype_id", "rebalance_date"])["target_weight"].sum()
    ledoit = diagnostics.loc[diagnostics["covariance_estimator"].eq("ledoit_wolf")]
    sample = diagnostics.loc[
        diagnostics["covariance_estimator"].eq("sample_ridge"),
        [
            "asset_family",
            "method",
            "rebalance_date",
            "sample_covariance_condition_number",
            "covariance_condition_number",
        ],
    ]
    paired_diagnostics = sample.merge(
        ledoit[
            [
                "asset_family",
                "method",
                "rebalance_date",
                "sample_covariance_condition_number",
                "covariance_condition_number",
            ]
        ],
        on=["asset_family", "method", "rebalance_date"],
        suffixes=("_sample_run", "_ledoit_run"),
        validate="one_to_one",
    )
    checks: list[tuple[str, object, object, str]] = [
        (
            "prototype_path_count",
            returns["prototype_id"].nunique(),
            expected_path_count,
            "equal",
        ),
        (
            "prototype_rebalance_count",
            len(diagnostics),
            expected_path_count * 36,
            "equal",
        ),
        (
            "invalid_path_rebalance_count",
            int(rebalance_counts.ne(36).sum()),
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
            "temporal_order_violations",
            int(diagnostics["estimation_end"].ge(diagnostics["first_held_return_date"]).sum()),
            0,
            "equal",
        ),
        (
            "maximum_weight_sum_residual",
            float((weight_sums - 1).abs().max()),
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
            "nonpositive_covariance_eigenvalue_count",
            int(diagnostics["covariance_minimum_eigenvalue"].le(0).sum()),
            0,
            "equal",
        ),
        (
            "invalid_ledoit_wolf_shrinkage_count",
            int((~ledoit["covariance_shrinkage"].between(0, 1, inclusive="both")).sum()),
            0,
            "equal",
        ),
        (
            "sample_input_condition_mismatch_count",
            int(
                (
                    ~np.isclose(
                        paired_diagnostics["sample_covariance_condition_number_sample_run"],
                        paired_diagnostics["sample_covariance_condition_number_ledoit_run"],
                        rtol=1e-12,
                        atol=0,
                    )
                ).sum()
            ),
            0,
            "equal",
        ),
        (
            "ledoit_conditioning_nonimprovement_count",
            int(
                paired_diagnostics["covariance_condition_number_ledoit_run"]
                .ge(paired_diagnostics["covariance_condition_number_sample_run"])
                .sum()
            ),
            0,
            "equal",
        ),
    ]
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


def build_ledoit_wolf_experiment(
    features: ReturnFeatures,
    config: ModelConfig,
) -> LedoitWolfExperiment:
    """Run matched monthly covariance-estimator paths without changing the menu."""
    panels = build_family_panels(features, config)
    backtests: list[FundBacktest] = []
    for family, method in PROTOTYPE_SPECS:
        for estimator in PROTOTYPE_ESTIMATORS:
            backtest = oos_backtest(
                panels[family],
                method,
                config=config,
                covariance_estimator=estimator,
            )
            backtests.append(_tag_backtest(backtest, estimator))
    returns = (
        pd.concat([backtest.fund_returns for backtest in backtests], ignore_index=True)
        .sort_values(["prototype_id", "date"], kind="stable")
        .reset_index(drop=True)
    )
    weights = (
        pd.concat([backtest.fund_weights for backtest in backtests], ignore_index=True)
        .sort_values(["prototype_id", "rebalance_date", "asset"], kind="stable")
        .reset_index(drop=True)
    )
    diagnostics = (
        pd.concat([backtest.diagnostics for backtest in backtests], ignore_index=True)
        .sort_values(["prototype_id", "rebalance_date"], kind="stable")
        .reset_index(drop=True)
    )
    metrics = _performance_rows(returns, weights, diagnostics, config)
    paired = _paired_comparison(returns, weights, metrics)
    validation = _validation(returns, weights, diagnostics, config)
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise PortfolioValidationError(f"Ledoit-Wolf prototype validation failed: {failures}")
    return LedoitWolfExperiment(
        fund_returns=returns,
        fund_weights=weights,
        rebalance_diagnostics=diagnostics,
        performance_comparison=metrics,
        paired_comparison=paired,
        validation_summary=validation,
    )


def save_ledoit_wolf_experiment(
    experiment: LedoitWolfExperiment,
    *,
    data_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Save isolated prototype artifacts without changing deployed-app inputs."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "ledoit_wolf_prototype_returns.csv": experiment.fund_returns,
        data_dir / "ledoit_wolf_prototype_weights.csv": experiment.fund_weights,
        tables_dir / "ledoit_wolf_prototype_diagnostics.csv": experiment.rebalance_diagnostics,
        tables_dir / "ledoit_wolf_prototype_metrics.csv": experiment.performance_comparison,
        tables_dir / "ledoit_wolf_prototype_paired_comparison.csv": experiment.paired_comparison,
        tables_dir / "ledoit_wolf_prototype_validation.csv": experiment.validation_summary,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
    return list(outputs)


__all__ = [
    "LedoitWolfExperiment",
    "build_ledoit_wolf_experiment",
    "save_ledoit_wolf_experiment",
]
