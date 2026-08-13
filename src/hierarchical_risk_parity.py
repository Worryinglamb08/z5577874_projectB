"""Pure Hierarchical Risk Parity calculations for the isolated prototype."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


class HierarchicalRiskParityValidationError(ValueError):
    """Raised when an HRP input or allocation is invalid."""


@dataclass(frozen=True)
class HierarchicalRiskParityResult:
    """Raw HRP weights and clustering diagnostics before product constraints."""

    weights: pd.Series
    ordered_assets: tuple[str, ...]
    linkage_matrix: np.ndarray
    diagnostics: dict[str, object]


def correlation_distance(correlation: np.ndarray) -> np.ndarray:
    """Convert a correlation matrix to the standard HRP angular distance."""
    matrix = np.asarray(correlation, dtype=float)
    if (
        matrix.ndim != 2
        or matrix.shape[0] != matrix.shape[1]
        or matrix.shape[0] < 2
    ):
        raise HierarchicalRiskParityValidationError(
            "correlation must be a square matrix with at least two assets"
        )
    if not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T, atol=1e-10):
        raise HierarchicalRiskParityValidationError(
            "correlation must be finite and symmetric"
        )
    if not np.allclose(np.diag(matrix), 1.0, atol=1e-8):
        raise HierarchicalRiskParityValidationError(
            "correlation diagonal must equal one"
        )
    if matrix.min() < -1 - 1e-8 or matrix.max() > 1 + 1e-8:
        raise HierarchicalRiskParityValidationError(
            "correlation values must lie in [-1, 1]"
        )
    distance = np.sqrt(np.clip((1 - matrix) / 2, 0.0, 1.0))
    np.fill_diagonal(distance, 0.0)
    return distance


def _cluster_variance(covariance: np.ndarray, positions: list[int]) -> float:
    subset = covariance[np.ix_(positions, positions)]
    diagonal = np.diag(subset)
    if (diagonal <= 0).any():
        raise HierarchicalRiskParityValidationError(
            "cluster covariance must have positive variances"
        )
    inverse_variance = 1 / diagonal
    weights = inverse_variance / inverse_variance.sum()
    variance = float(weights @ subset @ weights)
    if not np.isfinite(variance) or variance <= 0:
        raise HierarchicalRiskParityValidationError(
            "cluster variance must be positive and finite"
        )
    return variance


def hierarchical_risk_parity(
    covariance: np.ndarray,
    assets: pd.Index | list[str] | tuple[str, ...],
) -> HierarchicalRiskParityResult:
    """Build standard single-linkage HRP weights by recursive bisection."""
    labels = pd.Index(assets, dtype="object")
    matrix = np.asarray(covariance, dtype=float)
    if labels.empty or labels.has_duplicates:
        raise HierarchicalRiskParityValidationError(
            "asset labels must be non-empty and unique"
        )
    if matrix.shape != (len(labels), len(labels)):
        raise HierarchicalRiskParityValidationError(
            "covariance must be square and match the asset count"
        )
    if not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T, atol=1e-10):
        raise HierarchicalRiskParityValidationError(
            "covariance must be finite and symmetric"
        )
    if np.linalg.eigvalsh(matrix).min() <= 0:
        raise HierarchicalRiskParityValidationError(
            "covariance must be positive definite"
        )
    if len(labels) == 1:
        return HierarchicalRiskParityResult(
            weights=pd.Series([1.0], index=labels, name="raw_hrp_weight"),
            ordered_assets=(str(labels[0]),),
            linkage_matrix=np.empty((0, 4)),
            diagnostics={
                "cluster_count": 1,
                "minimum_linkage_distance": np.nan,
                "maximum_linkage_distance": np.nan,
            },
        )

    volatility = np.sqrt(np.diag(matrix))
    correlation = matrix / np.outer(volatility, volatility)
    correlation = np.clip(correlation, -1.0, 1.0)
    np.fill_diagonal(correlation, 1.0)
    distance = correlation_distance(correlation)
    tree = linkage(squareform(distance, checks=False), method="single")
    order = leaves_list(tree).astype(int).tolist()

    weights = np.ones(len(labels), dtype=float)
    clusters: list[list[int]] = [order]
    while clusters:
        next_clusters: list[list[int]] = []
        for cluster in clusters:
            if len(cluster) <= 1:
                continue
            split = len(cluster) // 2
            left = cluster[:split]
            right = cluster[split:]
            left_variance = _cluster_variance(matrix, left)
            right_variance = _cluster_variance(matrix, right)
            left_allocation = right_variance / (left_variance + right_variance)
            weights[left] *= left_allocation
            weights[right] *= 1 - left_allocation
            next_clusters.extend([left, right])
        clusters = next_clusters

    if (
        not np.isfinite(weights).all()
        or (weights <= 0).any()
        or not np.isclose(weights.sum(), 1.0, atol=1e-10)
    ):
        raise HierarchicalRiskParityValidationError("raw HRP weights are invalid")
    ordered_assets = tuple(str(labels[position]) for position in order)
    return HierarchicalRiskParityResult(
        weights=pd.Series(weights, index=labels, name="raw_hrp_weight"),
        ordered_assets=ordered_assets,
        linkage_matrix=tree,
        diagnostics={
            "cluster_count": len(labels),
            "minimum_linkage_distance": float(tree[:, 2].min()),
            "maximum_linkage_distance": float(tree[:, 2].max()),
        },
    )


__all__ = [
    "HierarchicalRiskParityResult",
    "HierarchicalRiskParityValidationError",
    "correlation_distance",
    "hierarchical_risk_parity",
]
