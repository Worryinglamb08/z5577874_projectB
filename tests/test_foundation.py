"""End-to-end regression and independence tests for Phase 1."""

from __future__ import annotations

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.foundation import run_foundation  # noqa: E402


def test_project_b_has_no_runtime_import_from_project_a() -> None:
    searched = [
        *PROJECT_ROOT.joinpath("src").glob("*.py"),
        *PROJECT_ROOT.joinpath("scripts").glob("*.py"),
    ]
    forbidden = "z5577874_" + "projectA"

    assert all(forbidden not in path.read_text(encoding="utf-8") for path in searched)


def test_real_data_reconciles_to_final_project_a_foundation() -> None:
    result = run_foundation(require_reconciliation=True)

    assert result.reconciliation["status"].eq("pass").all()
    assert set(result.input_catalog["dataset"]) == {
        "equity_returns",
        "crypto_returns_native",
        "combined_returns",
        "aligned_headlines",
        "ticker_day_news_panel",
        "sector_day_coverage_panel",
    }
    assert result.returns.combined_returns["date"].is_monotonic_increasing
    assert not result.returns.combined_returns["date"].dt.dayofweek.isin([5, 6]).any()
