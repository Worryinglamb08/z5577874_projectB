"""Run and compare canonical builds using a stable artifact-manifest baseline."""

from __future__ import annotations

import argparse
import pathlib
import sys

import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import artifact_manifest, compare_manifests, run_full_build  # noqa: E402


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=pathlib.Path,
        help="Manifest CSV used to split two builds across separate processes.",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Run one build and write --baseline instead of comparing.",
    )
    return parser.parse_args()


def main() -> None:
    """Build twice together, or record/compare across two bounded processes."""
    args = _arguments()
    if args.record and args.baseline is None:
        raise SystemExit("--record requires --baseline PATH")
    if args.record:
        run_full_build(PROJECT_ROOT)
        artifact_manifest(PROJECT_ROOT).to_csv(args.baseline, index=False)
        print(f"Baseline manifest recorded: {args.baseline}")
        return
    if args.baseline is not None:
        run_full_build(PROJECT_ROOT)
        first_manifest = pd.read_csv(args.baseline)
        second_manifest = artifact_manifest(PROJECT_ROOT)
    else:
        run_full_build(PROJECT_ROOT)
        first_manifest = artifact_manifest(PROJECT_ROOT)
        run_full_build(PROJECT_ROOT)
        second_manifest = artifact_manifest(PROJECT_ROOT)
    compare_manifests(first_manifest, second_manifest)
    print(
        "Reproducibility passed:",
        f"{len(second_manifest)} canonical artifacts are byte-identical across two runs.",
    )


if __name__ == "__main__":
    main()
