"""Pure investor-facing calculations for the Stockist Funds app."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

from src.allocation_history import SECTOR_LABELS, sector_allocation
from src.app_data import AppArtifacts

FAMILY_LABELS = {
    "equity": "Equity",
    "crypto": "Crypto",
    "combined": "Combined",
}
METHOD_LABELS = {
    "equal_weight": "Equal Weight",
    "minimum_variance": "Minimum Variance",
    "risk_parity": "Risk Parity",
    "maximum_sharpe": "Maximum Sharpe",
    "hierarchical_risk_parity": "Hierarchical Risk Parity",
}
BENCHMARK_LABELS = {
    "same_family_equal_weight": "Same-family Equal Weight",
    "sp500_spy": "S&P 500 (SPY total-return proxy)",
    "nasdaq_composite_oneq": "Nasdaq Composite (ONEQ total-return proxy)",
}
ALLOCATION_BENCHMARK_LABELS = {
    "equal_selected_funds": "Equal allocation across selected funds",
    "sp500_spy": BENCHMARK_LABELS["sp500_spy"],
    "nasdaq_composite_oneq": BENCHMARK_LABELS["nasdaq_composite_oneq"],
}
METHOD_OBJECTIVES = {
    "equal_weight": "Allocates equally across every eligible asset.",
    "minimum_variance": (
        "Targets the lowest estimated portfolio variance under the approved caps."
    ),
    "risk_parity": "Balances estimated risk contribution across eligible assets.",
    "maximum_sharpe": (
        "Maximises estimated excess return per unit of volatility under the approved caps."
    ),
    "hierarchical_risk_parity": (
        "Groups assets by correlation and allocates recursively across cluster risk."
    ),
}
METHOD_SUMMARIES = {
    "equal_weight": (
        "Divides capital evenly across every eligible asset. It is the simplest "
        "rule and the transparent benchmark for judging the other methods."
    ),
    "minimum_variance": (
        "Uses historical co-movement to seek the lowest estimated portfolio "
        "volatility. It can favour assets that were calmer in the estimation window."
    ),
    "risk_parity": (
        "Allocates so no single asset dominates estimated portfolio risk. It does "
        "not forecast which asset will earn the highest return."
    ),
    "maximum_sharpe": (
        "Uses historical return and risk estimates to seek the highest expected "
        "return per unit of volatility. It is especially sensitive to estimation error."
    ),
    "hierarchical_risk_parity": (
        "Groups assets that moved similarly, then spreads capital across the resulting "
        "risk clusters. It is a lower-risk alternative, not a promise of higher returns."
    ),
}
FAMILY_PURPOSE = {
    "equity": "A systematic allocation across 50 large-company equities.",
    "crypto": "A higher-volatility allocation across 10 cryptoassets on their native calendar.",
    "combined": "A multi-asset allocation across equities and crypto, with crypto capped at 30%.",
}
FAMILY_RISKS = {
    "equity": "Equity-market, sector, concentration, estimation and drawdown risk.",
    "crypto": "Severe drawdown, volatility, liquidity, market-structure and model risk.",
    "combined": (
        "Equity and crypto drawdowns, cross-asset dependence, concentration and model risk."
    ),
}


@dataclass(frozen=True)
class AllocationAnalysis:
    """Historical evidence for one hypothetical fund-level allocation."""

    path: pd.DataFrame
    metrics: dict[str, float]
    underlying_exposure: pd.DataFrame
    asset_class_exposure: pd.DataFrame
    correlation: pd.DataFrame
    overlap: pd.DataFrame
    annualization_days: int


@dataclass(frozen=True)
class AllocationBenchmarkEvidence:
    """Hypothetical allocation and benchmark evidence on exact common dates."""

    path: pd.DataFrame
    benchmark_id: str
    benchmark_label: str
    allocation_metrics: dict[str, float]
    benchmark_metrics: dict[str, float]
    annualized_return_difference: float
    tracking_error: float
    first_date: pd.Timestamp
    last_date: pd.Timestamp
    observation_count: int
    annualization_days: int
    source: str
    return_basis: str


@dataclass(frozen=True)
class BenchmarkEvidence:
    """Fund and selected benchmark evidence on their exact common dates."""

    path: pd.DataFrame
    benchmark_id: str
    benchmark_label: str
    fund_annualized_return: float
    benchmark_annualized_return: float
    annualized_return_difference: float
    tracking_error: float
    first_date: pd.Timestamp
    last_date: pd.Timestamp
    observation_count: int
    annualization_days: int
    source: str
    return_basis: str


def stockist_name(fund_name: str) -> str:
    """Apply the approved product naming hierarchy without altering artifacts."""
    name = str(fund_name)
    return name if name.startswith("Stockist ") else f"Stockist {name}"


def fund_catalog(artifacts: AppArtifacts) -> pd.DataFrame:
    """Return one presentation-ready row per primary monthly fund."""
    performance_columns = [
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "rebalance_schedule",
        "first_live_date",
        "last_live_date",
        "net_ending_growth_of_1",
        "net_annualized_return",
        "net_annualized_volatility",
        "net_sharpe_ratio",
        "net_maximum_drawdown",
        "average_rebalance_turnover",
        "cumulative_turnover",
        "total_transaction_cost",
        "latest_target_weight_hhi",
        "latest_effective_number_of_assets",
        "latest_crypto_sleeve_weight",
        "annualized_return_vs_benchmark",
        "tracking_error",
        "information_ratio",
        "benchmark_fund_id",
        "transaction_cost_bps",
    ]
    sheet_columns = [
        "fund_id",
        "latest_rebalance_date",
        "latest_nonzero_holding_count",
        "latest_top_10_weight",
        "estimation_window",
        "evidence_label",
        "evidence_limit",
    ]
    catalog = artifacts.performance[performance_columns].merge(
        artifacts.fact_sheets[sheet_columns],
        on="fund_id",
        how="left",
        validate="one_to_one",
    )
    catalog["display_name"] = catalog["fund_name"].map(stockist_name)
    catalog["family_label"] = catalog["asset_family"].map(FAMILY_LABELS)
    catalog["method_label"] = catalog["method"].map(METHOD_LABELS)
    catalog["objective"] = catalog["method"].map(METHOD_OBJECTIVES)
    catalog["family_purpose"] = catalog["asset_family"].map(FAMILY_PURPOSE)
    catalog["principal_risks"] = catalog["asset_family"].map(FAMILY_RISKS)
    return catalog.sort_values(
        ["asset_family", "method"], kind="stable"
    ).reset_index(drop=True)


def comparison_table(catalog: pd.DataFrame, fund_ids: list[str]) -> pd.DataFrame:
    """Build an aligned exact comparison for the selected funds."""
    selected = catalog.loc[catalog["fund_id"].isin(fund_ids)].copy()
    order = {fund_id: index for index, fund_id in enumerate(fund_ids)}
    selected["_order"] = selected["fund_id"].map(order)
    return selected.sort_values("_order").drop(columns="_order")


def benchmark_evidence(
    artifacts: AppArtifacts, fund_id: str, benchmark_option: str
) -> BenchmarkEvidence:
    """Compare one fund with a strategy or external benchmark on common dates."""
    if benchmark_option not in BENCHMARK_LABELS:
        raise ValueError(f"Unknown benchmark option: {benchmark_option}")
    metrics = artifacts.performance.set_index("fund_id")
    if fund_id not in metrics.index:
        raise ValueError(f"Unknown fund: {fund_id}")
    fund = artifacts.fund_returns.loc[
        artifacts.fund_returns["fund_id"].eq(fund_id), ["date", "net_return"]
    ].rename(columns={"net_return": "fund_return"})
    if benchmark_option == "same_family_equal_weight":
        benchmark_id = str(metrics.loc[fund_id, "benchmark_fund_id"])
        benchmark = artifacts.fund_returns.loc[
            artifacts.fund_returns["fund_id"].eq(benchmark_id),
            ["date", "net_return"],
        ].rename(columns={"net_return": "benchmark_return"})
        benchmark_name = str(metrics.loc[benchmark_id, "fund_name"])
        label = stockist_name(benchmark_name)
        annualization_days = int(metrics.loc[fund_id, "annualization_days"])
        source = "Stockist Funds supplied-asset backtest"
        return_basis = "After the same 10 bp one-way turnover cost as the selected fund"
    else:
        benchmark_id = benchmark_option
        external = artifacts.external_benchmarks.loc[
            artifacts.external_benchmarks["benchmark_id"].eq(benchmark_id)
        ]
        if external.empty:
            raise ValueError(f"No external observations found for {benchmark_id}")
        benchmark = external[["date", "daily_return"]].rename(
            columns={"daily_return": "benchmark_return"}
        )
        label = str(external["benchmark_name"].iloc[0])
        annualization_days = 252
        source = str(external["source"].iloc[0])
        return_basis = str(external["return_basis"].iloc[0])
    joined = (
        fund.merge(benchmark, on="date", how="inner", validate="one_to_one")
        .dropna()
        .sort_values("date")
        .reset_index(drop=True)
    )
    if len(joined) < 2:
        raise ValueError("Fund and benchmark do not have enough common observations")
    joined["fund_growth_of_1"] = (1 + joined["fund_return"]).cumprod()
    joined["benchmark_growth_of_1"] = (1 + joined["benchmark_return"]).cumprod()
    years = len(joined) / annualization_days
    fund_return = float(joined["fund_growth_of_1"].iloc[-1] ** (1 / years) - 1)
    benchmark_return = float(
        joined["benchmark_growth_of_1"].iloc[-1] ** (1 / years) - 1
    )
    active = joined["fund_return"] - joined["benchmark_return"]
    tracking_error = float(active.std(ddof=1) * np.sqrt(annualization_days))
    return BenchmarkEvidence(
        path=joined,
        benchmark_id=benchmark_id,
        benchmark_label=label,
        fund_annualized_return=fund_return,
        benchmark_annualized_return=benchmark_return,
        annualized_return_difference=fund_return - benchmark_return,
        tracking_error=tracking_error,
        first_date=pd.Timestamp(joined["date"].min()),
        last_date=pd.Timestamp(joined["date"].max()),
        observation_count=len(joined),
        annualization_days=annualization_days,
        source=source,
        return_basis=return_basis,
    )


def latest_fund_weights(
    weights: pd.DataFrame, fund_id: str
) -> tuple[pd.Timestamp, pd.DataFrame]:
    """Return the complete latest target vector for one fund."""
    selected = weights.loc[weights["fund_id"].eq(fund_id)].copy()
    if selected.empty:
        raise ValueError(f"No weight history found for {fund_id}")
    latest_date = pd.Timestamp(selected["rebalance_date"].max())
    latest = selected.loc[selected["rebalance_date"].eq(latest_date)].copy()
    latest = latest.loc[latest["target_weight"].gt(1e-10)]
    return latest_date, latest.sort_values("target_weight", ascending=False)


def latest_weight_changes(weights: pd.DataFrame, fund_id: str) -> pd.DataFrame:
    """Compare the last two target vectors without inventing causal explanations."""
    selected = weights.loc[weights["fund_id"].eq(fund_id)].copy()
    dates = sorted(pd.to_datetime(selected["rebalance_date"].unique()))
    if len(dates) < 2:
        raise ValueError(f"At least two rebalances are required for {fund_id}")
    previous_date, latest_date = dates[-2:]
    pivot = (
        selected.loc[selected["rebalance_date"].isin([previous_date, latest_date])]
        .pivot(index="asset", columns="rebalance_date", values="target_weight")
        .fillna(0.0)
    )
    result = pivot.rename(
        columns={previous_date: "previous_weight", latest_date: "latest_weight"}
    ).reset_index()
    result["change"] = result["latest_weight"] - result["previous_weight"]
    result["latest_date"] = latest_date
    result["previous_date"] = previous_date
    return result.sort_values("change", key=lambda values: values.abs(), ascending=False)


def _fund_return_panel(
    fund_returns: pd.DataFrame, fund_ids: list[str]
) -> pd.DataFrame:
    selected = fund_returns.loc[fund_returns["fund_id"].isin(fund_ids)]
    panel = selected.pivot(index="date", columns="fund_id", values="net_return")
    panel = panel.reindex(columns=fund_ids).sort_index().dropna(how="any")
    if panel.empty:
        raise ValueError("Selected funds have no common historical return dates")
    return panel


def _monthly_mix_path(panel: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
    current = target.copy()
    records: list[dict[str, object]] = []
    previous_month: tuple[int, int] | None = None
    for date, asset_returns in panel.iterrows():
        month = (pd.Timestamp(date).year, pd.Timestamp(date).month)
        rebalanced = previous_month is None or month != previous_month
        if rebalanced:
            current = target.copy()
        portfolio_return = float((current * asset_returns).sum())
        records.append(
            {
                "date": pd.Timestamp(date),
                "net_return": portfolio_return,
                "rebalanced": rebalanced,
            }
        )
        ending_values = current * (1 + asset_returns)
        current = ending_values / float(ending_values.sum())
        previous_month = month
    path = pd.DataFrame.from_records(records)
    path["growth_of_1"] = (1 + path["net_return"]).cumprod()
    path["drawdown"] = path["growth_of_1"] / path["growth_of_1"].cummax() - 1
    return path


def _performance(path: pd.DataFrame, annualization_days: int) -> dict[str, float]:
    returns = path["net_return"].astype(float)
    years = len(returns) / annualization_days
    ending = float(path["growth_of_1"].iloc[-1])
    annualized_return = ending ** (1 / years) - 1 if years > 0 else float("nan")
    volatility = float(returns.std(ddof=1) * np.sqrt(annualization_days))
    arithmetic = float(returns.mean() * annualization_days)
    sharpe = arithmetic / volatility if volatility > 0 else float("nan")
    return {
        "ending_growth_of_1": ending,
        "annualized_return": annualized_return,
        "annualized_volatility": volatility,
        "sharpe_ratio": sharpe,
        "maximum_drawdown": float(path["drawdown"].min()),
    }


def allocation_benchmark_evidence(
    artifacts: AppArtifacts,
    allocation_path: pd.DataFrame,
    equal_allocation_path: pd.DataFrame,
    benchmark_option: str,
    allocation_annualization_days: int,
) -> AllocationBenchmarkEvidence:
    """Align a hypothetical allocation with its selected comparison reference."""
    if benchmark_option not in ALLOCATION_BENCHMARK_LABELS:
        raise ValueError(f"Unknown allocation benchmark: {benchmark_option}")
    required = {"date", "net_return"}
    if not required.issubset(allocation_path.columns):
        raise ValueError("Allocation path is missing date or return fields")
    allocation = allocation_path[["date", "net_return"]].rename(
        columns={"net_return": "allocation_return"}
    )
    if benchmark_option == "equal_selected_funds":
        if not required.issubset(equal_allocation_path.columns):
            raise ValueError("Equal-allocation path is missing date or return fields")
        benchmark = equal_allocation_path[["date", "net_return"]].rename(
            columns={"net_return": "benchmark_return"}
        )
        annualization_days = allocation_annualization_days
        source = "Stockist Funds selected-fund return histories"
        return_basis = (
            "Same selected funds, equally allocated and reset monthly; underlying "
            "fund returns include their internal trading costs"
        )
    else:
        external = artifacts.external_benchmarks.loc[
            artifacts.external_benchmarks["benchmark_id"].eq(benchmark_option)
        ]
        if external.empty:
            raise ValueError(
                f"No external observations found for {benchmark_option}"
            )
        benchmark = external[["date", "daily_return"]].rename(
            columns={"daily_return": "benchmark_return"}
        )
        annualization_days = 252
        source = str(external["source"].iloc[0])
        return_basis = str(external["return_basis"].iloc[0])
    joined = (
        allocation.merge(benchmark, on="date", how="inner", validate="one_to_one")
        .dropna()
        .sort_values("date")
        .reset_index(drop=True)
    )
    if len(joined) < 2:
        raise ValueError(
            "Allocation and benchmark do not have enough common observations"
        )
    for prefix in ("allocation", "benchmark"):
        growth = (1 + joined[f"{prefix}_return"]).cumprod()
        joined[f"{prefix}_growth_of_1"] = growth
        joined[f"{prefix}_drawdown"] = growth / growth.cummax() - 1
    allocation_metrics = _performance(
        joined.rename(
            columns={
                "allocation_return": "net_return",
                "allocation_growth_of_1": "growth_of_1",
                "allocation_drawdown": "drawdown",
            }
        ),
        annualization_days,
    )
    benchmark_metrics = _performance(
        joined.rename(
            columns={
                "benchmark_return": "net_return",
                "benchmark_growth_of_1": "growth_of_1",
                "benchmark_drawdown": "drawdown",
            }
        ),
        annualization_days,
    )
    active_returns = joined["allocation_return"] - joined["benchmark_return"]
    tracking_error = float(
        active_returns.std(ddof=1) * np.sqrt(annualization_days)
    )
    return AllocationBenchmarkEvidence(
        path=joined,
        benchmark_id=benchmark_option,
        benchmark_label=ALLOCATION_BENCHMARK_LABELS[benchmark_option],
        allocation_metrics=allocation_metrics,
        benchmark_metrics=benchmark_metrics,
        annualized_return_difference=(
            allocation_metrics["annualized_return"]
            - benchmark_metrics["annualized_return"]
        ),
        tracking_error=tracking_error,
        first_date=pd.Timestamp(joined["date"].min()),
        last_date=pd.Timestamp(joined["date"].max()),
        observation_count=len(joined),
        annualization_days=annualization_days,
        source=source,
        return_basis=return_basis,
    )


def _latest_exposures(
    artifacts: AppArtifacts, allocations: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame]:
    pieces: list[pd.DataFrame] = []
    for fund_id, fund_allocation in allocations.items():
        _, latest = latest_fund_weights(artifacts.fund_weights, fund_id)
        part = latest[["asset", "asset_class", "target_weight"]].copy()
        part["allocation_weight"] = fund_allocation
        part["look_through_weight"] = part["target_weight"] * fund_allocation
        pieces.append(part)
    combined = pd.concat(pieces, ignore_index=True)
    exposure = (
        combined.groupby(["asset", "asset_class"], as_index=False)["look_through_weight"]
        .sum()
        .sort_values("look_through_weight", ascending=False)
    )
    classes = (
        exposure.groupby("asset_class", as_index=False)["look_through_weight"]
        .sum()
        .sort_values("look_through_weight", ascending=False)
    )
    return exposure, classes


def _pairwise_overlap(
    artifacts: AppArtifacts, fund_ids: list[str]
) -> pd.DataFrame:
    vectors: dict[str, pd.Series] = {}
    names = artifacts.performance.set_index("fund_id")["fund_name"].map(stockist_name)
    for fund_id in fund_ids:
        _, latest = latest_fund_weights(artifacts.fund_weights, fund_id)
        vectors[fund_id] = latest.set_index("asset")["target_weight"]
    records: list[dict[str, object]] = []
    for left, right in combinations(fund_ids, 2):
        assets = vectors[left].index.union(vectors[right].index)
        overlap = np.minimum(
            vectors[left].reindex(assets, fill_value=0.0),
            vectors[right].reindex(assets, fill_value=0.0),
        ).sum()
        records.append(
            {
                "fund_a": names[left],
                "fund_b": names[right],
                "holdings_overlap": float(overlap),
            }
        )
    return pd.DataFrame.from_records(records)


def allocation_analysis(
    artifacts: AppArtifacts, allocations: dict[str, float]
) -> AllocationAnalysis:
    """Combine cost-adjusted fund paths with monthly fund-level rebalancing."""
    target = pd.Series(allocations, dtype="float64")
    if target.empty or target.lt(0).any() or not np.isclose(target.sum(), 1.0):
        raise ValueError("Fund allocations must be nonnegative and sum to 100%")
    valid = set(artifacts.performance["fund_id"])
    if not set(target.index).issubset(valid):
        raise ValueError("Allocation contains an unknown fund identifier")
    panel = _fund_return_panel(artifacts.fund_returns, list(target.index))
    families = artifacts.performance.set_index("fund_id").loc[
        target.index, "asset_family"
    ]
    annualization_days = 365 if families.eq("crypto").all() else 252
    path = _monthly_mix_path(panel, target)
    exposure, classes = _latest_exposures(artifacts, target)
    correlation = panel.corr()
    labels = artifacts.performance.set_index("fund_id")["fund_name"].map(stockist_name)
    correlation = correlation.rename(index=labels, columns=labels)
    return AllocationAnalysis(
        path=path,
        metrics=_performance(path, annualization_days),
        underlying_exposure=exposure,
        asset_class_exposure=classes,
        correlation=correlation,
        overlap=_pairwise_overlap(artifacts, list(target.index)),
        annualization_days=annualization_days,
    )


def coverage_label(row: pd.Series) -> str:
    """Translate predeclared audit bands into text without implying accuracy."""
    if not bool(row.get("has_news", False)) or int(row.get("headline_count", 0)) == 0:
        return "No news"
    confidence = float(row["coverage_confidence"])
    if confidence < 0.25:
        return "Thin evidence"
    if confidence >= 0.75:
        return "Broad evidence"
    return "Mixed evidence"


__all__ = [
    "ALLOCATION_BENCHMARK_LABELS",
    "BENCHMARK_LABELS",
    "FAMILY_LABELS",
    "FAMILY_PURPOSE",
    "FAMILY_RISKS",
    "METHOD_LABELS",
    "METHOD_OBJECTIVES",
    "METHOD_SUMMARIES",
    "SECTOR_LABELS",
    "AllocationAnalysis",
    "AllocationBenchmarkEvidence",
    "BenchmarkEvidence",
    "allocation_analysis",
    "allocation_benchmark_evidence",
    "benchmark_evidence",
    "comparison_table",
    "coverage_label",
    "fund_catalog",
    "latest_fund_weights",
    "latest_weight_changes",
    "sector_allocation",
    "stockist_name",
]
