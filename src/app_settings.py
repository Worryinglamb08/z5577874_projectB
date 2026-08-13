"""User-facing product settings for the deployed Stockist Funds app."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class AppSettings:
    """Settings controlled by Stockist rather than by the allocation user."""

    annual_product_fee_rate: float = 0.0012

    def __post_init__(self) -> None:
        """Reject fee settings outside a meaningful annual-rate range."""
        if not 0 <= self.annual_product_fee_rate < 1:
            raise ValueError("annual product fee rate must lie in [0, 1)")


DEFAULT_APP_SETTINGS: Final = AppSettings()


__all__ = ["DEFAULT_APP_SETTINGS", "AppSettings"]
