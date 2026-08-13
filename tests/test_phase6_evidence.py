"""Generated-artifact contract tests for Phase 6 report evidence."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TABLES = PROJECT_ROOT / "results" / "tables"


def test_phase6_evidence_contract_is_complete_and_traceable() -> None:
    validation = pd.read_csv(TABLES / "phase6_validation_summary.csv")
    exhibits = pd.read_csv(TABLES / "exhibit_catalog.csv")
    findings = pd.read_csv(TABLES / "claim_to_artifact_findings.csv")
    fact_sheets = pd.read_csv(TABLES / "fact_sheet_validation.csv")

    assert len(validation) == 9
    assert validation["status"].eq("pass").all()
    assert len(exhibits) == 9
    assert exhibits["status"].eq("pass").all()
    assert "fund_sharpe_by_family" in set(exhibits["figure"])
    assert len(findings) == 9
    assert findings["status"].eq("reconciled").all()
    assert len(fact_sheets) == 15
    assert fact_sheets["status"].eq("pass").all()
    assert all((PROJECT_ROOT / path).is_file() for path in findings["source_artifact"])


def test_report_table_and_complete_holdings_reconcile_to_primary_outputs() -> None:
    report = pd.read_csv(TABLES / "report_performance_table.csv")
    metrics = pd.read_csv(TABLES / "performance_metrics.csv")
    sheets = pd.read_csv(TABLES / "fund_fact_sheets.csv")

    merged = report.merge(
        metrics[["fund_id", "net_annualized_return", "net_sharpe_ratio"]],
        on="fund_id",
        validate="one_to_one",
    )
    assert report["fund_id"].nunique() == 15
    assert np.allclose(merged["annualized_return_net"], merged["net_annualized_return"])
    assert np.allclose(merged["sharpe_ratio_net"], merged["net_sharpe_ratio"])

    for row in sheets.itertuples(index=False):
        holdings = str(row.latest_all_nonzero_holdings).split("; ")
        assert len(holdings) == row.latest_nonzero_holding_count
        assert all(holding.endswith("%") and " " in holding for holding in holdings)
        assert row.latest_weight_hhi > 0
        assert row.evidence_limit
