"""Regenerate the complete validated Project B analytical output."""

from __future__ import annotations

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_full_build  # noqa: E402


def main() -> None:
    """Run the fixed full build and report its completion gates."""
    result = run_full_build(PROJECT_ROOT)
    print(
        "Full Project B build complete:",
        f"{result.artifact_count} canonical artifacts;",
        f"{result.fund_count} monthly funds and {result.rebalance_count} rebalances;",
        f"{result.frequency_path_count} preserved diagnostic frequency paths;",
        f"{result.sector_day_rows:,} sector-day sentiment rows;",
        f"fusion Sharpe change {result.fusion_sharpe_change:.3f};",
        f"{result.exhibit_count} exhibits and {result.fact_sheet_count} fact sheets.",
    )
    print(
        "Foundation reconciliation:",
        f"{result.equity_rows:,} equity rows,",
        f"{result.crypto_rows:,} crypto rows,",
        f"{result.headline_rows:,} headlines; all checks passed.",
    )
    print("Output schemas validated and timestamp-free manifest written.")


if __name__ == "__main__":
    main()
