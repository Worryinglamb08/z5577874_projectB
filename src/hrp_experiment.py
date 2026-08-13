"""Monthly prototype comparing Hierarchical Risk Parity with Risk Parity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import ModelConfig
from src.features import ReturnFeatures
from src.portfolios import (
    FundBacktest,
    PortfolioValidationError,
    build_family_panels,
    oos_backtest,
    performance_metrics,
)


@dataclass(frozen=True)
class HrpExperiment:
    """HRP paths, diagnostics, comparisons, and validation evidence."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    rebalance_diagnostics: pd.DataFrame
    performance_comparison: pd.DataFrame
    method_distinctness: pd.DataFrame
    validation_summary: pd.DataFrame


def _target_weight_change(weights: pd.DataFrame) -> float:
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
    for portfolio_id, daily in returns.groupby("fund_id", sort=True):
        first = daily.iloc[0]
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
        portfolio_weights = weights.loc[weights["fund_id"].eq(portfolio_id)]
        rebalances = portfolio_weights.drop_duplicates("rebalance_date")
        portfolio_diagnostics = diagnostics.loc[
            diagnostics["fund_id"].eq(portfolio_id)
        ]
        latest = portfolio_weights.loc[
            portfolio_weights["rebalance_date"].eq(
                portfolio_weights["rebalance_date"].max()
            )
        ]
        concentration = portfolio_weights.groupby("rebalance_date")[
            "target_weight"
        ].apply(lambda values: float(np.square(values).sum()))
        is_hrp = first["method"] == "hierarchical_risk_parity"
        records.append(
            {
                "fund_id": portfolio_id,
                "fund_name": first["fund_name"],
                "asset_family": first["asset_family"],
                "method": first["method"],
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "annualization_days": annualization_days,
                "gross_annualized_return": gross["annualized_return"],
                "gross_sharpe_ratio": gross["sharpe_ratio"],
                "annualized_return": net["annualized_return"],
                "annualized_volatility": net["annualized_volatility"],
                "sharpe_ratio": net["sharpe_ratio"],
                "maximum_drawdown": net["maximum_drawdown"],
                "ending_growth_of_1": net["ending_growth_of_1"],
                "average_rebalance_turnover": float(rebalances["turnover"].mean()),
                "cumulative_turnover": float(rebalances["turnover"].sum()),
                "total_transaction_cost": float(
                    rebalances["transaction_cost"].sum()
                ),
                "average_target_change": _target_weight_change(portfolio_weights),
                "average_target_weight_hhi": float(concentration.mean()),
                "latest_target_weight_hhi": float(concentration.iloc[-1]),
                "average_effective_number_of_bets": float(
                    portfolio_diagnostics["effective_number_of_bets"].mean()
                ),
                "latest_nonzero_holding_count": int(
                    latest["target_weight"].gt(config.weight_tolerance).sum()
                ),
                "projection_rebalance_share": (
                    float(
                        portfolio_diagnostics[
                            "constraint_projection_applied"
                        ].astype(bool).mean()
                    )
                    if is_hrp
                    else 0.0
                ),
                "average_projection_l1_distance": (
                    float(portfolio_diagnostics["projection_l1_distance"].mean())
                    if is_hrp
                    else 0.0
                ),
                "maximum_projection_l1_distance": (
                    float(portfolio_diagnostics["projection_l1_distance"].max())
                    if is_hrp
                    else 0.0
                ),
            }
        )
    return pd.DataFrame.from_records(records).sort_values(
        ["asset_family", "method"], kind="stable"
    ).reset_index(drop=True)


def _distinctness(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    metrics: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for family in sorted(returns["asset_family"].unique()):
        risk_id = f"{family}_risk_parity"
        hrp_id = f"{family}_hierarchical_risk_parity"
        risk_weights = weights.loc[
            weights["fund_id"].eq(risk_id),
            ["rebalance_date", "asset", "target_weight"],
        ]
        hrp_weights = weights.loc[
            weights["fund_id"].eq(hrp_id),
            ["rebalance_date", "asset", "target_weight"],
        ]
        joined_weights = risk_weights.merge(
            hrp_weights,
            on=["rebalance_date", "asset"],
            suffixes=("_risk_parity", "_hrp"),
            validate="one_to_one",
        )
        l1 = joined_weights.assign(
            distance=(
                joined_weights["target_weight_hrp"]
                - joined_weights["target_weight_risk_parity"]
            ).abs()
        ).groupby("rebalance_date")["distance"].sum()
        risk_returns = returns.loc[
            returns["fund_id"].eq(risk_id), ["date", "net_return"]
        ]
        hrp_returns = returns.loc[
            returns["fund_id"].eq(hrp_id), ["date", "net_return"]
        ]
        joined_returns = risk_returns.merge(
            hrp_returns,
            on="date",
            suffixes=("_risk_parity", "_hrp"),
            validate="one_to_one",
        )
        family_metrics = metrics.loc[metrics["asset_family"].eq(family)].set_index(
            "method"
        )
        records.append(
            {
                "asset_family": family,
                "common_rebalance_count": len(l1),
                "mean_l1_weight_distance": float(l1.mean()),
                "minimum_l1_weight_distance": float(l1.min()),
                "maximum_l1_weight_distance": float(l1.max()),
                "net_return_correlation": float(
                    joined_returns["net_return_risk_parity"].corr(
                        joined_returns["net_return_hrp"]
                    )
                ),
                "annualized_return_difference": float(
                    family_metrics.loc[
                        "hierarchical_risk_parity", "annualized_return"
                    ]
                    - family_metrics.loc["risk_parity", "annualized_return"]
                ),
                "sharpe_ratio_difference": float(
                    family_metrics.loc["hierarchical_risk_parity", "sharpe_ratio"]
                    - family_metrics.loc["risk_parity", "sharpe_ratio"]
                ),
                "maximum_drawdown_difference": float(
                    family_metrics.loc[
                        "hierarchical_risk_parity", "maximum_drawdown"
                    ]
                    - family_metrics.loc["risk_parity", "maximum_drawdown"]
                ),
                "turnover_difference": float(
                    family_metrics.loc[
                        "hierarchical_risk_parity", "average_rebalance_turnover"
                    ]
                    - family_metrics.loc[
                        "risk_parity", "average_rebalance_turnover"
                    ]
                ),
                "economically_distinct": bool(l1.mean() > 0.05),
            }
        )
    return pd.DataFrame.from_records(records)


def _validation(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    diagnostics: pd.DataFrame,
    distinctness: pd.DataFrame,
    config: ModelConfig,
) -> pd.DataFrame:
    weight_sums = weights.groupby(["fund_id", "rebalance_date"])[
        "target_weight"
    ].sum()
    hrp_diagnostics = diagnostics.loc[
        diagnostics["method"].eq("hierarchical_risk_parity")
    ]
    checks: list[tuple[str, object, object, str]] = [
        ("prototype_path_count", returns["fund_id"].nunique(), 6, "equal"),
        (
            "hrp_path_count",
            returns.loc[
                returns["method"].eq("hierarchical_risk_parity"), "fund_id"
            ].nunique(),
            3,
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
            int(
                diagnostics["estimation_end"]
                .ge(diagnostics["first_held_return_date"])
                .sum()
            ),
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
            "maximum_hrp_projection_residual",
            float(hrp_diagnostics["maximum_bound_residual"].max()),
            config.weight_tolerance,
            "maximum",
        ),
        (
            "nondistinct_family_count",
            int(distinctness["economically_distinct"].ne(True).sum()),
            0,
            "equal",
        ),
        ("approved_menu_contains_hrp", len(config.methods), 5, "equal"),
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


def build_hrp_experiment(
    features: ReturnFeatures, config: ModelConfig
) -> HrpExperiment:
    """Run monthly HRP and Risk-Parity paths on identical family panels."""
    panels = build_family_panels(features, config)
    backtests: list[FundBacktest] = []
    for family in config.families:
        for method in ("risk_parity", "hierarchical_risk_parity"):
            backtests.append(oos_backtest(panels[family], method, config=config))
    returns = pd.concat(
        [backtest.fund_returns for backtest in backtests], ignore_index=True
    ).sort_values(["fund_id", "date"], kind="stable").reset_index(drop=True)
    weights = pd.concat(
        [backtest.fund_weights for backtest in backtests], ignore_index=True
    ).sort_values(
        ["fund_id", "rebalance_date", "asset"], kind="stable"
    ).reset_index(drop=True)
    diagnostics = pd.concat(
        [backtest.diagnostics for backtest in backtests], ignore_index=True
    ).sort_values(["fund_id", "rebalance_date"], kind="stable").reset_index(drop=True)
    metrics = _performance_rows(returns, weights, diagnostics, config)
    distinctness = _distinctness(returns, weights, metrics)
    validation = _validation(returns, weights, diagnostics, distinctness, config)
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise PortfolioValidationError(f"HRP prototype validation failed: {failures}")
    return HrpExperiment(
        fund_returns=returns,
        fund_weights=weights,
        rebalance_diagnostics=diagnostics,
        performance_comparison=metrics,
        method_distinctness=distinctness,
        validation_summary=validation,
    )


def save_hrp_experiment(
    experiment: HrpExperiment,
    *,
    data_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Save HRP prototype artifacts without changing deployed-app inputs."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "hrp_prototype_returns.csv": experiment.fund_returns,
        data_dir / "hrp_prototype_weights.csv": experiment.fund_weights,
        tables_dir / "hrp_prototype_diagnostics.csv": experiment.rebalance_diagnostics,
        tables_dir / "hrp_prototype_metrics.csv": experiment.performance_comparison,
        tables_dir / "hrp_prototype_distinctness.csv": experiment.method_distinctness,
        tables_dir / "hrp_prototype_validation.csv": experiment.validation_summary,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
    return list(outputs)


__all__ = ["HrpExperiment", "build_hrp_experiment", "save_hrp_experiment"]
