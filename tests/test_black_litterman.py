"""Tests for the isolated Risk-Parity Black-Litterman prototype."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.black_litterman import (
    black_litterman_posterior_returns,
    build_black_litterman_allocation,
    sector_basket_view_matrix,
)
from src.config import ModelConfig


def _config(**changes: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "equity_asset_cap": 0.60,
        "black_litterman_risk_aversion": 2.5,
        "black_litterman_view_scale_annual": 0.02,
    }
    defaults.update(changes)
    return ModelConfig(**defaults)


def test_sector_basket_views_are_complete_and_nonoverlapping() -> None:
    sectors = pd.Series({"A1": "A", "A2": "A", "B1": "B", "B2": "B"})

    views = sector_basket_view_matrix(sectors)

    assert list(views.index) == ["A", "B"]
    assert np.allclose(views.sum(axis=1), 1)
    assert np.allclose((views > 0).sum(axis=0), 1)
    assert views.loc["A", ["A1", "A2"]].sum() == pytest.approx(1)
    assert views.loc["A", ["B1", "B2"]].sum() == pytest.approx(0)


def test_posterior_moves_toward_a_confident_relative_view() -> None:
    covariance = np.diag([0.04, 0.04])
    prior = np.array([0.05, 0.05])
    views = np.array([[1.0, -1.0]])

    low, _ = black_litterman_posterior_returns(
        prior, covariance, views, np.array([0.10]), np.array([0.20]), tau=0.05
    )
    high, _ = black_litterman_posterior_returns(
        prior, covariance, views, np.array([0.10]), np.array([0.80]), tau=0.05
    )

    assert 0 < low[0] - low[1] < high[0] - high[1] < 0.10


def test_no_active_view_recovers_prior_returns() -> None:
    covariance = np.diag([0.04, 0.09])
    prior = np.array([0.03, 0.04])

    posterior, omega = black_litterman_posterior_returns(
        prior,
        covariance,
        np.empty((0, 2)),
        np.empty(0),
        np.empty(0),
        tau=0.05,
    )

    assert np.array_equal(posterior, prior)
    assert len(omega) == 0


def test_allocation_is_valid_and_rewards_positive_sector_view() -> None:
    assets = pd.Index(["A1", "A2", "B1", "B2"])
    prior = pd.Series(0.25, index=assets)
    covariance = np.diag([0.04, 0.04, 0.04, 0.04])
    sectors = pd.Series(["A", "A", "B", "B"], index=assets)
    signal = pd.Series({"A": 0.30, "B": -0.20})
    confidence = pd.Series({"A": 0.80, "B": 0.80})

    allocation = build_black_litterman_allocation(
        prior,
        covariance,
        sectors,
        signal,
        confidence,
        view_scale_annual=0.02,
        config=_config(),
    )

    assert allocation.weights.sum() == pytest.approx(1, abs=1e-8)
    assert allocation.weights.between(0, 0.60 + 1e-8).all()
    assert allocation.weights[["A1", "A2"]].sum() > 0.50
    assert allocation.diagnostics["active_view_count"] == 2


def test_future_signal_cannot_change_an_earlier_allocation() -> None:
    assets = pd.Index(["A1", "A2", "B1", "B2"])
    prior = pd.Series(0.25, index=assets)
    covariance = np.diag([0.04, 0.04, 0.04, 0.04])
    sectors = pd.Series(["A", "A", "B", "B"], index=assets)
    dated_signal = pd.DataFrame(
        {"A": [0.20, -0.90], "B": [-0.10, 0.90]},
        index=pd.to_datetime(["2022-01-03", "2022-01-04"]),
    )
    confidence = pd.Series({"A": 0.75, "B": 0.75})

    original = build_black_litterman_allocation(
        prior,
        covariance,
        sectors,
        dated_signal.loc[pd.Timestamp("2022-01-03")],
        confidence,
        view_scale_annual=0.02,
        config=_config(),
    )
    changed = dated_signal.copy()
    changed.loc[pd.Timestamp("2022-01-04")] = [100.0, -100.0]
    repeated = build_black_litterman_allocation(
        prior,
        covariance,
        sectors,
        changed.loc[pd.Timestamp("2022-01-03")],
        confidence,
        view_scale_annual=0.02,
        config=_config(),
    )

    assert np.allclose(original.weights, repeated.weights, atol=1e-12)
