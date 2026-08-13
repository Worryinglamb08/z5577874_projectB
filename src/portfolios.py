"""Constrained portfolio rules and walk-forward out-of-sample backtests.

The monthly implementation uses a fixed trailing window ending strictly before
the first return earned under each target vector. Holdings drift between
rebalances, so turnover is measured against pre-trade weights rather than the
previous target. All results are historical simulations, not live forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.optimize import OptimizeResult, linprog, minimize

from src.config import (
    AssetFamily,
    CovarianceEstimator,
    ModelConfig,
    PortfolioMethod,
    RebalanceSchedule,
)
from src.effective_bets import effective_number_of_bets
from src.features import ReturnFeatures
from src.hierarchical_risk_parity import hierarchical_risk_parity

METHOD_LABELS: Final = {
    "equal_weight": "Equal Weight",
    "minimum_variance": "Minimum Variance",
    "risk_parity": "Risk Parity",
    "maximum_sharpe": "Maximum Sharpe",
    "effective_bets": "Factor Diversification",
    "hierarchical_risk_parity": "Hierarchical Risk Parity",
    "conditional_value_at_risk": "Minimum CVaR",
}
FAMILY_LABELS: Final = {
    "equity": "Equity",
    "crypto": "Crypto",
    "combined": "Combined",
}


class PortfolioValidationError(ValueError):
    """Raised when inputs, weights, timing, or outputs fail validation."""


@dataclass(frozen=True)
class FamilyPanel:
    """A complete return panel and its investment constraints."""

    family: AssetFamily
    returns: pd.DataFrame
    asset_classes: pd.Series
    annualization_days: int
    estimation_window: int


@dataclass(frozen=True)
class WeightSolution:
    """One validated target vector and its optimiser diagnostics."""

    weights: pd.Series
    diagnostics: dict[str, object]


@dataclass(frozen=True)
class FundBacktest:
    """Daily fund path, rebalance weights, and optimiser diagnostics."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    diagnostics: pd.DataFrame


@dataclass(frozen=True)
class PortfolioSuite:
    """The 15 primary funds and all Phase 2 comparison evidence."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    performance_metrics: pd.DataFrame
    rebalance_diagnostics: pd.DataFrame
    method_distinctness: pd.DataFrame
    fund_fact_sheets: pd.DataFrame
    model_configuration: pd.DataFrame
    validation_summary: pd.DataFrame


def fund_id(family: AssetFamily, method: PortfolioMethod) -> str:
    """Return the stable machine identifier for a fund."""
    return f"{family}_{method}"


def fund_name(family: AssetFamily, method: PortfolioMethod) -> str:
    """Return the user-facing Stockist Funds name."""
    return f"{FAMILY_LABELS[family]} {METHOD_LABELS[method]}"


def _complete_panel(panel: pd.DataFrame, name: str) -> pd.DataFrame:
    """Remove only leading incomplete return rows and reject later gaps."""
    result = panel.copy(deep=True).sort_index().sort_index(axis=1)
    if result.empty or not isinstance(result.index, pd.DatetimeIndex):
        raise PortfolioValidationError(f"{name} must have a non-empty DatetimeIndex")
    if result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise PortfolioValidationError(f"{name} dates must be unique and increasing")
    if result.columns.duplicated().any():
        raise PortfolioValidationError(f"{name} assets must be unique")
    first_complete = result.notna().all(axis=1)
    if not first_complete.any():
        raise PortfolioValidationError(f"{name} has no complete cross-section")
    result = result.loc[first_complete.idxmax() :]
    if result.isna().any().any():
        raise PortfolioValidationError(
            f"{name} has missing returns after its first complete observation"
        )
    if not np.isfinite(result.to_numpy(dtype=float)).all():
        raise PortfolioValidationError(f"{name} contains non-finite returns")
    if result.le(-1).any().any():
        raise PortfolioValidationError(f"{name} contains a return at or below -100%")
    return result.astype("float64")


def build_family_panels(
    features: ReturnFeatures, config: ModelConfig
) -> dict[AssetFamily, FamilyPanel]:
    """Convert validated Phase 1 returns into three investable family panels."""
    equity = features.equity_returns.pivot(
        index="date", columns="ticker", values="simple_return"
    )
    crypto = features.crypto_returns_native.pivot(
        index="date", columns="ticker", values="simple_return"
    )
    combined = features.combined_returns.set_index("date").rename(
        columns=lambda column: column.split("__", maxsplit=1)[-1]
    )
    equity = _complete_panel(equity, "equity returns")
    crypto = _complete_panel(crypto, "crypto returns")
    combined = _complete_panel(combined, "combined returns")

    equity_classes = pd.Series("equity", index=equity.columns, dtype="string")
    crypto_classes = pd.Series("crypto", index=crypto.columns, dtype="string")
    combined_classes = pd.Series(
        ["crypto" if str(asset).endswith("-USD") else "equity" for asset in combined],
        index=combined.columns,
        dtype="string",
    )
    panels: dict[AssetFamily, FamilyPanel] = {
        "equity": FamilyPanel(
            "equity", equity, equity_classes, 252, config.equity_window
        ),
        "crypto": FamilyPanel(
            "crypto", crypto, crypto_classes, 365, config.crypto_window
        ),
        "combined": FamilyPanel(
            "combined", combined, combined_classes, 252, config.combined_window
        ),
    }
    for family, panel in panels.items():
        if len(panel.returns) <= panel.estimation_window:
            raise PortfolioValidationError(
                f"{family} needs more rows than its estimation window"
            )
    return panels


def monthly_rebalance_dates(index: pd.DatetimeIndex, window: int) -> pd.DatetimeIndex:
    """Select first observed date of each month after a complete trailing window."""
    if window < 2 or len(index) <= window:
        raise PortfolioValidationError("calendar cannot support the estimation window")
    first_in_month = ~index.to_period("M").duplicated()
    positions = np.flatnonzero(first_in_month)
    eligible = positions[positions >= window]
    if len(eligible) == 0:
        raise PortfolioValidationError("monthly schedule has no live rebalance dates")
    return index[eligible]


def rebalance_dates(
    index: pd.DatetimeIndex,
    window: int,
    schedule: RebalanceSchedule,
    config: ModelConfig,
) -> pd.DatetimeIndex:
    """Build the monthly primary or fixed-observation diagnostic schedule."""
    if schedule == "monthly":
        return monthly_rebalance_dates(index, window)
    interval_map = dict(
        zip(config.diagnostic_schedules, config.diagnostic_intervals, strict=True)
    )
    if schedule not in interval_map:
        raise PortfolioValidationError(f"unsupported rebalance schedule: {schedule}")
    if window < 2 or len(index) <= window:
        raise PortfolioValidationError("calendar cannot support the estimation window")
    positions = np.arange(window, len(index), interval_map[schedule], dtype=int)
    return index[positions]


def _caps(asset_classes: pd.Series, config: ModelConfig) -> np.ndarray:
    return np.where(
        asset_classes.eq("crypto").to_numpy(),
        config.crypto_asset_cap,
        config.equity_asset_cap,
    ).astype(float)


def _constraints(
    asset_classes: pd.Series, family: AssetFamily, config: ModelConfig
) -> list[dict[str, object]]:
    constraints: list[dict[str, object]] = [
        {
            "type": "eq",
            "fun": lambda weights: float(weights.sum() - 1.0),
            "jac": lambda weights: np.ones_like(weights),
        }
    ]
    if family == "combined":
        crypto = asset_classes.eq("crypto").to_numpy(dtype=float)
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda weights, mask=crypto: float(
                    config.combined_crypto_sleeve_cap - mask @ weights
                ),
                "jac": lambda weights, mask=crypto: -mask,
            }
        )
    return constraints


def _validate_feasibility(
    asset_classes: pd.Series, family: AssetFamily, config: ModelConfig
) -> None:
    caps = _caps(asset_classes, config)
    if caps.sum() < 1 - config.weight_tolerance:
        raise PortfolioValidationError(f"{family} individual caps are infeasible")
    if family == "combined":
        equity_capacity = caps[asset_classes.eq("equity").to_numpy()].sum()
        if equity_capacity < 1 - config.combined_crypto_sleeve_cap:
            raise PortfolioValidationError("combined equity capacity is infeasible")


def _equal_weight_start(
    asset_classes: pd.Series, family: AssetFamily, config: ModelConfig
) -> np.ndarray:
    """Return equal weights, projected only when a group cap requires it."""
    count = len(asset_classes)
    weights = np.repeat(1 / count, count)
    try:
        validate_weights(weights, asset_classes, family, config)
        return weights
    except PortfolioValidationError:
        crypto_mask = asset_classes.eq("crypto").to_numpy(dtype=float)
        feasible = linprog(
            np.zeros(count),
            A_ub=crypto_mask.reshape(1, -1) if family == "combined" else None,
            b_ub=[config.combined_crypto_sleeve_cap] if family == "combined" else None,
            A_eq=np.ones((1, count)),
            b_eq=[1.0],
            bounds=list(
                zip(np.zeros(count), _caps(asset_classes, config), strict=True)
            ),
            method="highs",
        )
        if not feasible.success:
            raise PortfolioValidationError("portfolio constraints have no feasible start")
        projected = minimize(
            lambda candidate: float(np.square(candidate - weights).sum()),
            feasible.x,
            jac=lambda candidate: 2 * (candidate - weights),
            method="SLSQP",
            bounds=list(
                zip(np.zeros(count), _caps(asset_classes, config), strict=True)
            ),
            constraints=_constraints(asset_classes, family, config),
            options={
                "ftol": config.solver_tolerance,
                "maxiter": config.solver_max_iterations,
            },
        )
        if not projected.success:
            raise PortfolioValidationError(
                f"constrained equal-weight projection failed: {projected.message}"
            )
        validate_weights(projected.x, asset_classes, family, config)
        return projected.x


def _project_weights(
    raw_weights: np.ndarray,
    asset_classes: pd.Series,
    family: AssetFamily,
    config: ModelConfig,
) -> np.ndarray:
    """Find the nearest feasible long-only vector to a proposed allocation."""
    raw = np.asarray(raw_weights, dtype=float)
    result = minimize(
        lambda weights: float(np.square(weights - raw).sum()),
        _equal_weight_start(asset_classes, family, config),
        jac=lambda weights: 2 * (weights - raw),
        method="SLSQP",
        bounds=list(zip(np.zeros(len(raw)), _caps(asset_classes, config), strict=True)),
        constraints=_constraints(asset_classes, family, config),
        options={
            "ftol": config.solver_tolerance,
            "maxiter": config.solver_max_iterations,
        },
    )
    if not result.success:
        raise PortfolioValidationError(f"weight projection failed: {result.message}")
    validate_weights(result.x, asset_classes, family, config)
    return result.x


def validate_weights(
    weights: np.ndarray,
    asset_classes: pd.Series,
    family: AssetFamily,
    config: ModelConfig,
) -> None:
    """Require finite, long-only, fully invested weights within all caps."""
    values = np.asarray(weights, dtype=float)
    tolerance = config.weight_tolerance
    if len(values) != len(asset_classes) or not np.isfinite(values).all():
        raise PortfolioValidationError("weights must be finite and match the universe")
    if values.min() < -tolerance:
        raise PortfolioValidationError("weights violate the long-only constraint")
    if abs(values.sum() - 1) > tolerance:
        raise PortfolioValidationError("weights are not fully invested")
    caps = _caps(asset_classes, config)
    if (values - caps > tolerance).any():
        raise PortfolioValidationError("weights violate an individual asset cap")
    if family == "combined":
        crypto_weight = values[asset_classes.eq("crypto").to_numpy()].sum()
        if crypto_weight > config.combined_crypto_sleeve_cap + tolerance:
            raise PortfolioValidationError("weights violate the combined crypto cap")


def annualized_moments(
    history: pd.DataFrame,
    annualization_days: int,
    config: ModelConfig,
    *,
    covariance_estimator: CovarianceEstimator = "sample_ridge",
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    """Estimate annualised means and the selected prior-only covariance."""
    if len(history) < 2 or history.isna().any().any():
        raise PortfolioValidationError("estimation history must be complete")
    values = history.to_numpy(dtype=float)
    expected_returns = values.mean(axis=0) * annualization_days
    sample_covariance = np.atleast_2d(
        np.cov(values, rowvar=False, ddof=1) * annualization_days
    )
    sample_condition_number = float(np.linalg.cond(sample_covariance))
    if covariance_estimator == "sample_ridge":
        average_variance = max(float(np.diag(sample_covariance).mean()), 1e-12)
        ridge_added = config.covariance_ridge * average_variance
        covariance = sample_covariance + np.eye(sample_covariance.shape[0]) * ridge_added
        shrinkage = np.nan
    elif covariance_estimator == "ledoit_wolf":
        try:
            from sklearn.covariance import LedoitWolf
        except ImportError as exc:  # pragma: no cover - environment-specific guard
            raise PortfolioValidationError(
                "Ledoit-Wolf requires requirements-dev.txt"
            ) from exc
        estimator = LedoitWolf(assume_centered=False).fit(values)
        covariance = np.atleast_2d(estimator.covariance_ * annualization_days)
        ridge_added = 0.0
        shrinkage = float(estimator.shrinkage_)
    else:
        raise PortfolioValidationError(
            f"unsupported covariance estimator: {covariance_estimator}"
        )
    minimum_eigenvalue = float(np.linalg.eigvalsh(covariance).min())
    if minimum_eigenvalue <= 0 or not np.isfinite(covariance).all():
        raise PortfolioValidationError("covariance estimate must be finite and positive definite")
    diagnostics = {
        "covariance_estimator": covariance_estimator,
        "covariance_shrinkage": shrinkage,
        "sample_covariance_condition_number": sample_condition_number,
        "covariance_trace": float(np.trace(covariance)),
        "covariance_condition_number": float(np.linalg.cond(covariance)),
        "covariance_minimum_eigenvalue": minimum_eigenvalue,
        "covariance_ridge_added": ridge_added,
        "expected_return_min": float(expected_returns.min()),
        "expected_return_max": float(expected_returns.max()),
    }
    return expected_returns, covariance, diagnostics


def _min_variance_result(
    covariance: np.ndarray,
    asset_classes: pd.Series,
    family: AssetFamily,
    config: ModelConfig,
    start: np.ndarray,
) -> OptimizeResult:
    return minimize(
        lambda weights: float(weights @ covariance @ weights),
        start,
        jac=lambda weights: 2 * covariance @ weights,
        method="SLSQP",
        bounds=list(
            zip(np.zeros(len(start)), _caps(asset_classes, config), strict=True)
        ),
        constraints=_constraints(asset_classes, family, config),
        options={
            "ftol": config.solver_tolerance,
            "maxiter": config.solver_max_iterations,
        },
    )


def _risk_parity_objective(
    weights: np.ndarray, covariance: np.ndarray
) -> tuple[float, np.ndarray]:
    marginal = covariance @ weights
    variance = float(weights @ marginal)
    if variance <= 0:
        return 1e12, np.zeros_like(weights)
    contributions = weights * marginal
    target = variance / len(weights)
    differences = contributions - target
    objective = float(differences @ differences / variance**2)
    jacobian = (
        np.diag(marginal)
        + np.diag(weights) @ covariance
        - np.outer(np.ones(len(weights)), 2 * marginal / len(weights))
    )
    gradient = (
        2 * jacobian.T @ differences / variance**2
        - 4 * float(differences @ differences) * marginal / variance**3
    )
    return objective, gradient


def _return_seeking_start(
    expected_returns: np.ndarray,
    asset_classes: pd.Series,
    family: AssetFamily,
    config: ModelConfig,
) -> np.ndarray:
    crypto_mask = asset_classes.eq("crypto").to_numpy(dtype=float)
    a_ub = crypto_mask.reshape(1, -1) if family == "combined" else None
    b_ub = [config.combined_crypto_sleeve_cap] if family == "combined" else None
    result = linprog(
        -expected_returns,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=np.ones((1, len(expected_returns))),
        b_eq=[1.0],
        bounds=list(
            zip(
                np.zeros(len(expected_returns)),
                _caps(asset_classes, config),
                strict=True,
            )
        ),
        method="highs",
    )
    if not result.success:
        return _equal_weight_start(asset_classes, family, config)
    return result.x


def _maximum_sharpe_result(
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    asset_classes: pd.Series,
    family: AssetFamily,
    config: ModelConfig,
    starts: list[np.ndarray],
) -> tuple[OptimizeResult, int]:
    excess = expected_returns - config.risk_free_rate_annual

    def objective(weights: np.ndarray) -> float:
        volatility = np.sqrt(max(float(weights @ covariance @ weights), 1e-18))
        return -float(excess @ weights) / volatility

    def gradient(weights: np.ndarray) -> np.ndarray:
        covariance_weight = covariance @ weights
        variance = max(float(weights @ covariance_weight), 1e-18)
        volatility = np.sqrt(variance)
        numerator = float(excess @ weights)
        return -(excess / volatility - numerator * covariance_weight / volatility**3)

    candidates: list[OptimizeResult] = []
    for start in starts:
        result = minimize(
            objective,
            start,
            jac=gradient,
            method="SLSQP",
            bounds=list(
                zip(np.zeros(len(start)), _caps(asset_classes, config), strict=True)
            ),
            constraints=_constraints(asset_classes, family, config),
            options={
                "ftol": config.solver_tolerance,
                "maxiter": config.solver_max_iterations,
            },
        )
        if result.success:
            try:
                validate_weights(result.x, asset_classes, family, config)
            except PortfolioValidationError:
                continue
            candidates.append(result)
    if not candidates:
        raise PortfolioValidationError("maximum-Sharpe optimisation has no valid solution")
    return min(candidates, key=lambda result: float(result.fun)), len(candidates)


def _effective_bets_result(
    covariance: np.ndarray,
    asset_classes: pd.Series,
    family: AssetFamily,
    config: ModelConfig,
    starts: list[np.ndarray],
) -> tuple[OptimizeResult, int]:
    """Maximise PCA effective-bet entropy from deterministic feasible starts."""
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)

    def objective(weights: np.ndarray) -> tuple[float, np.ndarray]:
        exposures = eigenvectors.T @ weights
        contributions = eigenvalues * np.square(exposures)
        variance = float(contributions.sum())
        distribution = np.clip(contributions / variance, 0.0, None)
        distribution /= distribution.sum()
        positive = distribution > 0
        entropy = -float(
            distribution[positive] @ np.log(distribution[positive])
        )
        safe_distribution = np.clip(distribution, 1e-300, None)
        factor_gradient = (
            2
            * eigenvalues
            * exposures
            * (entropy + np.log(safe_distribution))
            / variance
        )
        return -entropy, eigenvectors @ factor_gradient

    candidates: list[OptimizeResult] = []
    for start in starts:
        result = minimize(
            objective,
            start,
            jac=True,
            method="SLSQP",
            bounds=list(
                zip(np.zeros(len(start)), _caps(asset_classes, config), strict=True)
            ),
            constraints=_constraints(asset_classes, family, config),
            options={
                "ftol": config.solver_tolerance,
                "maxiter": config.solver_max_iterations,
            },
        )
        if result.success:
            try:
                validate_weights(result.x, asset_classes, family, config)
            except PortfolioValidationError:
                continue
            candidates.append(result)
    if not candidates:
        raise PortfolioValidationError(
            "effective-bets optimisation has no valid solution"
        )
    best_objective = min(float(result.fun) for result in candidates)
    near_best = [
        result
        for result in candidates
        if float(result.fun) <= best_objective + 1e-8
    ]
    selected = min(
        near_best,
        key=lambda result: float(result.x @ covariance @ result.x),
    )
    return selected, len(candidates)


def solve_weights(
    history: pd.DataFrame,
    asset_classes: pd.Series,
    family: AssetFamily,
    method: PortfolioMethod,
    annualization_days: int,
    config: ModelConfig,
    *,
    covariance_estimator: CovarianceEstimator = "sample_ridge",
) -> WeightSolution:
    """Estimate one target vector using only the supplied trailing history."""
    if list(history.columns) != list(asset_classes.index):
        raise PortfolioValidationError("asset-class map does not match return columns")
    _validate_feasibility(asset_classes, family, config)
    equal = _equal_weight_start(asset_classes, family, config)
    expected, covariance, moment_diagnostics = annualized_moments(
        history,
        annualization_days,
        config,
        covariance_estimator=covariance_estimator,
    )
    solver_success = True
    solver_status = 0
    solver_message = "closed-form feasible equal weight"
    solver_iterations = 0
    valid_start_count = 1
    method_diagnostics: dict[str, object] = {}

    if method == "equal_weight":
        weights = equal
        objective_value = float(weights @ covariance @ weights)
    elif method == "minimum_variance":
        result = _min_variance_result(
            covariance, asset_classes, family, config, equal
        )
        if not result.success:
            raise PortfolioValidationError(
                f"minimum-variance optimisation failed: {result.message}"
            )
        weights = result.x
        objective_value = float(result.fun)
        solver_status = int(result.status)
        solver_message = str(result.message)
        solver_iterations = int(result.nit)
    elif method == "risk_parity":
        inverse_volatility = 1 / np.sqrt(np.diag(covariance))
        start = _project_weights(
            inverse_volatility / inverse_volatility.sum(),
            asset_classes,
            family,
            config,
        )
        result = minimize(
            lambda weights: _risk_parity_objective(weights, covariance)[0],
            start,
            jac=lambda weights: _risk_parity_objective(weights, covariance)[1],
            method="SLSQP",
            bounds=list(
                zip(np.zeros(len(start)), _caps(asset_classes, config), strict=True)
            ),
            constraints=_constraints(asset_classes, family, config),
            options={
                "ftol": config.solver_tolerance,
                "maxiter": config.solver_max_iterations,
            },
        )
        if not result.success:
            raise PortfolioValidationError(f"risk-parity optimisation failed: {result.message}")
        weights = result.x
        objective_value = float(result.fun)
        solver_status = int(result.status)
        solver_message = str(result.message)
        solver_iterations = int(result.nit)
    elif method == "maximum_sharpe":
        minimum_variance = _min_variance_result(
            covariance, asset_classes, family, config, equal
        )
        starts = [equal, _return_seeking_start(expected, asset_classes, family, config)]
        if minimum_variance.success:
            starts.append(minimum_variance.x)
        result, valid_start_count = _maximum_sharpe_result(
            expected,
            covariance,
            asset_classes,
            family,
            config,
            starts,
        )
        weights = result.x
        objective_value = float(result.fun)
        solver_status = int(result.status)
        solver_message = str(result.message)
        solver_iterations = int(result.nit)
    elif method == "effective_bets":
        inverse_volatility = 1 / np.sqrt(np.diag(covariance))
        inverse_volatility = _project_weights(
            inverse_volatility / inverse_volatility.sum(),
            asset_classes,
            family,
            config,
        )
        minimum_variance = _min_variance_result(
            covariance, asset_classes, family, config, equal
        )
        starts = [equal, inverse_volatility]
        if minimum_variance.success:
            starts.append(minimum_variance.x)
        risk_parity = minimize(
            lambda candidate: _risk_parity_objective(candidate, covariance)[0],
            inverse_volatility,
            jac=lambda candidate: _risk_parity_objective(candidate, covariance)[1],
            method="SLSQP",
            bounds=list(
                zip(np.zeros(len(equal)), _caps(asset_classes, config), strict=True)
            ),
            constraints=_constraints(asset_classes, family, config),
            options={
                "ftol": config.solver_tolerance,
                "maxiter": config.solver_max_iterations,
            },
        )
        if risk_parity.success:
            starts.append(risk_parity.x)
        generator = np.random.default_rng(config.random_seed)
        for _ in range(3):
            starts.append(
                _project_weights(
                    generator.dirichlet(np.ones(len(equal))),
                    asset_classes,
                    family,
                    config,
                )
            )
        result, valid_start_count = _effective_bets_result(
            covariance,
            asset_classes,
            family,
            config,
            starts,
        )
        weights = result.x
        objective_value = float(result.fun)
        solver_status = int(result.status)
        solver_message = str(result.message)
        solver_iterations = int(result.nit)
    elif method == "hierarchical_risk_parity":
        hrp = hierarchical_risk_parity(covariance, history.columns)
        raw_weights = hrp.weights.to_numpy(dtype=float)
        raw_crypto_sleeve = float(
            raw_weights[asset_classes.eq("crypto").to_numpy()].sum()
        )
        try:
            validate_weights(raw_weights, asset_classes, family, config)
            weights = raw_weights
            projected = False
        except PortfolioValidationError:
            weights = _project_weights(
                raw_weights,
                asset_classes,
                family,
                config,
            )
            projected = True
        objective_value = float(weights @ covariance @ weights)
        solver_message = (
            "standard single-linkage HRP; projected to approved constraints"
            if projected
            else "standard single-linkage HRP; raw weights feasible"
        )
        method_diagnostics = {
            **hrp.diagnostics,
            "constraint_projection_applied": projected,
            "projection_l1_distance": float(np.abs(weights - raw_weights).sum()),
            "raw_maximum_weight": float(raw_weights.max()),
            "raw_weight_hhi": float(raw_weights @ raw_weights),
            "raw_crypto_sleeve_weight": raw_crypto_sleeve,
            "ordered_asset_signature": "|".join(hrp.ordered_assets),
        }
    elif method == "conditional_value_at_risk":
        from src.conditional_value_at_risk import minimum_cvar

        cvar = minimum_cvar(
            history,
            asset_classes,
            family,
            config,
        )
        weights = cvar.weights.to_numpy(dtype=float)
        objective_value = cvar.cvar
        solver_status = cvar.solver_status
        solver_message = cvar.solver_message
        method_diagnostics = {
            "cvar_confidence": config.cvar_confidence,
            "estimated_daily_var": cvar.var,
            "estimated_daily_cvar": cvar.cvar,
            "tail_scenario_count": cvar.tail_scenario_count,
        }
    else:
        raise PortfolioValidationError(f"unsupported portfolio method: {method}")

    validate_weights(weights, asset_classes, family, config)
    covariance_weight = covariance @ weights
    portfolio_variance = float(weights @ covariance_weight)
    risk_contributions = weights * covariance_weight
    normalised_contributions = risk_contributions / portfolio_variance
    caps = _caps(asset_classes, config)
    crypto_mask = asset_classes.eq("crypto").to_numpy()
    diagnostics: dict[str, object] = {
        **moment_diagnostics,
        "solver_success": solver_success,
        "solver_status": solver_status,
        "solver_message": solver_message,
        "solver_iterations": solver_iterations,
        "valid_start_count": valid_start_count,
        "objective_value": objective_value,
        "expected_portfolio_return": float(expected @ weights),
        "expected_portfolio_volatility": float(np.sqrt(portfolio_variance)),
        "expected_sharpe": float(
            (expected @ weights - config.risk_free_rate_annual)
            / np.sqrt(portfolio_variance)
        ),
        "weight_sum_residual": float(abs(weights.sum() - 1)),
        "maximum_bound_residual": float(max(0.0, np.max(weights - caps))),
        "minimum_weight": float(weights.min()),
        "maximum_weight": float(weights.max()),
        "crypto_sleeve_weight": float(weights[crypto_mask].sum()),
        "weight_hhi": float(weights @ weights),
        "risk_contribution_dispersion": float(
            np.sqrt(np.mean(np.square(normalised_contributions - 1 / len(weights))))
        ),
        "effective_number_of_bets": effective_number_of_bets(weights, covariance),
        "effective_bet_ratio": effective_number_of_bets(weights, covariance)
        / len(weights),
        **method_diagnostics,
    }
    return WeightSolution(
        pd.Series(weights, index=history.columns, name="target_weight"), diagnostics
    )


def _drift_weights(weights: np.ndarray, asset_returns: np.ndarray) -> np.ndarray:
    gross_return = float(weights @ asset_returns)
    if gross_return <= -1:
        raise PortfolioValidationError("portfolio return prevents weight drift")
    drifted = weights * (1 + asset_returns) / (1 + gross_return)
    if not np.isfinite(drifted).all() or abs(drifted.sum() - 1) > 1e-8:
        raise PortfolioValidationError("drifted weights are invalid")
    return drifted


def oos_backtest(
    panel: FamilyPanel,
    method: PortfolioMethod = "minimum_variance",
    *,
    config: ModelConfig,
    rebalance_schedule: RebalanceSchedule | None = None,
    transaction_cost_bps: float | None = None,
    solution_cache: dict[
        tuple[
            AssetFamily,
            PortfolioMethod,
            CovarianceEstimator,
            pd.Timestamp,
            int,
        ],
        WeightSolution,
    ]
    | None = None,
    covariance_estimator: CovarianceEstimator = "sample_ridge",
) -> FundBacktest:
    """Run one prior-only, drift-aware out-of-sample fund backtest."""
    returns = panel.returns
    schedule = rebalance_schedule or config.primary_schedule
    schedule_dates = rebalance_dates(
        returns.index, panel.estimation_window, schedule, config
    )
    rebalance_set = set(schedule_dates)
    first_live = schedule_dates[0]
    current_weights: np.ndarray | None = None
    return_records: list[dict[str, object]] = []
    weight_records: list[dict[str, object]] = []
    diagnostic_records: list[dict[str, object]] = []
    portfolio_id = fund_id(panel.family, method)
    portfolio_name = fund_name(panel.family, method)
    applied_cost_bps = (
        config.transaction_cost_bps
        if transaction_cost_bps is None
        else transaction_cost_bps
    )
    if applied_cost_bps < 0:
        raise PortfolioValidationError("transaction cost must be nonnegative")
    cost_rate = applied_cost_bps / 10_000
    rebalance_number = 0

    for date in returns.loc[first_live:].index:
        position = returns.index.get_loc(date)
        asset_returns = returns.loc[date].to_numpy(dtype=float)
        transaction_cost = 0.0
        turnover = 0.0
        rebalanced = date in rebalance_set
        if rebalanced:
            history = returns.iloc[
                position - panel.estimation_window : position
            ]
            if history.index.max() >= date:
                raise PortfolioValidationError("estimation history reaches the live date")
            cache_key = (
                panel.family,
                method,
                covariance_estimator,
                pd.Timestamp(date),
                panel.estimation_window,
            )
            solution = solution_cache.get(cache_key) if solution_cache is not None else None
            if solution is None:
                solution = solve_weights(
                    history,
                    panel.asset_classes,
                    panel.family,
                    method,
                    panel.annualization_days,
                    config,
                    covariance_estimator=covariance_estimator,
                )
                if solution_cache is not None:
                    solution_cache[cache_key] = solution
            target = solution.weights.to_numpy(dtype=float)
            pretrade = (
                np.zeros_like(target) if current_weights is None else current_weights.copy()
            )
            turnover = (
                1.0
                if current_weights is None
                else float(0.5 * np.abs(target - pretrade).sum())
            )
            transaction_cost = turnover * cost_rate
            current_weights = target
            rebalance_number += 1
            common = {
                "fund_id": portfolio_id,
                "fund_name": portfolio_name,
                "asset_family": panel.family,
                "method": method,
                "rebalance_schedule": schedule,
                "rebalance_number": rebalance_number,
                "rebalance_date": date,
                "estimation_start": history.index.min(),
                "estimation_end": history.index.max(),
                "first_held_return_date": date,
                "estimation_observations": len(history),
                "annualization_days": panel.annualization_days,
                "eligible_asset_count": len(returns.columns),
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "transaction_cost_bps": applied_cost_bps,
            }
            diagnostic_records.append({**common, **solution.diagnostics})
            for asset, target_weight, pretrade_weight, asset_class in zip(
                returns.columns,
                target,
                pretrade,
                panel.asset_classes,
                strict=True,
            ):
                weight_records.append(
                    {
                        **common,
                        "asset": asset,
                        "asset_class": asset_class,
                        "pretrade_weight": pretrade_weight,
                        "target_weight": target_weight,
                        "individual_cap": (
                            config.crypto_asset_cap
                            if asset_class == "crypto"
                            else config.equity_asset_cap
                        ),
                        "combined_crypto_sleeve_cap": (
                            config.combined_crypto_sleeve_cap
                            if panel.family == "combined"
                            else np.nan
                        ),
                    }
                )
        if current_weights is None:
            raise PortfolioValidationError("live return encountered before first rebalance")
        gross_return = float(current_weights @ asset_returns)
        net_return = gross_return - transaction_cost
        if net_return <= -1:
            raise PortfolioValidationError("transaction costs create an invalid net return")
        return_records.append(
            {
                "date": date,
                "fund_id": portfolio_id,
                "fund_name": portfolio_name,
                "asset_family": panel.family,
                "method": method,
                "rebalance_schedule": schedule,
                "rebalanced": rebalanced,
                "gross_return": gross_return,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "net_return": net_return,
            }
        )
        current_weights = _drift_weights(current_weights, asset_returns)

    daily = pd.DataFrame.from_records(return_records)
    daily["growth_of_1_gross"] = (1 + daily["gross_return"]).cumprod()
    daily["growth_of_1_net"] = (1 + daily["net_return"]).cumprod()
    daily["drawdown_net"] = (
        daily["growth_of_1_net"] / daily["growth_of_1_net"].cummax() - 1
    )
    weights = pd.DataFrame.from_records(weight_records)
    diagnostics = pd.DataFrame.from_records(diagnostic_records)
    return FundBacktest(daily, weights, diagnostics)


def performance_metrics(
    daily_returns: pd.Series,
    periods_per_year: int = 252,
    *,
    risk_free_rate_annual: float = 0.0,
) -> dict[str, float | int]:
    """Calculate CAGR, volatility, Sharpe, growth, and maximum drawdown."""
    values = pd.Series(daily_returns, dtype="float64").dropna()
    if len(values) < 2 or not np.isfinite(values).all() or values.le(-1).any():
        raise PortfolioValidationError("daily returns cannot support performance metrics")
    growth = (1 + values).cumprod()
    ending_growth = float(growth.iloc[-1])
    years = len(values) / periods_per_year
    annualized_return = ending_growth ** (1 / years) - 1
    daily_risk_free = (1 + risk_free_rate_annual) ** (1 / periods_per_year) - 1
    daily_volatility = float(values.std(ddof=1))
    annualized_volatility = daily_volatility * np.sqrt(periods_per_year)
    sharpe = (
        float((values.mean() - daily_risk_free) / daily_volatility * np.sqrt(periods_per_year))
        if daily_volatility > 0
        else np.nan
    )
    drawdown = growth / growth.cummax() - 1
    return {
        "observation_count": len(values),
        "ending_growth_of_1": ending_growth,
        "cumulative_return": ending_growth - 1,
        "annualized_return": annualized_return,
        "annualized_arithmetic_return": float(values.mean() * periods_per_year),
        "annualized_volatility": annualized_volatility,
        "sharpe_ratio": sharpe,
        "maximum_drawdown": float(drawdown.min()),
        "positive_return_share": float(values.gt(0).mean()),
    }


def _prefix_metrics(metrics: dict[str, object], prefix: str) -> dict[str, object]:
    return {f"{prefix}_{key}": value for key, value in metrics.items()}


def _build_metrics(
    fund_returns: pd.DataFrame,
    fund_weights: pd.DataFrame,
    config: ModelConfig,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for portfolio_id, daily in fund_returns.groupby("fund_id", sort=True):
        first = daily.iloc[0]
        annualization_days = 365 if first["asset_family"] == "crypto" else 252
        gross = performance_metrics(
            daily["gross_return"],
            annualization_days,
            risk_free_rate_annual=config.risk_free_rate_annual,
        )
        net = performance_metrics(
            daily["net_return"],
            annualization_days,
            risk_free_rate_annual=config.risk_free_rate_annual,
        )
        rebalances = fund_weights.loc[fund_weights["fund_id"].eq(portfolio_id)].drop_duplicates(
            "rebalance_date"
        )
        portfolio_weights = fund_weights.loc[
            fund_weights["fund_id"].eq(portfolio_id)
        ].copy()
        concentration = portfolio_weights.groupby("rebalance_date")[
            "target_weight"
        ].apply(lambda weights: float(np.square(weights).sum()))
        crypto_sleeves = portfolio_weights.groupby("rebalance_date").apply(
            lambda frame: float(
                frame.loc[frame["asset_class"].eq("crypto"), "target_weight"].sum()
            ),
            include_groups=False,
        )
        records.append(
            {
                "fund_id": portfolio_id,
                "fund_name": first["fund_name"],
                "asset_family": first["asset_family"],
                "method": first["method"],
                "rebalance_schedule": config.primary_schedule,
                "first_live_date": daily["date"].min(),
                "last_live_date": daily["date"].max(),
                "annualization_days": annualization_days,
                "risk_free_rate_annual": config.risk_free_rate_annual,
                "transaction_cost_bps": config.transaction_cost_bps,
                **_prefix_metrics(gross, "gross"),
                **_prefix_metrics(net, "net"),
                "annualized_return": net["annualized_return"],
                "annualized_volatility": net["annualized_volatility"],
                "sharpe_ratio": net["sharpe_ratio"],
                "maximum_drawdown": net["maximum_drawdown"],
                "rebalance_count": len(rebalances),
                "average_rebalance_turnover": float(rebalances["turnover"].mean()),
                "cumulative_turnover": float(rebalances["turnover"].sum()),
                "total_transaction_cost": float(rebalances["transaction_cost"].sum()),
                "average_target_weight_hhi": float(concentration.mean()),
                "maximum_target_weight_hhi": float(concentration.max()),
                "latest_target_weight_hhi": float(concentration.iloc[-1]),
                "latest_effective_number_of_assets": float(1 / concentration.iloc[-1]),
                "average_crypto_sleeve_weight": float(crypto_sleeves.mean()),
                "latest_crypto_sleeve_weight": float(crypto_sleeves.iloc[-1]),
                "cost_drag_ending_growth": (
                    gross["ending_growth_of_1"] - net["ending_growth_of_1"]
                ),
            }
        )
    metrics = pd.DataFrame.from_records(records)
    benchmark = metrics.loc[metrics["method"].eq("equal_weight")].set_index(
        "asset_family"
    )
    relative_records: list[dict[str, object]] = []
    for row in metrics.itertuples(index=False):
        benchmark_id = benchmark.loc[row.asset_family, "fund_id"]
        fund_daily = fund_returns.loc[fund_returns["fund_id"].eq(row.fund_id)].set_index(
            "date"
        )
        benchmark_daily = fund_returns.loc[
            fund_returns["fund_id"].eq(benchmark_id)
        ].set_index("date")
        joined = fund_daily[["net_return"]].join(
            benchmark_daily[["net_return"]],
            how="inner",
            lsuffix="_fund",
            rsuffix="_benchmark",
        )
        active = joined["net_return_fund"] - joined["net_return_benchmark"]
        tracking_error = float(active.std(ddof=1) * np.sqrt(row.annualization_days))
        information_ratio = (
            float(active.mean() / active.std(ddof=1) * np.sqrt(row.annualization_days))
            if active.std(ddof=1) > 0
            else np.nan
        )
        benchmark_return = float(
            benchmark.loc[row.asset_family, "annualized_return"]
        )
        relative_records.append(
            {
                "fund_id": row.fund_id,
                "benchmark_fund_id": benchmark_id,
                "benchmark_annualized_return": benchmark_return,
                "annualized_return_vs_benchmark": row.annualized_return
                - benchmark_return,
                "tracking_error": tracking_error,
                "information_ratio": information_ratio,
            }
        )
    return metrics.merge(
        pd.DataFrame.from_records(relative_records), on="fund_id", validate="one_to_one"
    ).sort_values(["asset_family", "method"], kind="stable").reset_index(drop=True)


def _method_distinctness(fund_weights: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for family, family_weights in fund_weights.groupby("asset_family", sort=True):
        methods = sorted(family_weights["method"].unique())
        for method_a, method_b in combinations(methods, 2):
            first = family_weights.loc[family_weights["method"].eq(method_a), [
                "rebalance_date",
                "asset",
                "target_weight",
            ]]
            second = family_weights.loc[family_weights["method"].eq(method_b), [
                "rebalance_date",
                "asset",
                "target_weight",
            ]]
            comparison = first.merge(
                second,
                on=["rebalance_date", "asset"],
                suffixes=("_a", "_b"),
                validate="one_to_one",
            )
            distance = comparison.assign(
                absolute_difference=(
                    comparison["target_weight_a"] - comparison["target_weight_b"]
                ).abs()
            ).groupby("rebalance_date")["absolute_difference"].sum()
            records.append(
                {
                    "asset_family": family,
                    "method_a": method_a,
                    "method_b": method_b,
                    "common_rebalance_count": len(distance),
                    "mean_l1_weight_distance": float(distance.mean()),
                    "minimum_l1_weight_distance": float(distance.min()),
                    "maximum_l1_weight_distance": float(distance.max()),
                    "economically_distinct": bool(distance.mean() > 1e-3),
                }
            )
    return pd.DataFrame.from_records(records)


def _fact_sheets(
    metrics: pd.DataFrame, fund_weights: pd.DataFrame, config: ModelConfig
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for row in metrics.itertuples(index=False):
        weights = fund_weights.loc[fund_weights["fund_id"].eq(row.fund_id)]
        latest_date = weights["rebalance_date"].max()
        latest = weights.loc[weights["rebalance_date"].eq(latest_date)].sort_values(
            "target_weight", ascending=False, kind="stable"
        )
        holdings = "; ".join(
            f"{asset} {weight:.2%}"
            for asset, weight in latest[["asset", "target_weight"]]
            .head(10)
            .itertuples(index=False, name=None)
        )
        all_holdings = "; ".join(
            f"{asset} {weight:.4%}"
            for asset, weight in latest[["asset", "target_weight"]]
            .loc[latest["target_weight"].gt(config.weight_tolerance)]
            .itertuples(index=False, name=None)
        )
        latest_hhi = float(np.square(latest["target_weight"]).sum())
        records.append(
            {
                "fund_id": row.fund_id,
                "fund_name": row.fund_name,
                "asset_family": row.asset_family,
                "method": row.method,
                "first_live_date": row.first_live_date,
                "last_live_date": row.last_live_date,
                "latest_rebalance_date": latest_date,
                "growth_of_1_net": row.net_ending_growth_of_1,
                "annualized_return": row.annualized_return,
                "annualized_volatility": row.annualized_volatility,
                "sharpe_ratio": row.sharpe_ratio,
                "maximum_drawdown": row.maximum_drawdown,
                "average_rebalance_turnover": row.average_rebalance_turnover,
                "cumulative_turnover": row.cumulative_turnover,
                "total_transaction_cost": row.total_transaction_cost,
                "latest_weight_hhi": latest_hhi,
                "latest_effective_number_of_assets": float(1 / latest_hhi),
                "latest_crypto_sleeve_weight": float(
                    latest.loc[latest["asset_class"].eq("crypto"), "target_weight"].sum()
                ),
                "latest_nonzero_holding_count": int(
                    latest["target_weight"].gt(config.weight_tolerance).sum()
                ),
                "latest_top_10_weight": float(latest["target_weight"].head(10).sum()),
                "latest_top_10_holdings": holdings,
                "latest_all_nonzero_holdings": all_holdings,
                "benchmark_fund_id": row.benchmark_fund_id,
                "annualized_return_vs_benchmark": row.annualized_return_vs_benchmark,
                "tracking_error": row.tracking_error,
                "information_ratio": row.information_ratio,
                "estimation_window": (
                    config.crypto_window
                    if row.asset_family == "crypto"
                    else config.equity_window
                ),
                "rebalance_rule": "first observed date of each month",
                "transaction_cost_bps": config.transaction_cost_bps,
                "risk_free_rate_annual": config.risk_free_rate_annual,
                "evidence_label": "walk-forward out-of-sample historical simulation",
                "evidence_limit": (
                    "historical 2021-2023 simulation; past simulated performance "
                    "is not a forecast"
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def _configuration_table(config: ModelConfig) -> pd.DataFrame:
    values = {
        "equity_window": config.equity_window,
        "crypto_window": config.crypto_window,
        "combined_window": config.combined_window,
        "primary_schedule": config.primary_schedule,
        "diagnostic_intervals": ",".join(map(str, config.diagnostic_intervals)),
        "diagnostic_schedules": ",".join(config.diagnostic_schedules),
        "risk_free_rate_annual": config.risk_free_rate_annual,
        "equity_asset_cap": config.equity_asset_cap,
        "crypto_asset_cap": config.crypto_asset_cap,
        "combined_crypto_sleeve_cap": config.combined_crypto_sleeve_cap,
        "transaction_cost_bps": config.transaction_cost_bps,
        "transaction_cost_sensitivities_bps": ",".join(
            map(str, config.transaction_cost_sensitivities_bps)
        ),
        "fusion_base_method": config.fusion_base_method,
        "fusion_tilt_strength": config.fusion_tilt_strength,
        "fusion_tilt_strength_sensitivities": ",".join(
            map(str, config.fusion_tilt_strength_sensitivities)
        ),
        "fusion_signal_z_cap": config.fusion_signal_z_cap,
        "covariance_ridge": config.covariance_ridge,
        "solver_tolerance": config.solver_tolerance,
        "solver_max_iterations": config.solver_max_iterations,
        "weight_tolerance": config.weight_tolerance,
        "random_seed": config.random_seed,
        "methods": ",".join(config.methods),
        "frequency_experiment_methods": ",".join(
            config.frequency_experiment_methods
        ),
        "families": ",".join(config.families),
    }
    return pd.DataFrame(
        [
            {
                "setting": setting,
                "value": value,
                "configuration_role": "approved primary model configuration",
            }
            for setting, value in values.items()
        ]
    )


def _validation_summary(
    fund_returns: pd.DataFrame,
    fund_weights: pd.DataFrame,
    metrics: pd.DataFrame,
    diagnostics: pd.DataFrame,
    distinctness: pd.DataFrame,
    config: ModelConfig,
) -> pd.DataFrame:
    combined = diagnostics.loc[diagnostics["asset_family"].eq("combined")]
    checks = (
        (
            "fund_count",
            int(metrics["fund_id"].nunique()),
            len(config.families) * len(config.methods),
            "equal",
        ),
        (
            "duplicate_fund_date_rows",
            int(fund_returns.duplicated(["fund_id", "date"]).sum()),
            0,
            "equal",
        ),
        (
            "duplicate_fund_rebalance_asset_rows",
            int(
                fund_weights.duplicated(
                    ["fund_id", "rebalance_date", "asset"]
                ).sum()
            ),
            0,
            "equal",
        ),
        (
            "temporal_order_violations",
            int(
                diagnostics["estimation_end"]
                .ge(diagnostics["first_held_return_date"])
                .sum()
            ),
            0,
            "equal",
        ),
        (
            "solver_failure_count",
            int(diagnostics["solver_success"].ne(True).sum()),
            0,
            "equal",
        ),
        (
            "maximum_weight_sum_residual",
            float(diagnostics["weight_sum_residual"].max()),
            config.weight_tolerance,
            "maximum",
        ),
        (
            "maximum_bound_residual",
            float(diagnostics["maximum_bound_residual"].max()),
            config.weight_tolerance,
            "maximum",
        ),
        (
            "maximum_combined_crypto_sleeve",
            float(combined["crypto_sleeve_weight"].max()),
            config.combined_crypto_sleeve_cap + config.weight_tolerance,
            "maximum",
        ),
        (
            "nondistinct_method_pair_count",
            int((~distinctness["economically_distinct"]).sum()),
            0,
            "equal",
        ),
        (
            "nonfinite_primary_metric_count",
            int(
                (~np.isfinite(
                    metrics[
                        [
                            "annualized_return",
                            "annualized_volatility",
                            "sharpe_ratio",
                            "maximum_drawdown",
                        ]
                    ].to_numpy(dtype=float)
                )).sum()
            ),
            0,
            "equal",
        ),
    )
    records: list[dict[str, object]] = []
    for check, value, threshold, rule in checks:
        passed = value == threshold if rule == "equal" else value <= threshold
        records.append(
            {
                "check": check,
                "observed_value": value,
                "pass_rule": f"{rule} {threshold}",
                "status": "pass" if passed else "fail",
            }
        )
    return pd.DataFrame.from_records(records)


def build_portfolio_suite(
    features: ReturnFeatures, config: ModelConfig
) -> PortfolioSuite:
    """Build the approved 15 monthly funds from the Phase 1 return features."""
    panels = build_family_panels(features, config)
    backtests: list[FundBacktest] = []
    for family in config.families:
        for method in config.methods:
            backtests.append(oos_backtest(panels[family], method, config=config))
    fund_returns = pd.concat(
        [backtest.fund_returns for backtest in backtests], ignore_index=True
    ).sort_values(["fund_id", "date"], kind="stable").reset_index(drop=True)
    fund_weights = pd.concat(
        [backtest.fund_weights for backtest in backtests], ignore_index=True
    ).sort_values(
        ["fund_id", "rebalance_date", "asset"], kind="stable"
    ).reset_index(drop=True)
    diagnostics = pd.concat(
        [backtest.diagnostics for backtest in backtests], ignore_index=True
    ).sort_values(["fund_id", "rebalance_date"], kind="stable").reset_index(drop=True)
    metrics = _build_metrics(fund_returns, fund_weights, config)
    distinctness = _method_distinctness(fund_weights)
    if diagnostics["solver_success"].ne(True).any():
        raise PortfolioValidationError("one or more optimiser diagnostics failed")
    if not distinctness["economically_distinct"].all():
        collapsed = distinctness.loc[
            ~distinctness["economically_distinct"],
            ["asset_family", "method_a", "method_b"],
        ].to_dict("records")
        raise PortfolioValidationError(f"portfolio methods are not distinct: {collapsed}")
    validation = _validation_summary(
        fund_returns, fund_weights, metrics, diagnostics, distinctness, config
    )
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise PortfolioValidationError(f"portfolio suite validation failed: {failures}")
    return PortfolioSuite(
        fund_returns=fund_returns,
        fund_weights=fund_weights,
        performance_metrics=metrics,
        rebalance_diagnostics=diagnostics,
        method_distinctness=distinctness,
        fund_fact_sheets=_fact_sheets(metrics, fund_weights, config),
        model_configuration=_configuration_table(config),
        validation_summary=validation,
    )


def save_portfolio_outputs(
    suite: PortfolioSuite, *, data_dir: Path, tables_dir: Path
) -> list[Path]:
    """Write required marker/app files and supporting Phase 2 evidence."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "fund_returns.csv": suite.fund_returns,
        data_dir / "fund_weights.csv": suite.fund_weights,
        tables_dir / "performance_metrics.csv": suite.performance_metrics,
        tables_dir / "rebalance_diagnostics.csv": suite.rebalance_diagnostics,
        tables_dir / "method_distinctness.csv": suite.method_distinctness,
        tables_dir / "fund_fact_sheets.csv": suite.fund_fact_sheets,
        tables_dir / "model_configuration.csv": suite.model_configuration,
        tables_dir / "portfolio_validation_summary.csv": suite.validation_summary,
    }
    paths: list[Path] = []
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


__all__ = [
    "FAMILY_LABELS",
    "METHOD_LABELS",
    "FamilyPanel",
    "FundBacktest",
    "PortfolioSuite",
    "PortfolioValidationError",
    "WeightSolution",
    "annualized_moments",
    "build_family_panels",
    "build_portfolio_suite",
    "fund_id",
    "fund_name",
    "monthly_rebalance_dates",
    "oos_backtest",
    "performance_metrics",
    "rebalance_dates",
    "save_portfolio_outputs",
    "solve_weights",
    "validate_weights",
]
