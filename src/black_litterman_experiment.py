"""Monthly Risk-Parity Black-Litterman sentiment prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.black_litterman import build_black_litterman_allocation
from src.config import ModelConfig
from src.features import ReturnFeatures
from src.fusion import apply_sentiment, build_coverage_adjusted_signals
from src.portfolios import (
    FundBacktest,
    PortfolioValidationError,
    _drift_weights,
    annualized_moments,
    build_family_panels,
    oos_backtest,
    performance_metrics,
)
from src.sentiment import SentimentResult


@dataclass(frozen=True)
class BlackLittermanExperiment:
    """Prototype paths, weights, diagnostics, comparisons, and validation."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    rebalance_diagnostics: pd.DataFrame
    performance_comparison: pd.DataFrame
    method_distinctness: pd.DataFrame
    validation_summary: pd.DataFrame


def _variant_specs(config: ModelConfig) -> list[dict[str, object]]:
    scales = sorted(
        {
            config.black_litterman_view_scale_annual,
            *config.black_litterman_view_scale_sensitivities_annual,
        }
    )
    specs: list[dict[str, object]] = [
        {
            "variant": "risk_parity_reference",
            "variant_label": "Risk Parity reference",
            "kind": "base",
            "view_scale_annual": 0.0,
            "is_primary": False,
        },
        {
            "variant": "direct_coverage_tilt",
            "variant_label": "Direct coverage-aware sentiment tilt",
            "kind": "direct",
            "view_scale_annual": 0.0,
            "is_primary": False,
        },
    ]
    for scale in scales:
        percentage = 100 * scale
        specs.append(
            {
                "variant": f"black_litterman_{round(scale * 10_000)}bp",
                "variant_label": (
                    "Black-Litterman sentiment "
                    f"({percentage:.0f}% annual view scale)"
                ),
                "kind": "black_litterman",
                "view_scale_annual": scale,
                "is_primary": bool(
                    np.isclose(scale, config.black_litterman_view_scale_annual)
                ),
            }
        )
    return specs


def _ticker_sector_map(ticker_sectors: pd.DataFrame, assets: pd.Index) -> pd.Series:
    required = {"ticker", "sector"}
    if ticker_sectors.empty or not required.issubset(ticker_sectors.columns):
        raise PortfolioValidationError("ticker-sector map is incomplete")
    pairs = ticker_sectors[["ticker", "sector"]].drop_duplicates()
    if pairs.duplicated("ticker").any():
        raise PortfolioValidationError("a ticker maps to multiple sectors")
    sectors = pairs.set_index("ticker")["sector"].astype("string").reindex(assets)
    if sectors.isna().any():
        raise PortfolioValidationError("every equity asset needs a sector")
    return sectors


def _simulate_variant(
    panel_returns: pd.DataFrame,
    base_backtest: FundBacktest,
    signals: pd.DataFrame,
    asset_sectors: pd.Series,
    spec: dict[str, object],
    config: ModelConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_targets = base_backtest.fund_weights.pivot(
        index="rebalance_date", columns="asset", values="target_weight"
    ).sort_index().reindex(columns=panel_returns.columns)
    signal_lookup = signals.set_index(["date", "sector"])
    rebalance_dates = set(base_targets.index)
    first_live = base_targets.index.min()
    current: np.ndarray | None = None
    daily_records: list[dict[str, object]] = []
    weight_records: list[dict[str, object]] = []
    diagnostic_records: list[dict[str, object]] = []
    cost_rate = config.transaction_cost_bps / 10_000

    for date in panel_returns.loc[first_live:].index:
        position = panel_returns.index.get_loc(date)
        transaction_cost = 0.0
        turnover = 0.0
        rebalanced = date in rebalance_dates
        if rebalanced:
            history = panel_returns.iloc[position - config.equity_window : position]
            if len(history) != config.equity_window or history.index.max() >= date:
                raise PortfolioValidationError(
                    "Black-Litterman estimation history violates timing"
                )
            base = base_targets.loc[date]
            day = signal_lookup.loc[date]
            source_dates = pd.to_datetime(day["signal_source_date"])
            if source_dates.isna().any() or source_dates.ge(date).any():
                raise PortfolioValidationError(
                    "Black-Litterman signal must precede the rebalance"
                )
            raw_signal = day["finance_signal_lag1"].astype(float)
            coverage = day["coverage_confidence_lag1"].astype(float)
            adjusted_signal = day["coverage_adjusted_signal_lag1"].astype(float)
            _, covariance, covariance_diagnostics = annualized_moments(
                history, 252, config
            )
            kind = str(spec["kind"])
            if kind == "base":
                target = base.copy()
                allocation_diagnostics: dict[str, object] = {
                    "solver_success": True,
                    "solver_status": 0,
                    "solver_iterations": 0,
                    "active_view_count": 0,
                    "mean_active_confidence": 0.0,
                    "maximum_active_confidence": 0.0,
                    "minimum_view_uncertainty": np.nan,
                    "maximum_view_uncertainty": np.nan,
                    "posterior_return_shift_l2": 0.0,
                    "maximum_absolute_posterior_return_shift": 0.0,
                    "l1_weight_tilt_from_prior": 0.0,
                    "maximum_weight_sum_residual": abs(base.sum() - 1),
                    "maximum_bound_residual": 0.0,
                }
                sector_zscores = pd.Series(0.0, index=raw_signal.index)
            elif kind == "direct":
                target, asset_zscores, _ = apply_sentiment(
                    base,
                    adjusted_signal,
                    asset_sectors,
                    strength=config.fusion_tilt_strength,
                    z_cap=config.fusion_signal_z_cap,
                    asset_cap=config.equity_asset_cap,
                )
                sector_zscores = asset_zscores.groupby(asset_sectors).first()
                allocation_diagnostics = {
                    "solver_success": True,
                    "solver_status": 0,
                    "solver_iterations": 0,
                    "active_view_count": int(adjusted_signal.ne(0).sum()),
                    "mean_active_confidence": float(
                        coverage.loc[adjusted_signal.ne(0)].mean()
                    ),
                    "maximum_active_confidence": float(
                        coverage.loc[adjusted_signal.ne(0)].max()
                    ),
                    "minimum_view_uncertainty": np.nan,
                    "maximum_view_uncertainty": np.nan,
                    "posterior_return_shift_l2": np.nan,
                    "maximum_absolute_posterior_return_shift": np.nan,
                    "l1_weight_tilt_from_prior": float((target - base).abs().sum()),
                    "maximum_weight_sum_residual": abs(target.sum() - 1),
                    "maximum_bound_residual": float(
                        max(0.0, -target.min(), target.max() - config.equity_asset_cap)
                    ),
                }
            elif kind == "black_litterman":
                allocation = build_black_litterman_allocation(
                    base,
                    covariance,
                    asset_sectors,
                    raw_signal,
                    coverage,
                    view_scale_annual=float(spec["view_scale_annual"]),
                    config=config,
                )
                target = allocation.weights
                sector_zscores = allocation.sector_zscores
                allocation_diagnostics = allocation.diagnostics
            else:
                raise PortfolioValidationError(f"unsupported prototype kind: {kind}")

            pretrade = np.zeros(len(target)) if current is None else current.copy()
            turnover = (
                1.0
                if current is None
                else float(0.5 * np.abs(target.to_numpy() - pretrade).sum())
            )
            transaction_cost = turnover * cost_rate
            current = target.to_numpy(dtype=float)
            diagnostic_records.append(
                {
                    "variant": spec["variant"],
                    "variant_label": spec["variant_label"],
                    "kind": kind,
                    "rebalance_date": date,
                    "estimation_start": history.index.min(),
                    "estimation_end": history.index.max(),
                    "first_held_return_date": date,
                    "estimation_observations": len(history),
                    "view_scale_annual": spec["view_scale_annual"],
                    "is_primary": spec["is_primary"],
                    "risk_aversion": config.black_litterman_risk_aversion,
                    "tau": config.black_litterman_tau,
                    "turnover": turnover,
                    "transaction_cost": transaction_cost,
                    **covariance_diagnostics,
                    **allocation_diagnostics,
                }
            )
            for asset in panel_returns.columns:
                sector = str(asset_sectors.loc[asset])
                weight_records.append(
                    {
                        "variant": spec["variant"],
                        "variant_label": spec["variant_label"],
                        "kind": kind,
                        "rebalance_date": date,
                        "asset": asset,
                        "sector": sector,
                        "signal_source_date": source_dates.loc[sector],
                        "raw_finance_signal_lag1": raw_signal.loc[sector],
                        "coverage_confidence_lag1": coverage.loc[sector],
                        "coverage_adjusted_signal_lag1": adjusted_signal.loc[sector],
                        "sector_signal_z": sector_zscores.loc[sector],
                        "base_target_weight": base.loc[asset],
                        "pretrade_weight": pretrade[
                            panel_returns.columns.get_loc(asset)
                        ],
                        "target_weight": target.loc[asset],
                        "individual_cap": config.equity_asset_cap,
                        "view_scale_annual": spec["view_scale_annual"],
                        "is_primary": spec["is_primary"],
                        "turnover": turnover,
                        "transaction_cost": transaction_cost,
                    }
                )
        if current is None:
            raise PortfolioValidationError("return encountered before first rebalance")
        asset_returns = panel_returns.loc[date].to_numpy(dtype=float)
        gross_return = float(current @ asset_returns)
        net_return = gross_return - transaction_cost
        if net_return <= -1:
            raise PortfolioValidationError("prototype produced an invalid return")
        daily_records.append(
            {
                "variant": spec["variant"],
                "variant_label": spec["variant_label"],
                "kind": spec["kind"],
                "date": date,
                "rebalanced": rebalanced,
                "gross_return": gross_return,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "net_return": net_return,
                "view_scale_annual": spec["view_scale_annual"],
                "is_primary": spec["is_primary"],
            }
        )
        current = _drift_weights(current, asset_returns)

    daily = pd.DataFrame.from_records(daily_records)
    daily["growth_of_1_gross"] = (1 + daily["gross_return"]).cumprod()
    daily["growth_of_1_net"] = (1 + daily["net_return"]).cumprod()
    daily["drawdown_net"] = (
        daily["growth_of_1_net"] / daily["growth_of_1_net"].cummax() - 1
    )
    return (
        daily,
        pd.DataFrame.from_records(weight_records),
        pd.DataFrame.from_records(diagnostic_records),
    )


def _performance_table(
    returns: pd.DataFrame, weights: pd.DataFrame, config: ModelConfig
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for variant, daily in returns.groupby("variant", sort=False):
        net = performance_metrics(
            daily["net_return"],
            252,
            risk_free_rate_annual=config.risk_free_rate_annual,
        )
        variant_weights = weights.loc[weights["variant"].eq(variant)]
        rebalances = variant_weights.drop_duplicates("rebalance_date")
        hhi = variant_weights.groupby("rebalance_date")["target_weight"].apply(
            lambda values: float(np.square(values).sum())
        )
        first = daily.iloc[0]
        records.append(
            {
                "variant": variant,
                "variant_label": first["variant_label"],
                "kind": first["kind"],
                "view_scale_annual": first["view_scale_annual"],
                "is_primary": first["is_primary"],
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "observation_count": len(daily),
                "ending_growth_of_1": net["ending_growth_of_1"],
                "annualized_return": net["annualized_return"],
                "annualized_volatility": net["annualized_volatility"],
                "sharpe_ratio": net["sharpe_ratio"],
                "maximum_drawdown": net["maximum_drawdown"],
                "average_rebalance_turnover": float(rebalances["turnover"].mean()),
                "cumulative_turnover": float(rebalances["turnover"].sum()),
                "total_transaction_cost": float(
                    rebalances["transaction_cost"].sum()
                ),
                "average_target_weight_hhi": float(hhi.mean()),
                "maximum_target_weight_hhi": float(hhi.max()),
                "latest_nonzero_holding_count": int(
                    variant_weights.loc[
                        variant_weights["rebalance_date"].eq(
                            variant_weights["rebalance_date"].max()
                        ),
                        "target_weight",
                    ].gt(config.weight_tolerance).sum()
                ),
            }
        )
    result = pd.DataFrame.from_records(records)
    base = result.set_index("variant").loc["risk_parity_reference"]
    for metric in (
        "ending_growth_of_1",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "maximum_drawdown",
        "average_rebalance_turnover",
    ):
        result[f"delta_{metric}_vs_reference"] = result[metric] - base[metric]
    return result


def _distinctness(returns: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    base_weights = weights.loc[
        weights["variant"].eq("risk_parity_reference"),
        ["rebalance_date", "asset", "target_weight"],
    ]
    base_returns = returns.loc[
        returns["variant"].eq("risk_parity_reference"), ["date", "net_return"]
    ]
    records: list[dict[str, object]] = []
    for variant in returns.loc[
        returns["variant"].ne("risk_parity_reference"), "variant"
    ].unique():
        candidate_weights = weights.loc[
            weights["variant"].eq(variant),
            ["rebalance_date", "asset", "target_weight"],
        ]
        joined_weights = base_weights.merge(
            candidate_weights,
            on=["rebalance_date", "asset"],
            suffixes=("_reference", "_candidate"),
            validate="one_to_one",
        )
        l1 = joined_weights.assign(
            distance=(
                joined_weights["target_weight_candidate"]
                - joined_weights["target_weight_reference"]
            ).abs()
        ).groupby("rebalance_date")["distance"].sum()
        candidate_returns = returns.loc[
            returns["variant"].eq(variant), ["date", "net_return"]
        ]
        joined_returns = base_returns.merge(
            candidate_returns,
            on="date",
            suffixes=("_reference", "_candidate"),
            validate="one_to_one",
        )
        records.append(
            {
                "variant": variant,
                "common_rebalance_count": len(l1),
                "mean_l1_weight_distance": float(l1.mean()),
                "minimum_l1_weight_distance": float(l1.min()),
                "maximum_l1_weight_distance": float(l1.max()),
                "net_return_correlation": float(
                    joined_returns["net_return_reference"].corr(
                        joined_returns["net_return_candidate"]
                    )
                ),
                "economically_distinct": bool(l1.mean() > 0.05),
            }
        )
    return pd.DataFrame.from_records(records)


def _validation(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    diagnostics: pd.DataFrame,
    base_backtest: FundBacktest,
    specs: list[dict[str, object]],
    config: ModelConfig,
) -> pd.DataFrame:
    sums = weights.groupby(["variant", "rebalance_date"])["target_weight"].sum()
    augmented = weights.loc[weights["variant"].ne("risk_parity_reference")]
    base_daily = returns.loc[returns["variant"].eq("risk_parity_reference")].set_index(
        "date"
    )
    approved_daily = base_backtest.fund_returns.set_index("date")
    base_weights = weights.loc[
        weights["variant"].eq("risk_parity_reference"),
        ["rebalance_date", "asset", "target_weight"],
    ].sort_values(["rebalance_date", "asset"], kind="stable")
    approved_weights = base_backtest.fund_weights[
        ["rebalance_date", "asset", "target_weight"]
    ].sort_values(["rebalance_date", "asset"], kind="stable")
    expected_paths = len(specs)
    expected_rebalances = diagnostics["rebalance_date"].nunique()
    checks: list[tuple[str, object, object, str]] = [
        ("prototype_path_count", returns["variant"].nunique(), expected_paths, "equal"),
        (
            "primary_black_litterman_path_count",
            returns.loc[
                returns["kind"].eq("black_litterman") & returns["is_primary"],
                "variant",
            ].nunique(),
            1,
            "equal",
        ),
        (
            "rebalance_count_per_path",
            diagnostics.groupby("variant")["rebalance_date"].nunique().min(),
            expected_rebalances,
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
            "signal_timing_violations",
            int(augmented["signal_source_date"].ge(augmented["rebalance_date"]).sum()),
            0,
            "equal",
        ),
        (
            "maximum_weight_sum_residual",
            float((sums - 1).abs().max()),
            config.weight_tolerance,
            "maximum",
        ),
        (
            "maximum_bound_residual",
            float(
                max(
                    0.0,
                    -weights["target_weight"].min(),
                    weights["target_weight"].max() - config.equity_asset_cap,
                )
            ),
            config.weight_tolerance,
            "maximum",
        ),
        (
            "risk_parity_daily_path_identity",
            bool(
                base_daily.index.equals(approved_daily.index)
                and np.allclose(base_daily["net_return"], approved_daily["net_return"])
            ),
            True,
            "equal",
        ),
        (
            "risk_parity_target_identity",
            bool(
                base_weights[["rebalance_date", "asset"]].reset_index(drop=True).equals(
                    approved_weights[["rebalance_date", "asset"]].reset_index(drop=True)
                )
                and np.allclose(
                    base_weights["target_weight"], approved_weights["target_weight"]
                )
            ),
            True,
            "equal",
        ),
        (
            "approved_menu_excludes_black_litterman",
            len(config.methods),
            5,
            "equal",
        ),
        (
            "metrics_finite",
            bool(
                np.isfinite(
                    returns[["gross_return", "net_return", "growth_of_1_net"]]
                ).all().all()
            ),
            True,
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


def build_black_litterman_experiment(
    features: ReturnFeatures,
    sentiment: SentimentResult | pd.DataFrame,
    ticker_sectors: pd.DataFrame,
    config: ModelConfig,
) -> BlackLittermanExperiment:
    """Run the pre-specified equity-only monthly prototype."""
    panel = build_family_panels(features, config)["equity"]
    base_backtest = oos_backtest(panel, "risk_parity", config=config)
    if isinstance(sentiment, SentimentResult):
        signals = build_coverage_adjusted_signals(sentiment.sector_index)
    else:
        required = {
            "date",
            "sector",
            "signal_source_date",
            "finance_signal_lag1",
            "coverage_confidence_lag1",
            "coverage_adjusted_signal_lag1",
        }
        if sentiment.empty or not required.issubset(sentiment.columns):
            raise PortfolioValidationError(
                "prepared sentiment signals are empty or incomplete"
            )
        signals = sentiment.copy(deep=True)
        signals["date"] = pd.to_datetime(signals["date"], errors="raise")
        signals["signal_source_date"] = pd.to_datetime(
            signals["signal_source_date"], errors="coerce"
        )
        signals = signals.sort_values(["date", "sector"], kind="stable").reset_index(
            drop=True
        )
    sectors = _ticker_sector_map(ticker_sectors, panel.returns.columns)
    specs = _variant_specs(config)

    daily_frames: list[pd.DataFrame] = []
    weight_frames: list[pd.DataFrame] = []
    diagnostic_frames: list[pd.DataFrame] = []
    for spec in specs:
        daily, weights, diagnostics = _simulate_variant(
            panel.returns,
            base_backtest,
            signals,
            sectors,
            spec,
            config,
        )
        daily_frames.append(daily)
        weight_frames.append(weights)
        diagnostic_frames.append(diagnostics)
    returns = pd.concat(daily_frames, ignore_index=True).sort_values(
        ["variant", "date"], kind="stable"
    ).reset_index(drop=True)
    weights = pd.concat(weight_frames, ignore_index=True).sort_values(
        ["variant", "rebalance_date", "asset"], kind="stable"
    ).reset_index(drop=True)
    diagnostics = pd.concat(diagnostic_frames, ignore_index=True).sort_values(
        ["variant", "rebalance_date"], kind="stable"
    ).reset_index(drop=True)
    metrics = _performance_table(returns, weights, config)
    distinctness = _distinctness(returns, weights)
    validation = _validation(
        returns, weights, diagnostics, base_backtest, specs, config
    )
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise PortfolioValidationError(
            f"Black-Litterman prototype validation failed: {failures}"
        )
    return BlackLittermanExperiment(
        fund_returns=returns,
        fund_weights=weights,
        rebalance_diagnostics=diagnostics,
        performance_comparison=metrics,
        method_distinctness=distinctness,
        validation_summary=validation,
    )


def save_black_litterman_experiment(
    experiment: BlackLittermanExperiment,
    *,
    data_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Save prototype-only artifacts without altering deployed-app inputs."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "black_litterman_prototype_returns.csv": experiment.fund_returns,
        data_dir / "black_litterman_prototype_weights.csv": experiment.fund_weights,
        tables_dir
        / "black_litterman_prototype_diagnostics.csv": experiment.rebalance_diagnostics,
        tables_dir
        / "black_litterman_prototype_metrics.csv": experiment.performance_comparison,
        tables_dir
        / "black_litterman_prototype_distinctness.csv": experiment.method_distinctness,
        tables_dir
        / "black_litterman_prototype_validation.csv": experiment.validation_summary,
    }
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
    return list(outputs)


__all__ = [
    "BlackLittermanExperiment",
    "build_black_litterman_experiment",
    "save_black_litterman_experiment",
]
