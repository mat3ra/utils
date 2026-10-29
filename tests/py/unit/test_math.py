import pytest
from mat3ra.utils.math import mod


@pytest.mark.parametrize(
    "value, expected",
    [
        # Within the tolerance of 0 and 1
        (-1e-06, 0.0),
        (0.999998, 0.0),
        # At the tolerance: |0.999 - 1| is 1e-18 past it in floats; mathjs smallerEq still counts it as equal
        (0.001, 0.0),
        (-0.001, 0.0),
        (0.999, 0.0),
        # Just past the tolerance
        (0.0011, 0.0011),
        (-0.0011, 0.9989),
        (0.998, 0.998),
        # Negatives and values above 1
        (-0.25, 0.75),
        (-1.0, 0.0),
        (1.0, 0.0),
        (1.25, 0.25),
        (2.0005, 0.0),
    ],
)
def test_mod(value, expected):
    assert mod(value) == expected
