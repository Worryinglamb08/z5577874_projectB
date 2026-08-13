"""Tests for Stockist-controlled app settings."""

from __future__ import annotations

import pytest
from src.app_settings import DEFAULT_APP_SETTINGS, AppSettings


def test_default_annual_product_fee_is_twelve_basis_points() -> None:
    assert DEFAULT_APP_SETTINGS.annual_product_fee_rate == pytest.approx(0.0012)


@pytest.mark.parametrize("fee_rate", [-0.001, 1.0])
def test_invalid_annual_product_fee_is_rejected(fee_rate: float) -> None:
    with pytest.raises(ValueError, match="annual product fee rate"):
        AppSettings(annual_product_fee_rate=fee_rate)
