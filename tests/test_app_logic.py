"""Pure artifact and allocation tests for the Stockist Funds app."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.allocation_history import allocation_history
from src.app_data import load_app_artifacts
from src.app_logic import (
    allocation_analysis,
    allocation_benchmark_evidence,
    benchmark_evidence,
    coverage_label,
    fund_catalog,
    latest_fund_weights,
    latest_weight_changes,
    sector_allocation,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_app_artifact_contract_and_fund_catalog() -> None:
    artifacts = load_app_artifacts(PROJECT_ROOT)
    catalog = fund_catalog(artifacts)

    assert len(artifacts.health) == 17
    assert artifacts.health["status"].eq("Ready").all()
    assert len(artifacts.market_sentiment) == 1006
    assert artifacts.market_sentiment["ticker_count"].eq(50).all()
    assert catalog["fund_id"].nunique() == 15
    assert catalog["display_name"].str.startswith("Stockist ").all()
    assert set(catalog["asset_family"]) == {"equity", "crypto", "combined"}
    assert set(catalog["method"]) == {
        "equal_weight",
        "minimum_variance",
        "risk_parity",
        "maximum_sharpe",
        "hierarchical_risk_parity",
    }


def test_benchmark_evidence_supports_strategy_spy_and_oneq_options() -> None:
    artifacts = load_app_artifacts(PROJECT_ROOT)

    own_benchmark = benchmark_evidence(
        artifacts, "equity_equal_weight", "same_family_equal_weight"
    )
    spy = benchmark_evidence(
        artifacts, "equity_minimum_variance", "sp500_spy"
    )
    oneq = benchmark_evidence(
        artifacts, "equity_minimum_variance", "nasdaq_composite_oneq"
    )

    assert own_benchmark.annualized_return_difference == pytest.approx(0)
    assert own_benchmark.benchmark_label == "Stockist Equity Equal Weight"
    assert spy.benchmark_label == "S&P 500 (SPY total-return proxy)"
    assert oneq.benchmark_label == "Nasdaq Composite (ONEQ total-return proxy)"
    assert spy.first_date == pd.Timestamp("2021-01-04")
    assert spy.last_date == pd.Timestamp("2023-12-29")
    assert spy.observation_count == 753
    assert spy.annualization_days == 252
    assert spy.path[["fund_growth_of_1", "benchmark_growth_of_1"]].gt(0).all().all()


def test_hypothetical_allocation_is_monthly_complete_and_look_through() -> None:
    artifacts = load_app_artifacts(PROJECT_ROOT)
    allocations = {
        "equity_equal_weight": 0.34,
        "crypto_equal_weight": 0.33,
        "combined_equal_weight": 0.33,
    }
    result = allocation_analysis(artifacts, allocations)

    assert result.annualization_days == 252
    assert result.path["date"].is_monotonic_increasing
    assert result.path["growth_of_1"].gt(0).all()
    assert np.isfinite(list(result.metrics.values())).all()
    assert result.underlying_exposure["look_through_weight"].sum() == pytest.approx(1)
    assert result.asset_class_exposure["look_through_weight"].sum() == pytest.approx(1)
    assert len(result.overlap) == 3
    assert result.overlap["holdings_overlap"].between(0, 1).all()
    assert np.allclose(np.diag(result.correlation), 1)


def test_allocation_benchmark_supports_equal_spy_and_oneq_on_common_dates() -> None:
    artifacts = load_app_artifacts(PROJECT_ROOT)
    allocations = {
        "equity_equal_weight": 0.50,
        "crypto_equal_weight": 0.30,
        "combined_equal_weight": 0.20,
    }
    selected = allocation_analysis(artifacts, allocations)
    equal = allocation_analysis(
        artifacts,
        {fund_id: 1 / len(allocations) for fund_id in allocations},
    )

    equal_reference = allocation_benchmark_evidence(
        artifacts,
        selected.path,
        equal.path,
        "equal_selected_funds",
        selected.annualization_days,
    )
    spy = allocation_benchmark_evidence(
        artifacts,
        selected.path,
        equal.path,
        "sp500_spy",
        selected.annualization_days,
    )
    oneq = allocation_benchmark_evidence(
        artifacts,
        selected.path,
        equal.path,
        "nasdaq_composite_oneq",
        selected.annualization_days,
    )

    assert equal_reference.benchmark_label == "Equal allocation across selected funds"
    assert spy.benchmark_label == "S&P 500 (SPY total-return proxy)"
    assert oneq.benchmark_label == "Nasdaq Composite (ONEQ total-return proxy)"
    assert spy.first_date == oneq.first_date == pd.Timestamp("2021-01-04")
    assert spy.last_date == oneq.last_date == pd.Timestamp("2023-12-29")
    assert spy.observation_count == oneq.observation_count == 753
    assert spy.annualization_days == oneq.annualization_days == 252
    assert spy.path[
        ["allocation_growth_of_1", "benchmark_growth_of_1"]
    ].gt(0).all().all()
    assert np.isfinite(spy.annualized_return_difference)
    assert spy.tracking_error > 0


def test_latest_holdings_and_changes_remain_exact() -> None:
    artifacts = load_app_artifacts(PROJECT_ROOT)
    latest_date, latest = latest_fund_weights(
        artifacts.fund_weights, "combined_risk_parity"
    )
    changes = latest_weight_changes(
        artifacts.fund_weights, "combined_risk_parity"
    )

    assert latest_date == pd.Timestamp("2023-12-01")
    assert latest["target_weight"].sum() == pytest.approx(1)
    assert not changes.empty
    assert np.isclose(changes["change"].sum(), 0)


@pytest.mark.parametrize(
    ("fund_id", "expected_sector_count", "expected_crypto"),
    [
        ("equity_equal_weight", 10, False),
        ("crypto_equal_weight", 1, True),
        ("combined_equal_weight", 11, True),
    ],
)
def test_latest_sector_allocation_uses_supplied_equity_map_and_crypto_bucket(
    fund_id: str, expected_sector_count: int, expected_crypto: bool
) -> None:
    artifacts = load_app_artifacts(PROJECT_ROOT)
    _, latest = latest_fund_weights(artifacts.fund_weights, fund_id)

    allocation = sector_allocation(latest, artifacts.fusion_weights)

    assert len(allocation) == expected_sector_count
    assert allocation["target_weight"].sum() == pytest.approx(1)
    assert allocation["target_weight"].gt(0).all()
    assert allocation["sector_label"].notna().all()
    assert bool(allocation["sector"].eq("Crypto").any()) is expected_crypto


@pytest.mark.parametrize(
    ("fund_id", "expected_basis", "expected_category_count"),
    [
        ("equity_risk_parity", "sector", 10),
        ("crypto_risk_parity", "cryptoasset", 10),
        ("combined_risk_parity", "sector", 11),
    ],
)
def test_allocation_history_is_complete_for_every_fund_family(
    fund_id: str, expected_basis: str, expected_category_count: int
) -> None:
    artifacts = load_app_artifacts(PROJECT_ROOT)

    history = allocation_history(
        artifacts.fund_weights,
        fund_id,
        artifacts.fusion_weights,
    )

    totals = history.data.groupby("rebalance_date")["target_weight"].sum()
    assert history.basis == expected_basis
    assert history.data["category"].nunique() == expected_category_count
    assert history.data["category_label"].notna().all()
    assert len(totals) == 36
    assert np.allclose(totals, 1)


@pytest.mark.parametrize(
    ("has_news", "headline_count", "confidence", "expected"),
    [
        (False, 0, 0.0, "No news"),
        (True, 1, 0.20, "Thin evidence"),
        (True, 3, 0.50, "Mixed evidence"),
        (True, 8, 0.80, "Broad evidence"),
    ],
)
def test_coverage_labels_are_textual_and_predeclared(
    has_news: bool, headline_count: int, confidence: float, expected: str
) -> None:
    row = pd.Series(
        {
            "has_news": has_news,
            "headline_count": headline_count,
            "coverage_confidence": confidence,
        }
    )
    assert coverage_label(row) == expected
