"""Run the isolated Ledoit-Wolf covariance robustness prototype."""

from __future__ import annotations

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_CONFIG  # noqa: E402
from src.foundation import run_foundation  # noqa: E402
from src.ledoit_wolf_experiment import (  # noqa: E402
    build_ledoit_wolf_experiment,
    save_ledoit_wolf_experiment,
)


def main() -> None:
    """Build and save matched sample and Ledoit-Wolf monthly paths."""
    foundation = run_foundation(require_reconciliation=True)
    experiment = build_ledoit_wolf_experiment(foundation.returns, DEFAULT_CONFIG)
    paths = save_ledoit_wolf_experiment(
        experiment,
        data_dir=PROJECT_ROOT / "results" / "data",
        tables_dir=PROJECT_ROOT / "results" / "tables",
    )
    candidates = int(experiment.paired_comparison["candidate_for_adoption"].sum())
    print(
        "Ledoit-Wolf prototype complete:",
        f"{experiment.fund_returns['prototype_id'].nunique()} matched paths,",
        f"{len(experiment.rebalance_diagnostics)} validated decisions,",
        f"{candidates}/{len(experiment.paired_comparison)} pairs meet the",
        "pre-declared adoption screen;",
        f"{len(paths)} artifacts written.",
    )


if __name__ == "__main__":
    main()
