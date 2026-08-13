"""Tests for the experimental Hierarchical Risk Parity rule."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.config import ModelConfig
from src.hierarchical_risk_parity import (
    correlation_distance,
    hierarchical_risk_parity,
)
from src.portfolios import FamilyPanel, oos_backtest, solve_weights


def _config(**changes: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "equity_window": 10,
        "crypto_window": 10,
        "combined_window": 10,
        "equity_asset_cap": 0.60,
        "crypto_asset_cap": 0.60,
        "combined_crypto_sleeve_cap": 0.50,
    }
    defaults.update(changes)
    return ModelConfig(**defaults)


def _returns() -> tuple[pd.DataFrame, pd.Series]:
    dates = pd.bdate_range("2022-01-03", periods=80)
    time = np.arange(len(dates), dtype=float)
    common_a = 0.006 * np.sin(time * 0.21)
    common_b = 0.007 * np.cos(time * 0.19)
    frame = pd.DataFrame(
        {
            "A1": 0.0004 + common_a + 0.001 * np.sin(time * 0.61),
            "A2": 0.0005 + common_a + 0.001 * np.cos(time * 0.53),
            "B1": 0.0006 + common_b + 0.002 * np.sin(time * 0.43),
            "B2": 0.0007 + common_b + 0.002 * np.cos(time * 0.47),
        },
        index=dates,
    )
    classes = pd.Series("equity", index=frame.columns, dtype="string")
    return frame, classes


def test_correlation_distance_has_known_limits() -> None:
    correlation = np.array(
        [[1.0, 1.0, -1.0], [1.0, 1.0, 0.0], [-1.0, 0.0, 1.0]]
    )

    distance = correlation_distance(correlation)

    assert distance[0, 1] == pytest.approx(0)
    assert distance[0, 2] == pytest.approx(1)
    assert distance[1, 2] == pytest.approx(np.sqrt(0.5))


def test_hrp_clusters_correlated_pairs_and_returns_valid_weights() -> None:
    covariance = np.array(
        [
            [0.04, 0.036, 0.000, 0.000],
            [0.036, 0.04, 0.000, 0.000],
            [0.000, 0.000, 0.09, 0.081],
            [0.000, 0.000, 0.081, 0.09],
        ]
    )

    result = hierarchical_risk_parity(covariance, ["A1", "A2", "B1", "B2"])

    assert result.weights.sum() == pytest.approx(1)
    assert result.weights.gt(0).all()
    assert abs(result.ordered_assets.index("A1") - result.ordered_assets.index("A2")) == 1
    assert abs(result.ordered_assets.index("B1") - result.ordered_assets.index("B2")) == 1
    assert result.weights["A1"] == pytest.approx(result.weights["A2"])
    assert result.weights["B1"] == pytest.approx(result.weights["B2"])
    assert result.weights[["A1", "A2"]].sum() > result.weights[["B1", "B2"]].sum()


def test_hrp_solver_projects_raw_weights_into_product_caps() -> None:
    returns, classes = _returns()
    config = _config(equity_asset_cap=0.27)

    solution = solve_weights(
        returns,
        classes,
        "equity",
        "hierarchical_risk_parity",
        252,
        config,
    )

    assert solution.weights.sum() == pytest.approx(1, abs=1e-7)
    assert solution.weights.between(0, 0.27 + 1e-7).all()
    assert solution.diagnostics["constraint_projection_applied"]
    assert solution.diagnostics["projection_l1_distance"] > 0


def test_hrp_is_deterministic_for_identical_inputs() -> None:
    returns, classes = _returns()
    config = _config()

    first = solve_weights(
        returns, classes, "equity", "hierarchical_risk_parity", 252, config
    )
    second = solve_weights(
        returns, classes, "equity", "hierarchical_risk_parity", 252, config
    )

    assert np.array_equal(first.weights.to_numpy(), second.weights.to_numpy())
    assert (
        first.diagnostics["ordered_asset_signature"]
        == second.diagnostics["ordered_asset_signature"]
    )


def test_hrp_backtest_uses_only_prior_returns() -> None:
    returns, classes = _returns()
    config = _config()
    panel = FamilyPanel("equity", returns, classes, 252, 10)

    base = oos_backtest(panel, "hierarchical_risk_parity", config=config)
    first_live = base.fund_weights["rebalance_date"].min()
    changed = returns.copy()
    changed.loc[changed.index >= first_live, "B2"] = 0.50
    changed_result = oos_backtest(
        FamilyPanel("equity", changed, classes, 252, 10),
        "hierarchical_risk_parity",
        config=config,
    )

    first_weights = base.fund_weights.loc[
        base.fund_weights["rebalance_date"].eq(first_live), "target_weight"
    ].to_numpy()
    changed_weights = changed_result.fund_weights.loc[
        changed_result.fund_weights["rebalance_date"].eq(first_live),
        "target_weight",
    ].to_numpy()
    assert np.array_equal(first_weights, changed_weights)
