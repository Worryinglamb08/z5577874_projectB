"""Run the isolated Effective Number of Bets prototype."""

from __future__ import annotations

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_CONFIG  # noqa: E402
from src.effective_bets_experiment import (  # noqa: E402
    build_effective_bets_experiment,
    save_effective_bets_experiment,
)
from src.foundation import run_foundation  # noqa: E402


def main() -> None:
    """Build and save prototype-only monthly comparison evidence."""
    foundation = run_foundation(require_reconciliation=True)
    experiment = build_effective_bets_experiment(foundation.returns, DEFAULT_CONFIG)
    paths = save_effective_bets_experiment(
        experiment,
        data_dir=PROJECT_ROOT / "results" / "data",
        tables_dir=PROJECT_ROOT / "results" / "tables",
    )
    print(
        "Effective-bets prototype complete:",
        f"{experiment.fund_returns['fund_id'].nunique()} comparison paths,",
        f"{len(experiment.rebalance_diagnostics)} validated rebalances,",
        f"{len(paths)} artifacts written.",
    )
    print(experiment.performance_comparison.to_string(index=False))
    print(experiment.method_distinctness.to_string(index=False))


if __name__ == "__main__":
    main()
