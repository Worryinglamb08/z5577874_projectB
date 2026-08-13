"""Coverage, timing, weight, and real-data tests for Phase 5 fusion."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.fusion import (  # noqa: E402
    apply_sentiment,
    build_coverage_adjusted_signals,
)


def _sector_index() -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for date, values in (
        ("2022-01-03", {"A": (0.20, 0.30, 0.50), "B": (-0.10, -0.20, 1.00)}),
        ("2022-01-04", {"A": (0.40, 0.50, 0.80), "B": (0.10, 0.20, 0.25)}),
        ("2022-01-05", {"A": (-0.30, -0.40, 0.75), "B": (0.30, 0.40, 0.50)}),
    ):
        for sector, (plain, finance, confidence) in values.items():
            records.append(
                {
                    "date": pd.Timestamp(date),
                    "sector": sector,
                    "plain_sentiment_index": plain,
                    "finance_sentiment_index": finance,
                    "coverage_confidence": confidence,
                    "has_news": True,
                }
            )
    return pd.DataFrame.from_records(records)


def test_coverage_adjustment_is_same_day_then_lagged_one_sector_date() -> None:
    result = build_coverage_adjusted_signals(_sector_index())
    sector_a = result.loc[result["sector"].eq("A")].set_index("date")

    assert sector_a.loc[
        pd.Timestamp("2022-01-03"), "coverage_adjusted_finance_sentiment"
    ] == pytest.approx(0.15)
    assert sector_a.loc[
        pd.Timestamp("2022-01-04"), "coverage_adjusted_signal_lag1"
    ] == pytest.approx(0.15)
    assert sector_a.loc[
        pd.Timestamp("2022-01-04"), "coverage_confidence_lag1"
    ] == pytest.approx(0.50)
    assert sector_a.loc[
        pd.Timestamp("2022-01-04"), "signal_source_date"
    ] == pd.Timestamp("2022-01-03")


def test_future_sentiment_cannot_change_an_earlier_tradable_signal() -> None:
    base = _sector_index()
    changed = base.copy()
    changed.loc[changed["date"].eq("2022-01-05"), "finance_sentiment_index"] = -0.99

    original = build_coverage_adjusted_signals(base).set_index(["date", "sector"])
    perturbed = build_coverage_adjusted_signals(changed).set_index(["date", "sector"])

    decision_key = (pd.Timestamp("2022-01-05"), "A")
    assert original.loc[
        decision_key, "coverage_adjusted_signal_lag1"
    ] == pytest.approx(
        perturbed.loc[decision_key, "coverage_adjusted_signal_lag1"]
    )


def test_sentiment_tilt_is_long_only_capped_and_rewards_positive_sector() -> None:
    base = pd.Series(0.25, index=["A1", "A2", "B1", "B2"])
    sectors = pd.Series({"A1": "A", "A2": "A", "B1": "B", "B2": "B"})
    signal = pd.Series({"A": 1.0, "B": -1.0})

    tilted, zscores, multipliers = apply_sentiment(
        base,
        signal,
        sectors,
        strength=0.20,
        z_cap=2.0,
        asset_cap=0.30,
    )

    assert tilted.sum() == pytest.approx(1.0)
    assert tilted.min() >= 0
    assert tilted.max() <= 0.30 + 1e-12
    assert tilted[["A1", "A2"]].sum() > 0.50
    assert (zscores[["A1", "A2"]] > zscores[["B1", "B2"]].to_numpy()).all()
    assert multipliers["A1"] > multipliers["B1"]


def test_constant_signal_preserves_base_weights() -> None:
    base = pd.Series({"A1": 0.20, "A2": 0.30, "B1": 0.10, "B2": 0.40})
    sectors = pd.Series({"A1": "A", "A2": "A", "B1": "B", "B2": "B"})

    tilted, zscores, multipliers = apply_sentiment(
        base,
        pd.Series({"A": 0.10, "B": 0.10}),
        sectors,
        strength=0.20,
        z_cap=2.0,
        asset_cap=0.50,
    )

    assert np.allclose(tilted, base)
    assert np.allclose(zscores, 0)
    assert np.allclose(multipliers, 1)


def test_tilt_handles_zero_base_weights_when_ten_assets_are_at_cap() -> None:
    assets = [f"A{i:02d}" for i in range(12)]
    base = pd.Series([0.10] * 10 + [0.0, 0.0], index=assets)
    sectors = pd.Series({asset: f"S{i % 3}" for i, asset in enumerate(assets)})

    tilted, _, _ = apply_sentiment(
        base,
        pd.Series({"S0": 1.0, "S1": 0.0, "S2": -1.0}),
        sectors,
        strength=0.20,
        z_cap=2.0,
        asset_cap=0.10,
    )

    assert tilted.sum() == pytest.approx(1.0)
    assert np.allclose(tilted.iloc[:10], 0.10)
    assert np.allclose(tilted.iloc[10:], 0.0)


def test_generated_real_data_fusion_evidence_is_complete_and_valid() -> None:
    data_dir = PROJECT_ROOT / "results" / "data"
    tables_dir = PROJECT_ROOT / "results" / "tables"
    validation = pd.read_csv(tables_dir / "fusion_validation_summary.csv")
    comparison = pd.read_csv(tables_dir / "fusion_performance_comparison.csv")
    weights = pd.read_csv(
        data_dir / "fusion_weights.csv",
        parse_dates=["rebalance_date", "signal_source_date"],
    )

    assert validation["status"].eq("pass").all()
    assert comparison["variant"].nunique() == 4
    assert weights["target_weight"].between(0, 0.10 + 1e-10).all()
    augmented = weights.loc[weights["variant"].eq("coverage_aware_finance")]
    assert (augmented["signal_source_date"] < augmented["rebalance_date"]).all()
    primary = comparison.set_index("variant").loc["coverage_aware_finance"]
    assert primary["delta_net_sharpe_ratio_vs_base"] == pytest.approx(
        -0.050235, abs=1e-6
    )
