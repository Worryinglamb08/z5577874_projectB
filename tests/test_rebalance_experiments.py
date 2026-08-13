"""Controlled-schedule, cost, timing, and real-data Phase 3 tests."""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_CONFIG, ModelConfig  # noqa: E402
from src.foundation import run_foundation  # noqa: E402
from src.portfolios import (  # noqa: E402
    FamilyPanel,
    build_portfolio_suite,
    oos_backtest,
    rebalance_dates,
)
from src.rebalance_experiments import (  # noqa: E402
    build_rebalance_experiments,
    save_rebalance_experiment_outputs,
)


def _config(**changes: object) -> ModelConfig:
    defaults: dict[str, object] = {
        "equity_window": 5,
        "crypto_window": 5,
        "combined_window": 5,
        "equity_asset_cap": 1.0,
        "crypto_asset_cap": 1.0,
        "combined_crypto_sleeve_cap": 0.5,
    }
    defaults.update(changes)
    return ModelConfig(**defaults)


def _returns() -> tuple[pd.DataFrame, pd.Series]:
    dates = pd.bdate_range("2022-01-03", periods=50)
    time = np.arange(len(dates), dtype=float)
    returns = pd.DataFrame(
        {
            "A": 0.0005 + 0.005 * np.sin(time),
            "B": 0.0010 + 0.010 * np.cos(time * 0.4),
        },
        index=dates,
    )
    classes = pd.Series("equity", index=returns.columns, dtype="string")
    return returns, classes


def test_fixed_observation_schedules_share_the_same_first_live_date() -> None:
    returns, _ = _returns()
    config = _config()

    schedules = {
        name: rebalance_dates(returns.index, 5, name, config)
        for name in ("daily", "weekly", "biweekly")
    }

    assert {dates[0] for dates in schedules.values()} == {returns.index[5]}
    assert len(schedules["daily"]) > len(schedules["weekly"]) > len(
        schedules["biweekly"]
    )
    assert np.diff(returns.index.get_indexer(schedules["weekly"])).tolist() == [5] * 8
    assert np.diff(returns.index.get_indexer(schedules["biweekly"])).tolist() == [10] * 4


def test_more_frequent_equal_weight_rebalancing_changes_turnover_not_weights() -> None:
    returns, classes = _returns()
    config = _config()
    panel = FamilyPanel("equity", returns, classes, 252, 5)

    daily = oos_backtest(panel, "equal_weight", config=config, rebalance_schedule="daily")
    weekly = oos_backtest(
        panel, "equal_weight", config=config, rebalance_schedule="weekly"
    )

    assert daily.fund_weights["target_weight"].eq(0.5).all()
    assert weekly.fund_weights["target_weight"].eq(0.5).all()
    assert daily.diagnostics["turnover"].sum() > weekly.diagnostics["turnover"].sum()


def test_transaction_cost_override_changes_only_net_returns() -> None:
    returns, classes = _returns()
    config = _config()
    panel = FamilyPanel("equity", returns, classes, 252, 5)

    low = oos_backtest(
        panel,
        "equal_weight",
        config=config,
        rebalance_schedule="weekly",
        transaction_cost_bps=5,
    )
    high = oos_backtest(
        panel,
        "equal_weight",
        config=config,
        rebalance_schedule="weekly",
        transaction_cost_bps=25,
    )

    assert np.allclose(low.fund_returns["gross_return"], high.fund_returns["gross_return"])
    assert np.allclose(low.fund_returns["turnover"], high.fund_returns["turnover"])
    assert high.fund_returns["growth_of_1_net"].iloc[-1] < low.fund_returns[
        "growth_of_1_net"
    ].iloc[-1]


def test_future_return_change_cannot_change_earlier_daily_weight() -> None:
    returns, classes = _returns()
    config = _config(equity_window=10)
    panel = FamilyPanel("equity", returns, classes, 252, 10)

    base = oos_backtest(
        panel, "minimum_variance", config=config, rebalance_schedule="daily"
    )
    first_live = base.diagnostics["rebalance_date"].min()
    changed = returns.copy()
    changed.loc[changed.index >= first_live, "B"] = 0.50
    changed_result = oos_backtest(
        FamilyPanel("equity", changed, classes, 252, 10),
        "minimum_variance",
        config=config,
        rebalance_schedule="daily",
    )

    first = base.fund_weights.loc[
        base.fund_weights["rebalance_date"].eq(first_live), "target_weight"
    ].to_numpy()
    changed_first = changed_result.fund_weights.loc[
        changed_result.fund_weights["rebalance_date"].eq(first_live), "target_weight"
    ].to_numpy()
    assert np.allclose(first, changed_first, atol=1e-12)


def test_real_data_frequency_experiment_is_controlled_and_reproducible(
    tmp_path: pathlib.Path,
) -> None:
    foundation = run_foundation(require_reconciliation=True)
    primary = build_portfolio_suite(foundation.returns, DEFAULT_CONFIG)

    result = build_rebalance_experiments(foundation.returns, primary, DEFAULT_CONFIG)
    paths = save_rebalance_experiment_outputs(
        result,
        data_dir=tmp_path / "data",
        tables_dir=tmp_path / "tables",
    )

    assert len(result.frequency_metrics) == 8
    assert len(result.cost_sensitivity) == 24
    assert result.validation_summary["status"].eq("pass").all()
    assert set(result.frequency_metrics["rebalance_schedule"]) == {
        "daily",
        "weekly",
        "biweekly",
        "monthly",
    }
    assert set(result.frequency_metrics["schedule_role"]) == {
        "diagnostic experiment",
        "primary",
    }
    assert set(path.name for path in paths) == {
        "rebalance_frequency_returns.csv",
        "rebalance_frequency_metrics.csv",
        "rebalance_frequency_cost_sensitivity.csv",
        "rebalance_frequency_rebalances.csv",
        "rebalance_frequency_decision_support.csv",
        "rebalance_frequency_validation.csv",
    }
