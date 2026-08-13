"""Pure diagnostics for the experimental PCA effective-bets portfolio rule."""

from __future__ import annotations

import numpy as np


class EffectiveBetsValidationError(ValueError):
    """Raised when weights or covariance cannot define PCA risk bets."""


def pca_bet_distribution(
    weights: np.ndarray, covariance: np.ndarray
) -> np.ndarray:
    """Return portfolio-variance shares across orthogonal PCA risk bets."""
    allocation = np.asarray(weights, dtype=float)
    matrix = np.asarray(covariance, dtype=float)
    if allocation.ndim != 1:
        raise EffectiveBetsValidationError("weights must be one-dimensional")
    if matrix.shape != (len(allocation), len(allocation)):
        raise EffectiveBetsValidationError("covariance shape must match weights")
    if not np.isfinite(allocation).all() or not np.isfinite(matrix).all():
        raise EffectiveBetsValidationError("weights and covariance must be finite")
    if not np.allclose(matrix, matrix.T, atol=1e-10, rtol=1e-10):
        raise EffectiveBetsValidationError("covariance must be symmetric")

    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    if eigenvalues.min() <= 0:
        raise EffectiveBetsValidationError("covariance must be positive definite")
    factor_exposure = eigenvectors.T @ allocation
    contributions = eigenvalues * np.square(factor_exposure)
    total_variance = float(allocation @ matrix @ allocation)
    if total_variance <= 0:
        raise EffectiveBetsValidationError("portfolio variance must be positive")
    distribution = np.clip(contributions / total_variance, 0.0, None)
    distribution /= distribution.sum()
    return distribution


def effective_number_of_bets(
    weights: np.ndarray, covariance: np.ndarray
) -> float:
    """Return exponential Shannon entropy of orthogonal PCA risk shares."""
    distribution = pca_bet_distribution(weights, covariance)
    positive = distribution[distribution > 0]
    entropy = -float(positive @ np.log(positive))
    return float(np.exp(entropy))


__all__ = [
    "EffectiveBetsValidationError",
    "effective_number_of_bets",
    "pca_bet_distribution",
]
