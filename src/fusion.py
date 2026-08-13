"""Coverage-aware, leakage-safe fusion of sector news into an equity fund.

The primary extension tilts the monthly equity minimum-variance target using
the previous observed trading day's finance sentiment multiplied by that same
day's coverage confidence.  The base optimiser, rebalance dates, eligible
assets, constraints, return sample, and cost model remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from src.config import ModelConfig
from src.features import ReturnFeatures
from src.portfolios import (
    METHOD_LABELS,
    PortfolioSuite,
    _drift_weights,
    build_family_panels,
    fund_id,
    performance_metrics,
)
from src.sentiment import SentimentResult

FUSION_VARIANTS: Final = {
    "base": ("Base minimum-variance fund", None),
    "plain_sentiment": ("Plain-VADER tilt", "plain_signal_lag1"),
    "finance_sentiment": ("Finance-VADER tilt", "finance_signal_lag1"),
    "coverage_aware_finance": (
        "Coverage-aware finance tilt",
        "coverage_adjusted_signal_lag1",
    ),
}


class FusionValidationError(ValueError):
    """Raised when a fusion input, timing identity, or weight is invalid."""


@dataclass(frozen=True)
class FusionResult:
    """Phase 5 signal, portfolio paths, comparisons, and validation evidence."""

    coverage_adjusted_sentiment: pd.DataFrame
    fusion_returns: pd.DataFrame
    fusion_weights: pd.DataFrame
    performance_comparison: pd.DataFrame
    tilt_sensitivity: pd.DataFrame
    validation_summary: pd.DataFrame


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if frame.empty:
        raise FusionValidationError(f"{name} is empty")
    if missing:
        raise FusionValidationError(f"{name} is missing required columns: {missing}")


def build_coverage_adjusted_signals(sector_index: pd.DataFrame) -> pd.DataFrame:
    """Keep raw inputs and lag their same-day combinations by one sector date."""
    required = {
        "date",
        "sector",
        "plain_sentiment_index",
        "finance_sentiment_index",
        "coverage_confidence",
        "has_news",
    }
    _require_columns(sector_index, required, "sector_index")
    result = sector_index[
        [
            "date",
            "sector",
            "plain_sentiment_index",
            "finance_sentiment_index",
            "coverage_confidence",
            "has_news",
        ]
    ].copy(deep=True)
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result = result.sort_values(["sector", "date"], kind="stable").reset_index(drop=True)
    if result.duplicated(["date", "sector"]).any():
        raise FusionValidationError("sector index date-sector keys must be unique")
    if not result["coverage_confidence"].between(0, 1).all():
        raise FusionValidationError("coverage confidence must lie in [0, 1]")

    result["coverage_adjusted_finance_sentiment"] = (
        result["finance_sentiment_index"] * result["coverage_confidence"]
    )
    grouped = result.groupby("sector", sort=False)
    result["signal_source_date"] = grouped["date"].shift(1)
    result["coverage_confidence_lag1"] = grouped["coverage_confidence"].shift(1)
    result["plain_signal_lag1"] = grouped["plain_sentiment_index"].shift(1)
    result["finance_signal_lag1"] = grouped["finance_sentiment_index"].shift(1)
    result["coverage_adjusted_signal_lag1"] = grouped[
        "coverage_adjusted_finance_sentiment"
    ].shift(1)
    result["tradable_signal_available"] = result[
        "coverage_adjusted_signal_lag1"
    ].notna()
    return result.sort_values(["date", "sector"], kind="stable").reset_index(drop=True)


def _cross_sectional_zscore(signal: pd.Series, cap: float) -> pd.Series:
    values = pd.Series(signal, dtype="float64")
    if values.isna().any() or not np.isfinite(values).all():
        raise FusionValidationError("sector signal must be finite and complete")
    scale = float(values.std(ddof=0))
    if scale <= 1e-12:
        return pd.Series(0.0, index=values.index, dtype="float64")
    return ((values - values.mean()) / scale).clip(-cap, cap)


def _normalise_with_cap(raw: pd.Series, cap: float) -> pd.Series:
    if cap <= 0 or cap * len(raw) < 1 - 1e-12:
        raise FusionValidationError("asset cap cannot support a fully invested portfolio")
    values = pd.Series(raw, dtype="float64")
    if values.lt(0).any() or not np.isfinite(values).all() or values.sum() <= 0:
        raise FusionValidationError("raw tilted weights must be nonnegative and finite")
    result = pd.Series(0.0, index=values.index, dtype="float64")
    remaining = pd.Series(True, index=values.index)
    residual = 1.0
    while remaining.any():
        if residual <= 1e-14:
            result.loc[remaining] = 0.0
            break
        remaining_total = float(values[remaining].sum())
        if remaining_total <= 0:
            raise FusionValidationError("positive residual has no investable raw weight")
        scaled = values[remaining] / remaining_total * residual
        over = scaled.gt(cap + 1e-14)
        if not over.any():
            result.loc[remaining] = scaled
            break
        capped_assets = scaled.index[over]
        result.loc[capped_assets] = cap
        remaining.loc[capped_assets] = False
        residual = 1.0 - float(result.sum())
    if abs(result.sum() - 1) > 1e-10 or result.gt(cap + 1e-10).any():
        raise FusionValidationError("capped tilted weights are invalid")
    return result


def apply_sentiment(
    base_weights: pd.Series,
    sector_signal: pd.Series,
    ticker_sector: pd.Series,
    *,
    strength: float,
    z_cap: float,
    asset_cap: float,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Exponentially tilt base weights by a clipped sector cross-section.

    ``strength`` is fixed before observing fusion performance.  Exponential
    multipliers remain positive, then capped proportional normalisation restores
    long-only, fully invested weights under the original individual-asset cap.
    """
    if strength < 0 or z_cap <= 0:
        raise FusionValidationError("tilt settings are invalid")
    base = pd.Series(base_weights, dtype="float64").sort_index()
    sectors = pd.Series(ticker_sector, dtype="string").reindex(base.index)
    if sectors.isna().any():
        raise FusionValidationError("every equity ticker needs a sector")
    signal = pd.Series(sector_signal, dtype="float64")
    missing_sectors = sorted(set(sectors).difference(signal.index))
    if missing_sectors:
        raise FusionValidationError(f"missing sector signals: {missing_sectors}")
    if abs(base.sum() - 1) > 1e-8 or base.lt(-1e-12).any():
        raise FusionValidationError("base weights must be long-only and fully invested")
    zscores = _cross_sectional_zscore(signal, z_cap)
    asset_zscores = sectors.map(zscores).astype(float)
    multipliers = np.exp(strength * asset_zscores)
    tilted = _normalise_with_cap(base * multipliers, asset_cap)
    return tilted, asset_zscores.rename("sector_signal_z"), multipliers.rename(
        "tilt_multiplier"
    )


def _base_targets(suite: PortfolioSuite, config: ModelConfig) -> pd.DataFrame:
    base_id = fund_id("equity", config.fusion_base_method)
    weights = suite.fund_weights.loc[suite.fund_weights["fund_id"].eq(base_id)].copy()
    if weights.empty:
        raise FusionValidationError(f"base fund not found: {base_id}")
    weights["rebalance_date"] = pd.to_datetime(weights["rebalance_date"])
    return weights.pivot(
        index="rebalance_date", columns="asset", values="target_weight"
    ).sort_index().sort_index(axis=1)


def _ticker_sector_map(ticker_sectors: pd.DataFrame) -> pd.Series:
    _require_columns(ticker_sectors, {"ticker", "sector"}, "ticker_sectors")
    pairs = ticker_sectors[["ticker", "sector"]].drop_duplicates()
    if pairs.duplicated("ticker").any():
        raise FusionValidationError("a ticker maps to multiple sectors")
    return pairs.set_index("ticker")["sector"].astype("string").sort_index()


def _simulate_variant(
    returns: pd.DataFrame,
    base_targets: pd.DataFrame,
    signals: pd.DataFrame,
    ticker_sectors: pd.Series,
    *,
    variant: str,
    signal_column: str | None,
    strength: float,
    config: ModelConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not base_targets.columns.equals(returns.columns):
        raise FusionValidationError("base targets and return assets differ")
    signal_lookup = signals.set_index(["date", "sector"])
    rebalance_dates = set(base_targets.index)
    first_live = base_targets.index.min()
    current: np.ndarray | None = None
    daily_records: list[dict[str, object]] = []
    weight_records: list[dict[str, object]] = []
    cost_rate = config.transaction_cost_bps / 10_000
    variant_label = FUSION_VARIANTS[variant][0]
    if variant == "base":
        variant_label = f"Base Equity {METHOD_LABELS[config.fusion_base_method]}"

    for date in returns.loc[first_live:].index:
        transaction_cost = 0.0
        turnover = 0.0
        rebalanced = date in rebalance_dates
        if rebalanced:
            base = base_targets.loc[date]
            if signal_column is None:
                target = base.copy()
                zscores = pd.Series(0.0, index=base.index)
                multipliers = pd.Series(1.0, index=base.index)
                asset_signal = pd.Series(np.nan, index=base.index)
                source_dates = pd.Series(pd.NaT, index=base.index)
            else:
                day = signal_lookup.loc[date]
                sector_signal = day[signal_column]
                target, zscores, multipliers = apply_sentiment(
                    base,
                    sector_signal,
                    ticker_sectors,
                    strength=strength,
                    z_cap=config.fusion_signal_z_cap,
                    asset_cap=config.equity_asset_cap,
                )
                asset_signal = ticker_sectors.reindex(base.index).map(sector_signal)
                source_dates = ticker_sectors.reindex(base.index).map(
                    day["signal_source_date"]
                )
                if source_dates.isna().any() or source_dates.ge(date).any():
                    raise FusionValidationError("fusion used a non-prior sentiment date")
            pretrade = np.zeros(len(target)) if current is None else current.copy()
            turnover = 1.0 if current is None else float(
                0.5 * np.abs(target.to_numpy() - pretrade).sum()
            )
            transaction_cost = turnover * cost_rate
            current = target.to_numpy(dtype=float)
            for asset in returns.columns:
                weight_records.append(
                    {
                        "variant": variant,
                        "variant_label": variant_label,
                        "base_method": config.fusion_base_method,
                        "rebalance_date": date,
                        "asset": asset,
                        "sector": ticker_sectors.loc[asset],
                        "signal_source_date": source_dates.loc[asset],
                        "lagged_sector_signal": asset_signal.loc[asset],
                        "sector_signal_z": zscores.loc[asset],
                        "tilt_multiplier": multipliers.loc[asset],
                        "base_target_weight": base.loc[asset],
                        "target_weight": target.loc[asset],
                        "pretrade_weight": pretrade[returns.columns.get_loc(asset)],
                        "turnover": turnover,
                        "transaction_cost": transaction_cost,
                        "tilt_strength": 0.0 if signal_column is None else strength,
                    }
                )
        if current is None:
            raise FusionValidationError("return encountered before the first rebalance")
        asset_returns = returns.loc[date].to_numpy(dtype=float)
        gross_return = float(current @ asset_returns)
        net_return = gross_return - transaction_cost
        daily_records.append(
            {
                "date": date,
                "variant": variant,
                "variant_label": variant_label,
                "base_method": config.fusion_base_method,
                "rebalanced": rebalanced,
                "gross_return": gross_return,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "net_return": net_return,
                "tilt_strength": 0.0 if signal_column is None else strength,
            }
        )
        current = _drift_weights(current, asset_returns)

    daily = pd.DataFrame.from_records(daily_records)
    daily["growth_of_1_gross"] = daily.groupby("variant", sort=False)[
        "gross_return"
    ].transform(lambda values: (1 + values).cumprod())
    daily["growth_of_1_net"] = daily.groupby("variant", sort=False)[
        "net_return"
    ].transform(lambda values: (1 + values).cumprod())
    daily["drawdown_net"] = daily["growth_of_1_net"] / daily[
        "growth_of_1_net"
    ].cummax() - 1
    return daily, pd.DataFrame.from_records(weight_records)


def _comparison_table(
    returns: pd.DataFrame, weights: pd.DataFrame, config: ModelConfig
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for variant, daily in returns.groupby("variant", sort=False):
        gross = performance_metrics(
            daily["gross_return"], 252, risk_free_rate_annual=config.risk_free_rate_annual
        )
        net = performance_metrics(
            daily["net_return"], 252, risk_free_rate_annual=config.risk_free_rate_annual
        )
        rebalance = daily.loc[daily["rebalanced"]]
        variant_weights = weights.loc[weights["variant"].eq(variant)]
        hhi = variant_weights.groupby("rebalance_date")["target_weight"].apply(
            lambda values: float(np.square(values).sum())
        )
        records.append(
            {
                "variant": variant,
                "variant_label": daily["variant_label"].iloc[0],
                "base_method": config.fusion_base_method,
                "signal_definition": FUSION_VARIANTS[variant][1] or "none",
                "tilt_strength": float(daily["tilt_strength"].iloc[0]),
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "observation_count": len(daily),
                "gross_annualized_return": gross["annualized_return"],
                "gross_sharpe_ratio": gross["sharpe_ratio"],
                "net_ending_growth_of_1": net["ending_growth_of_1"],
                "net_annualized_return": net["annualized_return"],
                "net_annualized_volatility": net["annualized_volatility"],
                "net_sharpe_ratio": net["sharpe_ratio"],
                "net_maximum_drawdown": net["maximum_drawdown"],
                "average_rebalance_turnover": rebalance["turnover"].mean(),
                "cumulative_turnover": rebalance["turnover"].sum(),
                "total_transaction_cost": rebalance["transaction_cost"].sum(),
                "average_target_weight_hhi": hhi.mean(),
                "maximum_target_weight_hhi": hhi.max(),
                "transaction_cost_bps": config.transaction_cost_bps,
            }
        )
    comparison = pd.DataFrame.from_records(records)
    base = comparison.set_index("variant").loc["base"]
    for metric in (
        "net_ending_growth_of_1",
        "net_annualized_return",
        "net_annualized_volatility",
        "net_sharpe_ratio",
        "net_maximum_drawdown",
        "cumulative_turnover",
    ):
        comparison[f"delta_{metric}_vs_base"] = comparison[metric] - base[metric]
    order = {variant: i for i, variant in enumerate(FUSION_VARIANTS)}
    return comparison.sort_values(
        "variant", key=lambda values: values.map(order), kind="stable"
    ).reset_index(drop=True)


def _tilt_sensitivity(
    returns_panel: pd.DataFrame,
    base_targets: pd.DataFrame,
    signals: pd.DataFrame,
    ticker_sectors: pd.Series,
    config: ModelConfig,
) -> pd.DataFrame:
    strengths = sorted(
        {0.0, config.fusion_tilt_strength, *config.fusion_tilt_strength_sensitivities}
    )
    base_daily, base_weights = _simulate_variant(
        returns_panel,
        base_targets,
        signals,
        ticker_sectors,
        variant="base",
        signal_column=None,
        strength=0.0,
        config=config,
    )
    base_row = _comparison_table(base_daily, base_weights, config).iloc[0].to_dict()
    records: list[dict[str, object]] = []
    for strength in strengths:
        if strength == 0:
            row = base_row.copy()
        else:
            daily, weights = _simulate_variant(
                returns_panel,
                base_targets,
                signals,
                ticker_sectors,
                variant="coverage_aware_finance",
                signal_column=FUSION_VARIANTS["coverage_aware_finance"][1],
                strength=strength,
                config=config,
            )
            comparison = _comparison_table(
                pd.concat([base_daily, daily], ignore_index=True),
                pd.concat([base_weights, weights], ignore_index=True),
                config,
            )
            row = comparison.loc[
                comparison["variant"].eq("coverage_aware_finance")
            ].iloc[0].to_dict()
        row["is_primary_strength"] = bool(
            np.isclose(strength, config.fusion_tilt_strength)
        )
        records.append(row)
    return pd.DataFrame.from_records(records).sort_values("tilt_strength").reset_index(
        drop=True
    )


def _validation_summary(
    result_signals: pd.DataFrame,
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    comparison: pd.DataFrame,
    suite: PortfolioSuite,
    config: ModelConfig,
) -> pd.DataFrame:
    adjusted_expected = (
        result_signals["finance_sentiment_index"]
        * result_signals["coverage_confidence"]
    )
    lag_expected = result_signals.groupby("sector", sort=False)[
        "coverage_adjusted_finance_sentiment"
    ].shift(1)
    sums = weights.groupby(["variant", "rebalance_date"])["target_weight"].sum()
    base_daily = returns.loc[returns["variant"].eq("base")].set_index("date")
    base_id = fund_id("equity", config.fusion_base_method)
    suite_base = suite.fund_returns.loc[suite.fund_returns["fund_id"].eq(base_id)].set_index(
        "date"
    )
    augmented = weights.loc[weights["variant"].ne("base")]
    checks = {
        "coverage_adjusted_identity": np.allclose(
            adjusted_expected,
            result_signals["coverage_adjusted_finance_sentiment"],
            atol=1e-12,
        ),
        "lag_is_previous_observed_sector_day": np.allclose(
            lag_expected,
            result_signals["coverage_adjusted_signal_lag1"],
            atol=1e-12,
            equal_nan=True,
        ),
        "signal_source_precedes_rebalance": bool(
            augmented["signal_source_date"].lt(augmented["rebalance_date"]).all()
        ),
        "weights_fully_invested": bool(np.allclose(sums, 1.0, atol=1e-10)),
        "weights_long_only": bool(weights["target_weight"].ge(-1e-12).all()),
        "individual_cap_respected": bool(
            weights["target_weight"].le(config.equity_asset_cap + 1e-10).all()
        ),
        "equity_only_assets": bool(~weights["asset"].str.endswith("-USD").any()),
        "base_daily_path_identity": bool(
            base_daily.index.equals(suite_base.index)
            and np.allclose(base_daily["gross_return"], suite_base["gross_return"])
            and np.allclose(base_daily["net_return"], suite_base["net_return"])
        ),
        "four_primary_variants": comparison["variant"].nunique() == 4,
        "metrics_are_finite": bool(
            np.isfinite(
                comparison[
                    [
                        "net_annualized_return",
                        "net_annualized_volatility",
                        "net_sharpe_ratio",
                        "net_maximum_drawdown",
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
                "detail": "required Phase 5 identity satisfied" if passed else "identity failed",
            }
            for check, passed in checks.items()
        ]
    )


def build_fusion_analysis(
    returns_features: ReturnFeatures,
    suite: PortfolioSuite,
    sentiment: SentimentResult,
    ticker_sectors: pd.DataFrame,
    config: ModelConfig,
) -> FusionResult:
    """Build the fixed-strength primary fusion and labelled sensitivities."""
    signals = build_coverage_adjusted_signals(sentiment.sector_index)
    panel = build_family_panels(returns_features, config)["equity"].returns
    base_targets = _base_targets(suite, config).reindex(columns=panel.columns)
    sectors = _ticker_sector_map(ticker_sectors).reindex(panel.columns)
    if sectors.isna().any():
        raise FusionValidationError("equity return panel has an unmapped ticker")

    daily_frames: list[pd.DataFrame] = []
    weight_frames: list[pd.DataFrame] = []
    for variant, (_, signal_column) in FUSION_VARIANTS.items():
        daily, weights = _simulate_variant(
            panel,
            base_targets,
            signals,
            sectors,
            variant=variant,
            signal_column=signal_column,
            strength=config.fusion_tilt_strength,
            config=config,
        )
        daily_frames.append(daily)
        weight_frames.append(weights)
    daily = pd.concat(daily_frames, ignore_index=True).sort_values(
        ["variant", "date"], kind="stable"
    ).reset_index(drop=True)
    weights = pd.concat(weight_frames, ignore_index=True).sort_values(
        ["variant", "rebalance_date", "asset"], kind="stable"
    ).reset_index(drop=True)
    comparison = _comparison_table(daily, weights, config)
    sensitivity = _tilt_sensitivity(panel, base_targets, signals, sectors, config)
    validation = _validation_summary(signals, daily, weights, comparison, suite, config)
    failures = validation.loc[validation["status"].eq("fail")]
    if not failures.empty:
        raise FusionValidationError(
            f"fusion validation failed: {failures['check'].tolist()}"
        )
    return FusionResult(
        coverage_adjusted_sentiment=signals,
        fusion_returns=daily,
        fusion_weights=weights,
        performance_comparison=comparison,
        tilt_sensitivity=sensitivity,
        validation_summary=validation,
    )


def save_fusion_outputs(
    result: FusionResult, *, data_dir: Path, tables_dir: Path
) -> list[Path]:
    """Save app-readable fusion paths plus compact Phase 5 evidence."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "coverage_adjusted_sentiment.csv": result.coverage_adjusted_sentiment,
        data_dir / "fusion_returns.csv": result.fusion_returns,
        data_dir / "fusion_weights.csv": result.fusion_weights,
        tables_dir / "fusion_performance_comparison.csv": result.performance_comparison,
        tables_dir / "fusion_tilt_sensitivity.csv": result.tilt_sensitivity,
        tables_dir / "fusion_validation_summary.csv": result.validation_summary,
    }
    paths: list[Path] = []
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


__all__ = [
    "FUSION_VARIANTS",
    "FusionResult",
    "FusionValidationError",
    "apply_sentiment",
    "build_coverage_adjusted_signals",
    "build_fusion_analysis",
    "save_fusion_outputs",
]
