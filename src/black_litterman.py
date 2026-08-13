"""Modified Black-Litterman allocations for the isolated sentiment prototype.

The prototype reverse-optimises a Risk-Parity reference portfolio rather than
claiming to observe a historical market-cap portfolio. Sector sentiment defines
relative-return views, while news coverage controls view uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.config import ModelConfig


class BlackLittermanValidationError(ValueError):
    """Raised when a Black-Litterman input or solution is invalid."""


@dataclass(frozen=True)
class BlackLittermanAllocation:
    """One posterior allocation and its auditable intermediate values."""

    weights: pd.Series
    prior_returns: pd.Series
    posterior_returns: pd.Series
    sector_zscores: pd.Series
    view_confidence: pd.Series
    diagnostics: dict[str, object]


def _validate_covariance(covariance: np.ndarray, asset_count: int) -> np.ndarray:
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape != (asset_count, asset_count):
        raise BlackLittermanValidationError(
            "covariance must be square and match the asset count"
        )
    if not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T, atol=1e-12):
        raise BlackLittermanValidationError("covariance must be finite and symmetric")
    if np.linalg.eigvalsh(matrix).min() <= 0:
        raise BlackLittermanValidationError("covariance must be positive definite")
    return matrix


def cross_sectional_zscore(values: pd.Series, cap: float) -> pd.Series:
    """Standardise one dated sector cross-section and clip extreme scores."""
    series = pd.Series(values, dtype="float64").sort_index()
    if series.empty or series.isna().any() or not np.isfinite(series).all():
        raise BlackLittermanValidationError("sector signal must be finite and complete")
    if cap <= 0:
        raise BlackLittermanValidationError("z-score cap must be positive")
    scale = float(series.std(ddof=0))
    if scale <= 1e-12:
        return pd.Series(0.0, index=series.index, dtype="float64")
    return ((series - series.mean()) / scale).clip(-cap, cap)


def sector_basket_view_matrix(asset_sectors: pd.Series) -> pd.DataFrame:
    """Create one non-overlapping equal-weight basket view per sector."""
    sectors = pd.Series(asset_sectors, dtype="string").sort_index()
    if sectors.empty or sectors.isna().any() or sectors.nunique() < 2:
        raise BlackLittermanValidationError(
            "at least two complete asset sectors are required"
        )
    records: list[pd.Series] = []
    for sector in sorted(sectors.unique()):
        inside = sectors.eq(sector)
        row = pd.Series(0.0, index=sectors.index, dtype="float64", name=sector)
        row.loc[inside] = 1 / int(inside.sum())
        records.append(row)
    matrix = pd.DataFrame(records)
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-12):
        raise BlackLittermanValidationError("sector-basket view rows must sum to one")
    if not np.allclose((matrix > 0).sum(axis=0), 1):
        raise BlackLittermanValidationError("sector baskets must not overlap")
    return matrix


def black_litterman_posterior_returns(
    prior_returns: np.ndarray,
    covariance: np.ndarray,
    view_matrix: np.ndarray,
    view_returns: np.ndarray,
    view_confidence: np.ndarray,
    *,
    tau: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Blend a prior with confidence-scaled relative views.

    View uncertainty follows ``diag(P tau Sigma P') * (1-c) / c``. Views with
    zero confidence must be removed by the caller; confidence below one keeps
    the posterior numerically well defined.
    """
    prior = np.asarray(prior_returns, dtype=float)
    matrix = _validate_covariance(covariance, len(prior))
    views = np.asarray(view_matrix, dtype=float)
    targets = np.asarray(view_returns, dtype=float)
    confidence = np.asarray(view_confidence, dtype=float)
    if tau <= 0:
        raise BlackLittermanValidationError("tau must be positive")
    if views.ndim != 2 or views.shape[1] != len(prior):
        raise BlackLittermanValidationError("view matrix has an invalid shape")
    if len(views) == 0:
        return prior.copy(), np.empty(0, dtype=float)
    if targets.shape != (len(views),) or confidence.shape != (len(views),):
        raise BlackLittermanValidationError("view vectors have invalid shapes")
    if not (
        np.isfinite(views).all()
        and np.isfinite(targets).all()
        and np.isfinite(confidence).all()
    ):
        raise BlackLittermanValidationError("views must be finite")
    if (confidence <= 0).any() or (confidence >= 1).any():
        raise BlackLittermanValidationError("active confidence must lie in (0, 1)")

    scaled_covariance = tau * matrix
    view_variance = np.diag(views @ scaled_covariance @ views.T)
    if (view_variance <= 0).any():
        raise BlackLittermanValidationError("view variance must be positive")
    omega = view_variance * (1 - confidence) / confidence
    prior_precision = np.linalg.solve(scaled_covariance, np.eye(len(prior)))
    inverse_omega = 1 / omega
    posterior_precision = prior_precision + views.T @ (
        inverse_omega[:, None] * views
    )
    posterior_information = (
        prior_precision @ prior + views.T @ (inverse_omega * targets)
    )
    posterior = np.linalg.solve(posterior_precision, posterior_information)
    if not np.isfinite(posterior).all():
        raise BlackLittermanValidationError("posterior returns are not finite")
    return posterior, omega


def _optimise_utility(
    posterior_returns: np.ndarray,
    covariance: np.ndarray,
    start: np.ndarray,
    *,
    risk_aversion: float,
    asset_cap: float,
    tolerance: float,
    max_iterations: int,
) -> tuple[np.ndarray, object]:
    def objective(weights: np.ndarray) -> float:
        return float(
            0.5 * risk_aversion * weights @ covariance @ weights
            - posterior_returns @ weights
        )

    result = minimize(
        objective,
        start,
        jac=lambda weights: risk_aversion * covariance @ weights
        - posterior_returns,
        method="SLSQP",
        bounds=[(0.0, asset_cap)] * len(start),
        constraints={
            "type": "eq",
            "fun": lambda weights: float(weights.sum() - 1),
            "jac": lambda weights: np.ones_like(weights),
        },
        options={"ftol": tolerance, "maxiter": max_iterations},
    )
    if not result.success:
        raise BlackLittermanValidationError(
            f"posterior utility optimisation failed: {result.message}"
        )
    weights = np.asarray(result.x, dtype=float)
    if (
        not np.isfinite(weights).all()
        or weights.min() < -tolerance
        or weights.max() > asset_cap + tolerance
        or abs(weights.sum() - 1) > tolerance
    ):
        raise BlackLittermanValidationError("posterior weights are invalid")
    return weights, result


def build_black_litterman_allocation(
    prior_weights: pd.Series,
    covariance: np.ndarray,
    asset_sectors: pd.Series,
    sector_signal: pd.Series,
    sector_confidence: pd.Series,
    *,
    view_scale_annual: float,
    config: ModelConfig,
) -> BlackLittermanAllocation:
    """Build one constrained posterior allocation from lagged sector evidence."""
    prior = pd.Series(prior_weights, dtype="float64").sort_index()
    sectors = pd.Series(asset_sectors, dtype="string").reindex(prior.index)
    if prior.empty or sectors.isna().any():
        raise BlackLittermanValidationError("prior weights and sectors must be complete")
    if (
        not np.isfinite(prior).all()
        or prior.lt(-config.weight_tolerance).any()
        or prior.gt(config.equity_asset_cap + config.weight_tolerance).any()
        or abs(prior.sum() - 1) > config.weight_tolerance
    ):
        raise BlackLittermanValidationError("prior weights are invalid")
    if view_scale_annual <= 0:
        raise BlackLittermanValidationError("annual view scale must be positive")
    matrix = _validate_covariance(covariance, len(prior))
    view_frame = sector_basket_view_matrix(sectors)
    signal = pd.Series(sector_signal, dtype="float64").reindex(view_frame.index)
    confidence = pd.Series(sector_confidence, dtype="float64").reindex(
        view_frame.index
    )
    if signal.isna().any() or confidence.isna().any():
        raise BlackLittermanValidationError("sector views must be complete")
    if not confidence.between(0, 1).all():
        raise BlackLittermanValidationError("coverage confidence must lie in [0, 1]")
    zscores = cross_sectional_zscore(signal, config.fusion_signal_z_cap)
    prior_returns = config.black_litterman_risk_aversion * matrix @ prior.to_numpy()
    prior_view_returns = view_frame.to_numpy() @ prior_returns
    target_view_returns = prior_view_returns + view_scale_annual * zscores.to_numpy()
    capped_confidence = confidence.clip(upper=config.black_litterman_confidence_cap)
    active = capped_confidence.gt(0) & zscores.ne(0)
    posterior_returns, omega = black_litterman_posterior_returns(
        prior_returns,
        matrix,
        view_frame.loc[active].to_numpy(),
        target_view_returns[active.to_numpy()],
        capped_confidence.loc[active].to_numpy(),
        tau=config.black_litterman_tau,
    )
    weights, result = _optimise_utility(
        posterior_returns,
        matrix,
        prior.to_numpy(),
        risk_aversion=config.black_litterman_risk_aversion,
        asset_cap=config.equity_asset_cap,
        tolerance=config.solver_tolerance,
        max_iterations=config.solver_max_iterations,
    )
    shift = posterior_returns - prior_returns
    diagnostics: dict[str, object] = {
        "solver_success": bool(result.success),
        "solver_status": int(result.status),
        "solver_iterations": int(result.nit),
        "active_view_count": int(active.sum()),
        "mean_active_confidence": (
            float(capped_confidence.loc[active].mean()) if active.any() else 0.0
        ),
        "maximum_active_confidence": (
            float(capped_confidence.loc[active].max()) if active.any() else 0.0
        ),
        "minimum_view_uncertainty": float(omega.min()) if len(omega) else np.nan,
        "maximum_view_uncertainty": float(omega.max()) if len(omega) else np.nan,
        "posterior_return_shift_l2": float(np.linalg.norm(shift)),
        "maximum_absolute_posterior_return_shift": float(np.abs(shift).max()),
        "l1_weight_tilt_from_prior": float(np.abs(weights - prior.to_numpy()).sum()),
        "maximum_weight_sum_residual": float(abs(weights.sum() - 1)),
        "maximum_bound_residual": float(
            max(0.0, -weights.min(), weights.max() - config.equity_asset_cap)
        ),
    }
    return BlackLittermanAllocation(
        weights=pd.Series(weights, index=prior.index, name="target_weight"),
        prior_returns=pd.Series(prior_returns, index=prior.index),
        posterior_returns=pd.Series(posterior_returns, index=prior.index),
        sector_zscores=zscores,
        view_confidence=capped_confidence,
        diagnostics=diagnostics,
    )


__all__ = [
    "BlackLittermanAllocation",
    "BlackLittermanValidationError",
    "black_litterman_posterior_returns",
    "build_black_litterman_allocation",
    "cross_sectional_zscore",
    "sector_basket_view_matrix",
]
