"""Tests for the experimental PCA effective-number-of-bets rule."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.config import ModelConfig
from src.effective_bets import (
    EffectiveBetsValidationError,
    effective_number_of_bets,
    pca_bet_distribution,
)
from src.portfolios import FamilyPanel, oos_backtest, solve_weights


def _config(**changes: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "equity_window": 10,
        "crypto_window": 10,
        "combined_window": 10,
        "equity_asset_cap": 1.0,
        "crypto_asset_cap": 1.0,
        "combined_crypto_sleeve_cap": 0.5,
    }
    defaults.update(changes)
    return ModelConfig(**defaults)


def _returns() -> tuple[pd.DataFrame, pd.Series]:
    dates = pd.bdate_range("2022-01-03", periods=80)
    time = np.arange(len(dates), dtype=float)
    frame = pd.DataFrame(
        {
            "LOW": 0.0004 + 0.003 * np.sin(time * 0.31),
            "MID": 0.0007 + 0.008 * np.cos(time * 0.23),
            "HIGH": 0.0010 + 0.018 * np.sin(time * 0.47),
        },
        index=dates,
    )
    classes = pd.Series("equity", index=frame.columns, dtype="string")
    return frame, classes


def test_effective_bets_has_known_identity_covariance_limits() -> None:
    covariance = np.eye(3)

    equal = pca_bet_distribution(np.repeat(1 / 3, 3), covariance)
    concentrated = effective_number_of_bets(np.array([1.0, 0.0, 0.0]), covariance)

    assert equal == pytest.approx(np.repeat(1 / 3, 3))
    assert effective_number_of_bets(np.repeat(1 / 3, 3), covariance) == pytest.approx(3)
    assert concentrated == pytest.approx(1)


def test_bet_distribution_reconstructs_total_variance() -> None:
    covariance = np.array(
        [[0.04, 0.01, 0.00], [0.01, 0.09, 0.02], [0.00, 0.02, 0.16]]
    )
    weights = np.array([0.5, 0.3, 0.2])

    distribution = pca_bet_distribution(weights, covariance)

    assert distribution.sum() == pytest.approx(1)
    assert (distribution >= 0).all()
    assert 1 <= effective_number_of_bets(weights, covariance) <= 3


def test_invalid_covariance_is_rejected() -> None:
    with pytest.raises(EffectiveBetsValidationError, match="positive definite"):
        effective_number_of_bets(
            np.array([0.5, 0.5]), np.array([[1.0, 1.0], [1.0, 1.0]])
        )


def test_effective_bets_solver_is_valid_and_improves_factor_diversification() -> None:
    returns, classes = _returns()
    config = _config()

    equal = solve_weights(returns, classes, "equity", "equal_weight", 252, config)
    diversified = solve_weights(
        returns, classes, "equity", "effective_bets", 252, config
    )

    assert diversified.weights.sum() == pytest.approx(1, abs=1e-7)
    assert diversified.weights.min() >= -1e-7
    assert diversified.diagnostics["solver_success"]
    assert diversified.diagnostics["effective_number_of_bets"] >= (
        equal.diagnostics["effective_number_of_bets"] - 1e-8
    )


def test_effective_bets_backtest_uses_only_prior_returns() -> None:
    returns, classes = _returns()
    config = _config()
    panel = FamilyPanel("equity", returns, classes, 252, 10)

    base = oos_backtest(panel, "effective_bets", config=config)
    first_live = base.fund_weights["rebalance_date"].min()
    changed = returns.copy()
    changed.loc[changed.index >= first_live, "HIGH"] = 0.50
    changed_result = oos_backtest(
        FamilyPanel("equity", changed, classes, 252, 10),
        "effective_bets",
        config=config,
    )

    first_weights = base.fund_weights.loc[
        base.fund_weights["rebalance_date"].eq(first_live), "target_weight"
    ].to_numpy()
    changed_weights = changed_result.fund_weights.loc[
        changed_result.fund_weights["rebalance_date"].eq(first_live),
        "target_weight",
    ].to_numpy()
    assert np.allclose(first_weights, changed_weights, atol=1e-12)
