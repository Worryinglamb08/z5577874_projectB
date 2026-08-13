"""Pure allocation-history transformations shared by report and app figures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

SECTOR_LABELS = {
    "Comm": "Communication Services",
    "Consumer": "Consumer",
    "Energy": "Energy",
    "Financials": "Financials",
    "Healthcare": "Healthcare",
    "Industrials": "Industrials",
    "Materials": "Materials",
    "RealEstate": "Real Estate",
    "Tech": "Technology",
    "Utilities": "Utilities",
    "Crypto": "Crypto",
}
SECTOR_ORDER = (
    "Comm",
    "Consumer",
    "Energy",
    "Financials",
    "Healthcare",
    "Industrials",
    "Materials",
    "RealEstate",
    "Tech",
    "Utilities",
    "Crypto",
)


@dataclass(frozen=True)
class AllocationHistory:
    """Long target-weight history with an explicit display order and basis."""

    data: pd.DataFrame
    category_order: tuple[str, ...]
    basis: Literal["sector", "cryptoasset"]


def _sector_pairs(sector_source: pd.DataFrame) -> pd.DataFrame:
    asset_column = "asset" if "asset" in sector_source else "ticker"
    if asset_column not in sector_source or "sector" not in sector_source:
        raise ValueError("Sector source is missing asset-sector fields")
    pairs = (
        sector_source[[asset_column, "sector"]]
        .rename(columns={asset_column: "asset"})
        .drop_duplicates()
    )
    if pairs.duplicated("asset").any():
        raise ValueError("An equity asset maps to more than one sector")
    return pairs


def sector_allocation(
    latest_weights: pd.DataFrame, sector_source: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate one latest target vector by supplied equity sector."""
    required_weights = {"asset", "asset_class", "target_weight"}
    if not required_weights.issubset(latest_weights.columns):
        raise ValueError("Latest weights are missing asset allocation fields")
    allocated = latest_weights[["asset", "asset_class", "target_weight"]].merge(
        _sector_pairs(sector_source),
        on="asset",
        how="left",
        validate="many_to_one",
    )
    allocated.loc[allocated["asset_class"].eq("crypto"), "sector"] = "Crypto"
    if allocated["sector"].isna().any():
        missing = sorted(allocated.loc[allocated["sector"].isna(), "asset"].unique())
        raise ValueError(f"Missing supplied sector classification for: {missing}")
    result = (
        allocated.groupby("sector", as_index=False, sort=True)["target_weight"]
        .sum()
        .sort_values("target_weight", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    result["sector_label"] = result["sector"].map(SECTOR_LABELS)
    if result["sector_label"].isna().any():
        raise ValueError("Sector display label is missing")
    if not np.isclose(result["target_weight"].sum(), 1.0):
        raise ValueError("Sector allocation must sum to 100%")
    return result


def allocation_history(
    fund_weights: pd.DataFrame,
    fund_id: str,
    sector_source: pd.DataFrame,
) -> AllocationHistory:
    """Aggregate every target vector by equity sector or cryptoasset."""
    required = (
        "fund_id",
        "rebalance_date",
        "asset",
        "asset_class",
        "target_weight",
    )
    if not set(required).issubset(fund_weights.columns):
        raise ValueError("Fund weights are missing allocation-history fields")
    selected = fund_weights.loc[
        fund_weights["fund_id"].eq(fund_id), list(required)
    ].copy()
    if selected.empty:
        raise ValueError(f"No weight history found for {fund_id}")
    selected["rebalance_date"] = pd.to_datetime(selected["rebalance_date"])
    asset_classes = set(selected["asset_class"].unique())
    if asset_classes == {"crypto"}:
        selected["category"] = selected["asset"]
        selected["category_label"] = selected["asset"].str.removesuffix("-USD")
        means = selected.groupby("category", sort=True)["target_weight"].mean()
        order = tuple(means.sort_values(ascending=False, kind="stable").index)
        basis: Literal["sector", "cryptoasset"] = "cryptoasset"
    else:
        selected = selected.merge(
            _sector_pairs(sector_source),
            on="asset",
            how="left",
            validate="many_to_one",
        )
        selected.loc[selected["asset_class"].eq("crypto"), "sector"] = "Crypto"
        if selected["sector"].isna().any():
            missing = sorted(
                selected.loc[selected["sector"].isna(), "asset"].unique()
            )
            raise ValueError(f"Missing supplied sector classification for: {missing}")
        selected["category"] = selected["sector"]
        selected["category_label"] = selected["sector"].map(SECTOR_LABELS)
        present = set(selected["category"])
        order = tuple(category for category in SECTOR_ORDER if category in present)
        basis = "sector"
    history = (
        selected.groupby(
            ["rebalance_date", "category", "category_label"],
            as_index=False,
            sort=True,
        )["target_weight"]
        .sum()
        .sort_values(["rebalance_date", "category"], kind="stable")
        .reset_index(drop=True)
    )
    totals = history.groupby("rebalance_date")["target_weight"].sum()
    if not np.allclose(totals, 1.0, atol=1e-7, rtol=0):
        raise ValueError("Every allocation-history date must sum to 100%")
    if history["target_weight"].lt(-1e-10).any():
        raise ValueError("Allocation history contains a negative target weight")
    return AllocationHistory(history, order, basis)


__all__ = [
    "SECTOR_LABELS",
    "SECTOR_ORDER",
    "AllocationHistory",
    "allocation_history",
    "sector_allocation",
]
