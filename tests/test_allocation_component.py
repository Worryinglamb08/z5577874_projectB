"""Validation tests for the single-bar allocation component."""

from __future__ import annotations

import pytest
from src.allocation_component import _valid_weights, allocation_slider


@pytest.mark.parametrize(
    ("values", "count", "expected"),
    [
        ([34, 33, 33], 3, [34, 33, 33]),
        ([0, 100], 2, [0, 100]),
        ([25, 25, 25, 25], 4, [25, 25, 25, 25]),
        ([34, 33, 32], 3, None),
        ([-1, 51, 50], 3, None),
        ([50, 50], 3, None),
        ("50,50", 2, None),
    ],
)
def test_valid_weights_requires_bounded_whole_percentages_summing_to_100(
    values: object, count: int, expected: list[int] | None
) -> None:
    assert _valid_weights(values, count) == expected


def test_allocation_slider_rejects_invalid_default_contract() -> None:
    with pytest.raises(ValueError, match="two to four weights summing to 100"):
        allocation_slider(["Fund A", "Fund B"], [60, 30], key="invalid")
