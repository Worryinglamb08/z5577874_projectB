"""Monthly prototype comparing minimum CVaR with defensive portfolio rules."""

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

COMPARATORS = ("minimum_variance", "hierarchical_risk_parity")
METHODS = (*COMPARATORS, "conditional_value_at_risk")


@dataclass(frozen=True)
class CvarExperiment:
    """CVaR paths, diagnostics, comparisons, and validation evidence."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    rebalance_diagnostics: pd.DataFrame
    performance_comparison: pd.DataFrame
    method_distinctness: pd.DataFrame
    validation_summary: pd.DataFrame


def _expected_shortfall(returns: pd.Series, confidence: float) -> tuple[float, float]:
    losses = -pd.Series(returns, dtype="float64")
    var = float(losses.quantile(confidence, interpolation="higher"))
    tail = losses.loc[losses.ge(var - 1e-12)]
    return var, float(tail.mean())


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
        net = performance_metrics(
            daily["net_return"],
            annualization_days,
            risk_free_rate_annual=config.risk_free_rate_annual,
        )
        var, cvar = _expected_shortfall(daily["net_return"], config.cvar_confidence)
        portfolio_weights = weights.loc[weights["fund_id"].eq(portfolio_id)]
        rebalances = portfolio_weights.drop_duplicates("rebalance_date")
        portfolio_diagnostics = diagnostics.loc[
            diagnostics["fund_id"].eq(portfolio_id)
        ]
        latest_date = portfolio_weights["rebalance_date"].max()
        latest = portfolio_weights.loc[
            portfolio_weights["rebalance_date"].eq(latest_date)
        ]
        records.append(
            {
                "fund_id": portfolio_id,
                "fund_name": first["fund_name"],
                "asset_family": first["asset_family"],
                "method": first["method"],
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "annualization_days": annualization_days,
                "annualized_return": net["annualized_return"],
                "annualized_volatility": net["annualized_volatility"],
                "sharpe_ratio": net["sharpe_ratio"],
                "maximum_drawdown": net["maximum_drawdown"],
                "ending_growth_of_1": net["ending_growth_of_1"],
                "oos_daily_var_95": var,
                "oos_daily_cvar_95": cvar,
                "average_rebalance_turnover": float(rebalances["turnover"].mean()),
                "cumulative_turnover": float(rebalances["turnover"].sum()),
                "total_transaction_cost": float(
                    rebalances["transaction_cost"].sum()
                ),
                "average_target_change": _target_weight_change(portfolio_weights),
                "average_weight_hhi": float(
                    portfolio_diagnostics["weight_hhi"].mean()
                ),
                "average_effective_number_of_bets": float(
                    portfolio_diagnostics["effective_number_of_bets"].mean()
                ),
                "latest_nonzero_holding_count": int(
                    latest["target_weight"].gt(config.weight_tolerance).sum()
                ),
                "average_estimated_daily_cvar": (
                    float(portfolio_diagnostics["estimated_daily_cvar"].mean())
                    if first["method"] == "conditional_value_at_risk"
                    else np.nan
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
        cvar_id = f"{family}_conditional_value_at_risk"
        cvar_weights = weights.loc[
            weights["fund_id"].eq(cvar_id),
            ["rebalance_date", "asset", "target_weight"],
        ]
        cvar_returns = returns.loc[
            returns["fund_id"].eq(cvar_id), ["date", "net_return"]
        ]
        family_metrics = metrics.loc[metrics["asset_family"].eq(family)].set_index(
            "method"
        )
        for comparator in COMPARATORS:
            comparator_id = f"{family}_{comparator}"
            comparator_weights = weights.loc[
                weights["fund_id"].eq(comparator_id),
                ["rebalance_date", "asset", "target_weight"],
            ]
            joined_weights = cvar_weights.merge(
                comparator_weights,
                on=["rebalance_date", "asset"],
                suffixes=("_cvar", "_comparator"),
                validate="one_to_one",
            )
            l1 = joined_weights.assign(
                distance=(
                    joined_weights["target_weight_cvar"]
                    - joined_weights["target_weight_comparator"]
                ).abs()
            ).groupby("rebalance_date")["distance"].sum()
            comparator_returns = returns.loc[
                returns["fund_id"].eq(comparator_id), ["date", "net_return"]
            ]
            joined_returns = cvar_returns.merge(
                comparator_returns,
                on="date",
                suffixes=("_cvar", "_comparator"),
                validate="one_to_one",
            )
            records.append(
                {
                    "asset_family": family,
                    "comparator_method": comparator,
                    "common_rebalance_count": len(l1),
                    "mean_l1_weight_distance": float(l1.mean()),
                    "minimum_l1_weight_distance": float(l1.min()),
                    "maximum_l1_weight_distance": float(l1.max()),
                    "net_return_correlation": float(
                        joined_returns["net_return_cvar"].corr(
                            joined_returns["net_return_comparator"]
                        )
                    ),
                    "annualized_return_difference": float(
                        family_metrics.loc[
                            "conditional_value_at_risk", "annualized_return"
                        ]
                        - family_metrics.loc[comparator, "annualized_return"]
                    ),
                    "sharpe_ratio_difference": float(
                        family_metrics.loc[
                            "conditional_value_at_risk", "sharpe_ratio"
                        ]
                        - family_metrics.loc[comparator, "sharpe_ratio"]
                    ),
                    "oos_daily_cvar_difference": float(
                        family_metrics.loc[
                            "conditional_value_at_risk", "oos_daily_cvar_95"
                        ]
                        - family_metrics.loc[comparator, "oos_daily_cvar_95"]
                    ),
                    "turnover_difference": float(
                        family_metrics.loc[
                            "conditional_value_at_risk",
                            "average_rebalance_turnover",
                        ]
                        - family_metrics.loc[
                            comparator, "average_rebalance_turnover"
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
    config: ModelConfig,
) -> pd.DataFrame:
    weight_sums = weights.groupby(["fund_id", "rebalance_date"])[
        "target_weight"
    ].sum()
    cvar_diagnostics = diagnostics.loc[
        diagnostics["method"].eq("conditional_value_at_risk")
    ]
    checks = (
        ("prototype_path_count", int(returns["fund_id"].nunique()), 9, "equal"),
        (
            "cvar_path_count",
            int(
                returns.loc[
                    returns["method"].eq("conditional_value_at_risk"), "fund_id"
                ].nunique()
            ),
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
            "cvar_confidence_mismatch_count",
            int(cvar_diagnostics["cvar_confidence"].ne(config.cvar_confidence).sum()),
            0,
            "equal",
        ),
        (
            "nonfinite_cvar_objective_count",
            int((~np.isfinite(cvar_diagnostics["estimated_daily_cvar"])).sum()),
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


def build_cvar_experiment(
    features: ReturnFeatures, config: ModelConfig
) -> CvarExperiment:
    """Run monthly CVaR, Minimum Variance, and HRP on identical panels."""
    panels = build_family_panels(features, config)
    backtests: list[FundBacktest] = []
    for family in config.families:
        for method in METHODS:
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
    validation = _validation(returns, weights, diagnostics, config)
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise PortfolioValidationError(f"CVaR prototype validation failed: {failures}")
    return CvarExperiment(
        fund_returns=returns,
        fund_weights=weights,
        rebalance_diagnostics=diagnostics,
        performance_comparison=metrics,
        method_distinctness=distinctness,
        validation_summary=validation,
    )


def save_cvar_experiment(
    experiment: CvarExperiment,
    *,
    data_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Save prototype artifacts without changing primary fund or app inputs."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "cvar_prototype_returns.csv": experiment.fund_returns,
        data_dir / "cvar_prototype_weights.csv": experiment.fund_weights,
        tables_dir / "cvar_prototype_diagnostics.csv": experiment.rebalance_diagnostics,
        tables_dir / "cvar_prototype_metrics.csv": experiment.performance_comparison,
        tables_dir / "cvar_prototype_distinctness.csv": experiment.method_distinctness,
        tables_dir / "cvar_prototype_validation.csv": experiment.validation_summary,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
    return list(outputs)


__all__ = ["CvarExperiment", "build_cvar_experiment", "save_cvar_experiment"]
