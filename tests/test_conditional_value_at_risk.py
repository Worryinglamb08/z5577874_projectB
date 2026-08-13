"""Tests for the isolated historical minimum-CVaR prototype."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.conditional_value_at_risk import minimum_cvar
from src.config import ModelConfig
from src.portfolios import FamilyPanel, oos_backtest, solve_weights


def _config(**changes: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "equity_window": 20,
        "crypto_window": 20,
        "combined_window": 20,
        "equity_asset_cap": 1.0,
        "crypto_asset_cap": 1.0,
        "combined_crypto_sleeve_cap": 0.40,
        "cvar_confidence": 0.90,
    }
    defaults.update(changes)
    return ModelConfig(**defaults)


def test_minimum_cvar_avoids_the_asset_with_worse_tail_losses() -> None:
    dates = pd.bdate_range("2022-01-03", periods=40)
    history = pd.DataFrame(
        {
            "Stable": np.repeat(0.001, len(dates)),
            "Crashy": np.r_[np.repeat(0.004, 36), np.repeat(-0.20, 4)],
        },
        index=dates,
    )
    classes = pd.Series("equity", index=history.columns, dtype="string")

    result = minimum_cvar(history, classes, "equity", _config())

    assert result.weights.sum() == pytest.approx(1)
    assert result.weights["Stable"] == pytest.approx(1)
    assert result.weights["Crashy"] == pytest.approx(0)
    assert result.cvar == pytest.approx(-0.001)


def test_minimum_cvar_respects_asset_and_combined_crypto_caps() -> None:
    dates = pd.bdate_range("2022-01-03", periods=40)
    history = pd.DataFrame(
        {
            "E1": np.repeat(-0.004, len(dates)),
            "E2": np.repeat(-0.006, len(dates)),
            "C1": np.repeat(0.002, len(dates)),
        },
        index=dates,
    )
    classes = pd.Series(
        ["equity", "equity", "crypto"],
        index=history.columns,
        dtype="string",
    )
    config = _config(
        equity_asset_cap=0.60,
        crypto_asset_cap=0.70,
        combined_crypto_sleeve_cap=0.30,
    )

    result = minimum_cvar(history, classes, "combined", config)

    assert result.weights.sum() == pytest.approx(1)
    assert result.weights["C1"] == pytest.approx(0.30)
    assert result.weights.max() <= 0.60 + 1e-9


def test_cvar_solver_diagnostics_are_exposed_by_portfolio_engine() -> None:
    dates = pd.bdate_range("2022-01-03", periods=40)
    time = np.arange(len(dates), dtype=float)
    history = pd.DataFrame(
        {
            "A": 0.001 + 0.003 * np.sin(time),
            "B": 0.001 + 0.005 * np.cos(time),
        },
        index=dates,
    )
    classes = pd.Series("equity", index=history.columns, dtype="string")

    solution = solve_weights(
        history,
        classes,
        "equity",
        "conditional_value_at_risk",
        252,
        _config(),
    )

    assert solution.weights.sum() == pytest.approx(1)
    assert solution.diagnostics["cvar_confidence"] == pytest.approx(0.90)
    assert np.isfinite(solution.diagnostics["estimated_daily_cvar"])
    assert solution.diagnostics["tail_scenario_count"] >= 4


def test_cvar_solution_is_deterministic_for_identical_history() -> None:
    dates = pd.bdate_range("2022-01-03", periods=40)
    generator = np.random.default_rng(5545)
    history = pd.DataFrame(
        generator.normal(0.0005, 0.01, size=(len(dates), 4)),
        index=dates,
        columns=["A", "B", "C", "D"],
    )
    classes = pd.Series("equity", index=history.columns, dtype="string")
    config = _config(equity_asset_cap=0.50)

    first = minimum_cvar(history, classes, "equity", config)
    second = minimum_cvar(history, classes, "equity", config)

    assert np.array_equal(first.weights.to_numpy(), second.weights.to_numpy())
    assert first.cvar == second.cvar


def test_cvar_backtest_uses_only_prior_returns() -> None:
    dates = pd.bdate_range("2022-01-03", periods=90)
    time = np.arange(len(dates), dtype=float)
    returns = pd.DataFrame(
        {
            "A": 0.0005 + 0.006 * np.sin(time * 0.31),
            "B": 0.0004 + 0.008 * np.cos(time * 0.27),
        },
        index=dates,
    )
    classes = pd.Series("equity", index=returns.columns, dtype="string")
    config = _config()
    panel = FamilyPanel("equity", returns, classes, 252, 20)

    base = oos_backtest(panel, "conditional_value_at_risk", config=config)
    first_live = base.fund_weights["rebalance_date"].min()
    changed = returns.copy()
    changed.loc[changed.index >= first_live, "B"] = -0.50
    changed_result = oos_backtest(
        FamilyPanel("equity", changed, classes, 252, 20),
        "conditional_value_at_risk",
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
