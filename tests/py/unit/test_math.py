import pytest
from mat3ra.utils.math import mod


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.25, 0.25),
        (1.25, 0.25),
        (-0.25, 0.75),
        (0.999998, 0.0),
        (-1e-06, 0.0),
        (0.999, 0.0),
        (-0.001, 0.0),
        (0.0011, 0.0011),
        (1.0, 0.0),
        (-1.0, 0.0),
    ],
)
def test_mod(value, expected):
    assert mod(value) == pytest.approx(expected)
