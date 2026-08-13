"""Run the isolated Risk-Parity Black-Litterman sentiment prototype."""

from __future__ import annotations

import pathlib
import sys

import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.black_litterman_experiment import (  # noqa: E402
    build_black_litterman_experiment,
    save_black_litterman_experiment,
)
from src.config import DEFAULT_CONFIG  # noqa: E402
from src.foundation import run_foundation  # noqa: E402


def main() -> None:
    """Build and save prototype-only monthly comparison evidence."""
    foundation = run_foundation(require_reconciliation=True)
    sentiment = pd.read_csv(
        PROJECT_ROOT / "results" / "data" / "coverage_adjusted_sentiment.csv",
        parse_dates=["date", "signal_source_date"],
    )
    ticker_sectors = foundation.clean.equities[["ticker", "sector"]].drop_duplicates()
    experiment = build_black_litterman_experiment(
        foundation.returns,
        sentiment,
        ticker_sectors,
        DEFAULT_CONFIG,
    )
    paths = save_black_litterman_experiment(
        experiment,
        data_dir=PROJECT_ROOT / "results" / "data",
        tables_dir=PROJECT_ROOT / "results" / "tables",
    )
    print(
        "Black-Litterman prototype complete:",
        f"{experiment.fund_returns['variant'].nunique()} comparison paths,",
        f"{len(experiment.rebalance_diagnostics)} validated rebalances,",
        f"{len(paths)} artifacts written.",
    )
    print(experiment.performance_comparison.to_string(index=False))
    print(experiment.method_distinctness.to_string(index=False))


if __name__ == "__main__":
    main()
