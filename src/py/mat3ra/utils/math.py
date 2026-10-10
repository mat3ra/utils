import math
import sys

# mathjs smallerEq counts values within config.epsilon (relative) or DBL_EPSILON (absolute) as equal
MATHJS_EPSILON = 1e-12


def smaller_or_equal(value: float, other: float) -> bool:
    """
    Mirrors mathjs smallerEq: `value` is smaller than `other` or nearly equal to it.
    """
    return value <= other or math.isclose(value, other, rel_tol=MATHJS_EPSILON, abs_tol=sys.float_info.epsilon)


def mod(value: float, tolerance: float = 0.001) -> float:
    """
    Mirrors JS Utils.math.mod: the fractional part of `value` in [0, 1), set to 0 within `tolerance` of 0 or 1.
    """
    remainder = math.fmod(value, 1)
    wrapped = remainder if value >= 0 else 1 + remainder
    if smaller_or_equal(abs(wrapped - 1), tolerance) or smaller_or_equal(abs(wrapped), tolerance):
        return 0.0
    return wrapped
