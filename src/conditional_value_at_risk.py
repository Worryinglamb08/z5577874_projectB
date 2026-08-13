"""Historical minimum-CVaR portfolio optimisation for isolated experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from src.config import AssetFamily, ModelConfig


@dataclass(frozen=True)
class CvarSolution:
    """A feasible target and its historical tail-loss diagnostics."""

    weights: pd.Series
    var: float
    cvar: float
    tail_scenario_count: int
    solver_status: int
    solver_message: str


def minimum_cvar(
    history: pd.DataFrame,
    asset_classes: pd.Series,
    family: AssetFamily,
    config: ModelConfig,
) -> CvarSolution:
    """Minimise historical Expected Shortfall under the approved product caps.

    The Rockafellar-Uryasev linear programme uses one loss scenario per trailing
    return observation. No expected-return target is imposed.
    """
    if history.empty or list(history.columns) != list(asset_classes.index):
        raise ValueError("CVaR history and asset-class map must align")
    values = history.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("CVaR history must contain only finite returns")
    observation_count, asset_count = values.shape
    confidence = config.cvar_confidence
    tail_scale = 1 / ((1 - confidence) * observation_count)

    objective = np.concatenate(
        [np.zeros(asset_count), np.array([1.0]), np.repeat(tail_scale, observation_count)]
    )
    scenario_constraints = np.hstack(
        [
            -values,
            -np.ones((observation_count, 1)),
            -np.eye(observation_count),
        ]
    )
    upper_matrix = scenario_constraints
    upper_bounds = np.zeros(observation_count)
    if family == "combined":
        crypto = asset_classes.eq("crypto").to_numpy(dtype=float)
        sleeve_row = np.concatenate(
            [crypto, np.zeros(1 + observation_count)]
        ).reshape(1, -1)
        upper_matrix = np.vstack([upper_matrix, sleeve_row])
        upper_bounds = np.append(
            upper_bounds,
            config.combined_crypto_sleeve_cap,
        )

    equality_matrix = np.concatenate(
        [np.ones(asset_count), np.zeros(1 + observation_count)]
    ).reshape(1, -1)
    caps = np.where(
        asset_classes.eq("crypto").to_numpy(),
        config.crypto_asset_cap,
        config.equity_asset_cap,
    )
    bounds = [
        *[(0.0, float(cap)) for cap in caps],
        (None, None),
        *[(0.0, None)] * observation_count,
    ]
    result = linprog(
        objective,
        A_ub=upper_matrix,
        b_ub=upper_bounds,
        A_eq=equality_matrix,
        b_eq=np.array([1.0]),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise ValueError(f"minimum-CVaR optimisation failed: {result.message}")

    weights = result.x[:asset_count]
    losses = -(values @ weights)
    var = float(result.x[asset_count])
    cvar = float(result.fun)
    tail_count = int(np.count_nonzero(losses >= var - 1e-10))
    return CvarSolution(
        weights=pd.Series(weights, index=history.columns, name="target_weight"),
        var=var,
        cvar=cvar,
        tail_scenario_count=tail_count,
        solver_status=int(result.status),
        solver_message=str(result.message),
    )


__all__ = ["CvarSolution", "minimum_cvar"]
