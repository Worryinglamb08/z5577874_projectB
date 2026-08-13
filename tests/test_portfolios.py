"""Financial-calculation, constraint, timing, and leakage tests for Phase 2."""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_CONFIG, ModelConfig  # noqa: E402
from src.foundation import run_foundation  # noqa: E402
from src.portfolios import (  # noqa: E402
    FamilyPanel,
    build_portfolio_suite,
    monthly_rebalance_dates,
    oos_backtest,
    performance_metrics,
    save_portfolio_outputs,
    solve_weights,
)


def _test_config(**changes: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "equity_window": 5,
        "crypto_window": 5,
        "combined_window": 5,
        "equity_asset_cap": 1.0,
        "crypto_asset_cap": 1.0,
        "combined_crypto_sleeve_cap": 0.5,
        "transaction_cost_bps": 10.0,
    }
    defaults.update(changes)
    return ModelConfig(**defaults)


def _history() -> tuple[pd.DataFrame, pd.Series]:
    dates = pd.bdate_range("2022-01-03", periods=80)
    time = np.arange(len(dates), dtype=float)
    frame = pd.DataFrame(
        {
            "LOW": 0.0005 + 0.003 * np.sin(time),
            "HIGH": 0.0015 + 0.020 * np.cos(time * 0.7),
            "STEADY": 0.0010 + 0.007 * np.sin(time * 0.3),
        },
        index=dates,
    )
    classes = pd.Series("equity", index=frame.columns, dtype="string")
    return frame, classes


def test_default_configuration_retains_approved_primary_values() -> None:
    config = ModelConfig()

    assert config.equity_window == 252
    assert config.crypto_window == 365
    assert config.primary_schedule == "monthly"
    assert config.equity_asset_cap == pytest.approx(0.10)
    assert config.crypto_asset_cap == pytest.approx(0.25)
    assert config.combined_crypto_sleeve_cap == pytest.approx(0.30)
    assert config.transaction_cost_bps == pytest.approx(10.0)
    assert config.methods == (
        "equal_weight",
        "minimum_variance",
        "risk_parity",
        "maximum_sharpe",
        "hierarchical_risk_parity",
    )


def test_monthly_schedule_is_first_observed_date_after_full_window() -> None:
    dates = pd.bdate_range("2022-01-03", "2022-03-31")

    schedule = monthly_rebalance_dates(dates, window=10)

    assert schedule.tolist() == [pd.Timestamp("2022-02-01"), pd.Timestamp("2022-03-01")]


@pytest.mark.parametrize(
    "method",
    [
        "equal_weight",
        "minimum_variance",
        "risk_parity",
        "maximum_sharpe",
        "hierarchical_risk_parity",
    ],
)
def test_all_methods_produce_valid_long_only_fully_invested_weights(method: str) -> None:
    history, classes = _history()
    config = _test_config()

    solution = solve_weights(history, classes, "equity", method, 252, config)

    assert solution.weights.sum() == pytest.approx(1.0, abs=1e-7)
    assert solution.weights.min() >= -1e-7
    assert solution.weights.max() <= 1 + 1e-7
    assert solution.diagnostics["solver_success"]
    assert solution.diagnostics["weight_sum_residual"] <= 1e-7


def test_methods_respond_to_different_objectives() -> None:
    history, classes = _history()
    config = _test_config()

    minimum_variance = solve_weights(
        history, classes, "equity", "minimum_variance", 252, config
    ).weights
    maximum_sharpe = solve_weights(
        history, classes, "equity", "maximum_sharpe", 252, config
    ).weights

    assert minimum_variance["LOW"] > minimum_variance["HIGH"]
    assert not np.allclose(minimum_variance, maximum_sharpe, atol=1e-3)


def test_combined_crypto_sleeve_cap_is_enforced() -> None:
    history, _ = _history()
    history = history.rename(columns={"HIGH": "BTC-USD"})
    classes = pd.Series(
        ["equity", "crypto", "equity"], index=history.columns, dtype="string"
    )
    config = _test_config(combined_crypto_sleeve_cap=0.25)

    solution = solve_weights(
        history, classes, "combined", "maximum_sharpe", 252, config
    )

    assert solution.weights["BTC-USD"] <= 0.25 + 1e-7
    assert solution.diagnostics["crypto_sleeve_weight"] <= 0.25 + 1e-7


def test_backtest_uses_strictly_prior_window_and_future_returns_do_not_change_weight() -> None:
    returns, classes = _history()
    config = _test_config(equity_window=10)
    panel = FamilyPanel("equity", returns, classes, 252, 10)

    base = oos_backtest(panel, "minimum_variance", config=config)
    changed = returns.copy()
    first_live = base.fund_weights["rebalance_date"].min()
    changed.loc[changed.index >= first_live, "HIGH"] = 0.50
    changed_result = oos_backtest(
        FamilyPanel("equity", changed, classes, 252, 10),
        "minimum_variance",
        config=config,
    )
    first_weights = base.fund_weights.loc[
        base.fund_weights["rebalance_date"].eq(first_live), "target_weight"
    ].to_numpy()
    changed_weights = changed_result.fund_weights.loc[
        changed_result.fund_weights["rebalance_date"].eq(first_live), "target_weight"
    ].to_numpy()

    assert np.allclose(first_weights, changed_weights, atol=1e-12)
    first_diagnostic = base.diagnostics.iloc[0]
    assert first_diagnostic["estimation_end"] < first_diagnostic["first_held_return_date"]
    assert first_diagnostic["estimation_observations"] == 10


def test_turnover_uses_drifted_pretrade_weights_and_charges_initial_deployment() -> None:
    dates = pd.to_datetime(
        ["2022-01-30", "2022-01-31", "2022-02-01", "2022-02-02", "2022-03-01"]
    )
    returns = pd.DataFrame(
        {
            "A": [0.00, 0.00, 0.10, 0.00, 0.00],
            "B": [0.00, 0.00, 0.00, 0.00, 0.00],
        },
        index=dates,
    )
    classes = pd.Series("equity", index=returns.columns, dtype="string")
    config = _test_config(
        equity_window=2,
        transaction_cost_bps=10.0,
    )

    result = oos_backtest(
        FamilyPanel("equity", returns, classes, 252, 2),
        "equal_weight",
        config=config,
    )
    rebalances = result.diagnostics.set_index("rebalance_date")

    assert rebalances.loc[pd.Timestamp("2022-02-01"), "turnover"] == pytest.approx(1.0)
    assert rebalances.loc[pd.Timestamp("2022-02-01"), "transaction_cost"] == pytest.approx(
        0.001
    )
    drifted_a = 0.5 * 1.10 / 1.05
    expected_turnover = 0.5 * (abs(0.5 - drifted_a) + abs(0.5 - (1 - drifted_a)))
    assert rebalances.loc[pd.Timestamp("2022-03-01"), "turnover"] == pytest.approx(
        expected_turnover
    )


def test_performance_metrics_match_hand_calculated_growth_and_drawdown() -> None:
    returns = pd.Series([0.10, -0.20, 0.05])

    metrics = performance_metrics(returns, periods_per_year=3)

    assert metrics["ending_growth_of_1"] == pytest.approx(0.924)
    assert metrics["cumulative_return"] == pytest.approx(-0.076)
    assert metrics["annualized_return"] == pytest.approx(-0.076)
    assert metrics["maximum_drawdown"] == pytest.approx(-0.20)


def test_real_data_builds_fifteen_distinct_monthly_funds(
    tmp_path: pathlib.Path,
) -> None:
    foundation = run_foundation(require_reconciliation=True)

    suite = build_portfolio_suite(foundation.returns, DEFAULT_CONFIG)
    paths = save_portfolio_outputs(
        suite,
        data_dir=tmp_path / "data",
        tables_dir=tmp_path / "tables",
    )

    assert suite.performance_metrics["fund_id"].nunique() == 15
    assert len(suite.rebalance_diagnostics) == 540
    assert suite.rebalance_diagnostics["solver_success"].all()
    assert (
        suite.rebalance_diagnostics["estimation_end"]
        < suite.rebalance_diagnostics["first_held_return_date"]
    ).all()
    assert suite.method_distinctness["economically_distinct"].all()
    assert suite.performance_metrics["annualized_return"].notna().all()
    assert suite.performance_metrics["maximum_drawdown"].between(-1, 0).all()
    assert set(suite.performance_metrics["annualization_days"]) == {252, 365}
    weight_sums = suite.fund_weights.groupby(
        ["fund_id", "rebalance_date"]
    )["target_weight"].sum()
    assert np.allclose(weight_sums, 1.0, atol=DEFAULT_CONFIG.weight_tolerance)
    assert set(path.name for path in paths) == {
        "fund_returns.csv",
        "fund_weights.csv",
        "performance_metrics.csv",
        "rebalance_diagnostics.csv",
        "method_distinctness.csv",
        "fund_fact_sheets.csv",
        "model_configuration.csv",
        "portfolio_validation_summary.csv",
    }
