import pytest
from mat3ra.utils.math import mod, smaller_or_equal


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.25, 0.25),
        (1.25, 0.25),
        (-0.25, 0.75),
        (0.999998, 0.0),
        (-1e-06, 0.0),
        (0.999, 0.0),  # |0.999 - 1| is 1e-18 past the tolerance in floats; mathjs still counts it as equal
        (-0.001, 0.0),
        (0.0011, 0.0011),
        (1.0, 0.0),
        (-1.0, 0.0),
    ],
)
def test_mod(value, expected):
    assert mod(value) == expected


@pytest.mark.parametrize(
    "value, other, expected",
    [
        (0.001 + 5e-16, 0.001, True),
        (0.001 + 2e-15, 0.001, False),
        (1e-06 + 2e-16, 1e-06, True),
        (1e-06 + 3e-16, 1e-06, False),
    ],
)
def test_smaller_or_equal(value, other, expected):
    assert smaller_or_equal(value, other) == expected
