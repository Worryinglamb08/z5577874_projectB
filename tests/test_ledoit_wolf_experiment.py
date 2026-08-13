"""Tests for the isolated Ledoit-Wolf covariance robustness prototype."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.config import ModelConfig
from src.ledoit_wolf_experiment import PROTOTYPE_SPECS
from src.portfolios import (
    FamilyPanel,
    annualized_moments,
    oos_backtest,
    solve_weights,
)


def _config(**changes: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "equity_window": 20,
        "crypto_window": 20,
        "combined_window": 20,
        "equity_asset_cap": 1.0,
        "crypto_asset_cap": 1.0,
        "combined_crypto_sleeve_cap": 0.5,
    }
    defaults.update(changes)
    return ModelConfig(**defaults)


def _correlated_returns() -> tuple[pd.DataFrame, pd.Series]:
    dates = pd.bdate_range("2022-01-03", periods=100)
    generator = np.random.default_rng(55_45)
    common = generator.normal(0.0004, 0.01, size=(len(dates), 1))
    loadings = np.linspace(0.65, 1.25, 12).reshape(1, -1)
    noise = generator.normal(0, 0.002, size=(len(dates), 12))
    values = common * loadings + noise
    frame = pd.DataFrame(
        values,
        index=dates,
        columns=[f"A{index:02d}" for index in range(values.shape[1])],
    )
    classes = pd.Series("equity", index=frame.columns, dtype="string")
    return frame, classes


def test_crypto_extension_is_limited_to_hrp() -> None:
    crypto_specs = [spec for spec in PROTOTYPE_SPECS if spec[0] == "crypto"]

    assert crypto_specs == [("crypto", "hierarchical_risk_parity")]


def test_ledoit_wolf_is_positive_definite_and_improves_conditioning() -> None:
    returns, _ = _correlated_returns()
    history = returns.iloc[:20]
    config = _config()

    _, sample, sample_diagnostics = annualized_moments(
        history,
        252,
        config,
        covariance_estimator="sample_ridge",
    )
    _, shrunk, shrunk_diagnostics = annualized_moments(
        history,
        252,
        config,
        covariance_estimator="ledoit_wolf",
    )

    assert np.linalg.eigvalsh(shrunk).min() > 0
    assert 0 <= shrunk_diagnostics["covariance_shrinkage"] <= 1
    assert (
        shrunk_diagnostics["covariance_condition_number"]
        < (sample_diagnostics["covariance_condition_number"])
    )
    assert not np.allclose(sample, shrunk)


@pytest.mark.parametrize(
    "method",
    [
        "minimum_variance",
        "risk_parity",
        "maximum_sharpe",
        "hierarchical_risk_parity",
    ],
)
def test_ledoit_wolf_produces_valid_weights_for_each_tested_method(
    method: str,
) -> None:
    returns, classes = _correlated_returns()

    solution = solve_weights(
        returns.iloc[:40],
        classes,
        "equity",
        method,
        252,
        _config(),
        covariance_estimator="ledoit_wolf",
    )

    assert solution.weights.sum() == pytest.approx(1, abs=1e-7)
    assert solution.weights.min() >= -1e-7
    assert solution.diagnostics["covariance_estimator"] == "ledoit_wolf"
    assert solution.diagnostics["solver_success"]


def test_default_sample_path_is_identical_to_explicit_sample_estimator() -> None:
    returns, classes = _correlated_returns()
    history = returns.iloc[:40]
    config = _config()

    default = solve_weights(history, classes, "equity", "minimum_variance", 252, config)
    explicit = solve_weights(
        history,
        classes,
        "equity",
        "minimum_variance",
        252,
        config,
        covariance_estimator="sample_ridge",
    )

    assert np.array_equal(default.weights.to_numpy(), explicit.weights.to_numpy())
    assert default.diagnostics == explicit.diagnostics


def test_ledoit_wolf_backtest_is_prior_only_and_reproducible() -> None:
    returns, classes = _correlated_returns()
    config = _config(equity_window=20)
    panel = FamilyPanel("equity", returns, classes, 252, 20)

    base = oos_backtest(
        panel,
        "minimum_variance",
        config=config,
        covariance_estimator="ledoit_wolf",
    )
    repeated = oos_backtest(
        panel,
        "minimum_variance",
        config=config,
        covariance_estimator="ledoit_wolf",
    )
    first_live = base.fund_weights["rebalance_date"].min()
    changed = returns.copy()
    changed.loc[changed.index >= first_live, "A11"] = 0.50
    changed_result = oos_backtest(
        FamilyPanel("equity", changed, classes, 252, 20),
        "minimum_variance",
        config=config,
        covariance_estimator="ledoit_wolf",
    )

    pd.testing.assert_frame_equal(base.fund_returns, repeated.fund_returns)
    pd.testing.assert_frame_equal(base.fund_weights, repeated.fund_weights)
    pd.testing.assert_frame_equal(base.diagnostics, repeated.diagnostics)
    first_weights = base.fund_weights.loc[
        base.fund_weights["rebalance_date"].eq(first_live), "target_weight"
    ].to_numpy()
    changed_weights = changed_result.fund_weights.loc[
        changed_result.fund_weights["rebalance_date"].eq(first_live),
        "target_weight",
    ].to_numpy()
    assert np.allclose(first_weights, changed_weights, atol=1e-12)
    assert (
        base.diagnostics.iloc[0]["estimation_end"]
        < base.diagnostics.iloc[0]["first_held_return_date"]
    )
