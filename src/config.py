"""Central typed configuration for Stockist Funds modelling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

AssetFamily = Literal["equity", "crypto", "combined"]
CovarianceEstimator = Literal["sample_ridge", "ledoit_wolf"]
PortfolioMethod = Literal[
    "equal_weight",
    "minimum_variance",
    "risk_parity",
    "maximum_sharpe",
    "effective_bets",
    "hierarchical_risk_parity",
    "conditional_value_at_risk",
]
RebalanceSchedule = Literal["daily", "weekly", "biweekly", "monthly"]


@dataclass(frozen=True)
class ModelConfig:
    """Approved primary settings plus numerical validation tolerances."""

    equity_window: int = 252
    crypto_window: int = 365
    combined_window: int = 252
    primary_schedule: str = "monthly"
    diagnostic_schedules: tuple[str, ...] = ("daily", "weekly", "biweekly")
    diagnostic_intervals: tuple[int, ...] = (1, 5, 10)
    risk_free_rate_annual: float = 0.0
    equity_asset_cap: float = 0.10
    crypto_asset_cap: float = 0.25
    combined_crypto_sleeve_cap: float = 0.30
    transaction_cost_bps: float = 10.0
    transaction_cost_sensitivities_bps: tuple[float, ...] = (5.0, 25.0)
    fusion_base_method: PortfolioMethod = "minimum_variance"
    fusion_tilt_strength: float = 0.20
    fusion_tilt_strength_sensitivities: tuple[float, ...] = (0.10, 0.40)
    fusion_signal_z_cap: float = 2.0
    black_litterman_risk_aversion: float = 2.5
    black_litterman_tau: float = 0.05
    black_litterman_view_scale_annual: float = 0.02
    black_litterman_view_scale_sensitivities_annual: tuple[float, ...] = (
        0.01,
        0.04,
    )
    black_litterman_confidence_cap: float = 0.95
    cvar_confidence: float = 0.95
    covariance_ridge: float = 1e-8
    solver_tolerance: float = 1e-9
    solver_max_iterations: int = 1_000
    weight_tolerance: float = 1e-7
    random_seed: int = 55_45
    methods: tuple[PortfolioMethod, ...] = (
        "equal_weight",
        "minimum_variance",
        "risk_parity",
        "maximum_sharpe",
        "hierarchical_risk_parity",
    )
    frequency_experiment_methods: tuple[PortfolioMethod, ...] = (
        "risk_parity",
        "maximum_sharpe",
    )
    families: tuple[AssetFamily, ...] = ("equity", "crypto", "combined")

    def __post_init__(self) -> None:
        """Reject settings that cannot define the approved portfolio problem."""
        if min(self.equity_window, self.crypto_window, self.combined_window) < 2:
            raise ValueError("estimation windows must be at least two observations")
        if self.primary_schedule != "monthly":
            raise ValueError("the primary Project B schedule must remain monthly")
        if len(self.diagnostic_schedules) != len(self.diagnostic_intervals):
            raise ValueError("diagnostic schedules and intervals must correspond")
        if len(set(self.diagnostic_schedules)) != len(self.diagnostic_schedules):
            raise ValueError("diagnostic schedule names must be unique")
        if any(interval <= 0 for interval in self.diagnostic_intervals):
            raise ValueError("diagnostic rebalance intervals must be positive")
        if self.risk_free_rate_annual < 0:
            raise ValueError("risk-free rate must be nonnegative")
        for name, value in (
            ("equity_asset_cap", self.equity_asset_cap),
            ("crypto_asset_cap", self.crypto_asset_cap),
            ("combined_crypto_sleeve_cap", self.combined_crypto_sleeve_cap),
        ):
            if not 0 < value <= 1:
                raise ValueError(f"{name} must lie in (0, 1]")
        if self.transaction_cost_bps < 0 or any(
            cost < 0 for cost in self.transaction_cost_sensitivities_bps
        ):
            raise ValueError("transaction costs must be nonnegative")
        if self.fusion_base_method not in self.methods:
            raise ValueError("fusion base method must be one of the primary methods")
        if self.fusion_tilt_strength < 0 or any(
            strength < 0 for strength in self.fusion_tilt_strength_sensitivities
        ):
            raise ValueError("fusion tilt strengths must be nonnegative")
        if self.fusion_signal_z_cap <= 0:
            raise ValueError("fusion signal z-score cap must be positive")
        if self.black_litterman_risk_aversion <= 0:
            raise ValueError("Black-Litterman risk aversion must be positive")
        if self.black_litterman_tau <= 0:
            raise ValueError("Black-Litterman tau must be positive")
        if self.black_litterman_view_scale_annual <= 0 or any(
            scale <= 0
            for scale in self.black_litterman_view_scale_sensitivities_annual
        ):
            raise ValueError("Black-Litterman view scales must be positive")
        if not 0 < self.black_litterman_confidence_cap < 1:
            raise ValueError("Black-Litterman confidence cap must lie in (0, 1)")
        if not 0 < self.cvar_confidence < 1:
            raise ValueError("CVaR confidence must lie in (0, 1)")
        if self.covariance_ridge <= 0:
            raise ValueError("covariance ridge must be positive")
        if self.solver_tolerance <= 0 or self.weight_tolerance <= 0:
            raise ValueError("solver and weight tolerances must be positive")
        if self.solver_max_iterations <= 0:
            raise ValueError("solver iterations must be positive")
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("portfolio methods must be unique")
        if not set(self.frequency_experiment_methods).issubset(self.methods):
            raise ValueError("frequency experiment methods must be primary methods")
        if len(set(self.families)) != len(self.families):
            raise ValueError("asset families must be unique")


DEFAULT_CONFIG: Final = ModelConfig()


__all__ = [
    "DEFAULT_CONFIG",
    "AssetFamily",
    "ModelConfig",
    "PortfolioMethod",
    "RebalanceSchedule",
]
