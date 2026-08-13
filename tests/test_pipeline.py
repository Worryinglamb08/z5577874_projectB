"""Phase 8 output-contract and reproducibility-helper tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.pipeline import (
    CANONICAL_ARTIFACTS,
    FROZEN_FREQUENCY_ARTIFACTS,
    MANIFEST_RELATIVE_PATH,
    MONTHLY_BUILD_ARTIFACTS,
    artifact_manifest,
    clean_managed_outputs,
    compare_manifests,
    validate_output_contract,
    write_artifact_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_current_outputs_satisfy_the_canonical_contract() -> None:
    assert len(CANONICAL_ARTIFACTS) == 76
    assert len(set(CANONICAL_ARTIFACTS)) == len(CANONICAL_ARTIFACTS)
    assert all(relative.startswith("results/") for relative in CANONICAL_ARTIFACTS)
    validate_output_contract(PROJECT_ROOT)


def test_manifest_is_timestamp_free_sorted_and_content_addressed(
    tmp_path: Path,
) -> None:
    manifest = artifact_manifest(PROJECT_ROOT)

    assert manifest["relative_path"].tolist() == sorted(CANONICAL_ARTIFACTS)
    assert manifest["sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert not any("time" in column.lower() for column in manifest.columns)
    assert manifest["bytes"].gt(0).all()

    copied = manifest.copy(deep=True)
    compare_manifests(manifest, copied)
    output = tmp_path / "manifest.csv"
    manifest.to_csv(output, index=False)
    assert output.is_file()


def test_cleanup_removes_only_declared_outputs(tmp_path: Path) -> None:
    managed = tmp_path / MONTHLY_BUILD_ARTIFACTS[0]
    frozen = tmp_path / FROZEN_FREQUENCY_ARTIFACTS[0]
    prototype = tmp_path / "results/data/example_prototype_returns.csv"
    curated = tmp_path / "results/tables/finance_lexicon_candidate_research.csv"
    for path in (managed, frozen, prototype, curated):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("preserve-or-replace", encoding="utf-8")

    removed = clean_managed_outputs(tmp_path)

    assert managed.resolve() in removed
    assert not managed.exists()
    assert frozen.exists()
    assert prototype.exists()
    assert curated.exists()


def test_manifest_writer_uses_the_declared_location() -> None:
    path = write_artifact_manifest(PROJECT_ROOT)
    manifest = pd.read_csv(path)

    assert path == (PROJECT_ROOT / MANIFEST_RELATIVE_PATH).resolve()
    assert len(manifest) == len(CANONICAL_ARTIFACTS)
