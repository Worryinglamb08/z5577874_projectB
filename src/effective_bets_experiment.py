"""Monthly prototype comparing PCA effective bets with asset risk parity."""

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
class EffectiveBetsExperiment:
    """Prototype paths, diagnostics, comparisons, and validation evidence."""

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
        metrics = performance_metrics(
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
        records.append(
            {
                "fund_id": portfolio_id,
                "fund_name": first["fund_name"],
                "asset_family": first["asset_family"],
                "method": first["method"],
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "annualization_days": annualization_days,
                "annualized_return": metrics["annualized_return"],
                "annualized_volatility": metrics["annualized_volatility"],
                "sharpe_ratio": metrics["sharpe_ratio"],
                "maximum_drawdown": metrics["maximum_drawdown"],
                "ending_growth_of_1": metrics["ending_growth_of_1"],
                "average_rebalance_turnover": float(rebalances["turnover"].mean()),
                "cumulative_turnover": float(rebalances["turnover"].sum()),
                "total_transaction_cost": float(
                    rebalances["transaction_cost"].sum()
                ),
                "average_target_change": _target_weight_change(portfolio_weights),
                "average_effective_number_of_bets": float(
                    portfolio_diagnostics["effective_number_of_bets"].mean()
                ),
                "minimum_effective_number_of_bets": float(
                    portfolio_diagnostics["effective_number_of_bets"].min()
                ),
                "latest_effective_number_of_bets": float(
                    portfolio_diagnostics["effective_number_of_bets"].iloc[-1]
                ),
                "average_effective_bet_ratio": float(
                    portfolio_diagnostics["effective_bet_ratio"].mean()
                ),
                "latest_nonzero_holding_count": int(
                    latest["target_weight"].gt(config.weight_tolerance).sum()
                ),
                "latest_weight_hhi": float(
                    np.square(latest["target_weight"]).sum()
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
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for family in sorted(returns["asset_family"].unique()):
        risk_parity_id = f"{family}_risk_parity"
        effective_bets_id = f"{family}_effective_bets"
        risk_weights = weights.loc[
            weights["fund_id"].eq(risk_parity_id),
            ["rebalance_date", "asset", "target_weight"],
        ]
        effective_weights = weights.loc[
            weights["fund_id"].eq(effective_bets_id),
            ["rebalance_date", "asset", "target_weight"],
        ]
        joined_weights = risk_weights.merge(
            effective_weights,
            on=["rebalance_date", "asset"],
            suffixes=("_risk_parity", "_effective_bets"),
            validate="one_to_one",
        )
        l1 = joined_weights.assign(
            distance=(
                joined_weights["target_weight_effective_bets"]
                - joined_weights["target_weight_risk_parity"]
            ).abs()
        ).groupby("rebalance_date")["distance"].sum()
        risk_returns = returns.loc[
            returns["fund_id"].eq(risk_parity_id), ["date", "net_return"]
        ]
        effective_returns = returns.loc[
            returns["fund_id"].eq(effective_bets_id), ["date", "net_return"]
        ]
        joined_returns = risk_returns.merge(
            effective_returns,
            on="date",
            suffixes=("_risk_parity", "_effective_bets"),
            validate="one_to_one",
        )
        family_metrics = metrics.loc[metrics["asset_family"].eq(family)].set_index(
            "method"
        )
        family_diagnostics = diagnostics.loc[
            diagnostics["asset_family"].eq(family),
            ["method", "rebalance_date", "effective_number_of_bets"],
        ]
        enb = family_diagnostics.pivot(
            index="rebalance_date",
            columns="method",
            values="effective_number_of_bets",
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
                        joined_returns["net_return_effective_bets"]
                    )
                ),
                "average_enb_improvement": float(
                    (enb["effective_bets"] - enb["risk_parity"]).mean()
                ),
                "enb_dominance_violation_count": int(
                    (enb["effective_bets"] + 1e-7 < enb["risk_parity"]).sum()
                ),
                "annualized_return_difference": float(
                    family_metrics.loc["effective_bets", "annualized_return"]
                    - family_metrics.loc["risk_parity", "annualized_return"]
                ),
                "sharpe_ratio_difference": float(
                    family_metrics.loc["effective_bets", "sharpe_ratio"]
                    - family_metrics.loc["risk_parity", "sharpe_ratio"]
                ),
                "turnover_difference": float(
                    family_metrics.loc[
                        "effective_bets", "average_rebalance_turnover"
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
    checks = (
        ("prototype_path_count", int(returns["fund_id"].nunique()), 6, "equal"),
        (
            "effective_bets_path_count",
            int(returns.loc[returns["method"].eq("effective_bets"), "fund_id"].nunique()),
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
            "enb_dominance_violation_count",
            int(distinctness["enb_dominance_violation_count"].sum()),
            0,
            "equal",
        ),
        (
            "nondistinct_family_count",
            int(distinctness["economically_distinct"].ne(True).sum()),
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


def build_effective_bets_experiment(
    features: ReturnFeatures, config: ModelConfig
) -> EffectiveBetsExperiment:
    """Run monthly PCA-ENB and Risk Parity paths on identical family panels."""
    panels = build_family_panels(features, config)
    backtests: list[FundBacktest] = []
    for family in config.families:
        for method in ("risk_parity", "effective_bets"):
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
    distinctness = _distinctness(returns, weights, metrics, diagnostics)
    validation = _validation(returns, weights, diagnostics, distinctness, config)
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise PortfolioValidationError(
            f"effective-bets prototype validation failed: {failures}"
        )
    return EffectiveBetsExperiment(
        fund_returns=returns,
        fund_weights=weights,
        rebalance_diagnostics=diagnostics,
        performance_comparison=metrics,
        method_distinctness=distinctness,
        validation_summary=validation,
    )


def save_effective_bets_experiment(
    experiment: EffectiveBetsExperiment,
    *,
    data_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Save prototype-only artifacts without changing the primary fund outputs."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "effective_bets_prototype_returns.csv": experiment.fund_returns,
        data_dir / "effective_bets_prototype_weights.csv": experiment.fund_weights,
        tables_dir
        / "effective_bets_prototype_diagnostics.csv": experiment.rebalance_diagnostics,
        tables_dir
        / "effective_bets_prototype_metrics.csv": experiment.performance_comparison,
        tables_dir
        / "effective_bets_prototype_distinctness.csv": experiment.method_distinctness,
        tables_dir
        / "effective_bets_prototype_validation.csv": experiment.validation_summary,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
    return list(outputs)


__all__ = [
    "EffectiveBetsExperiment",
    "build_effective_bets_experiment",
    "save_effective_bets_experiment",
]
