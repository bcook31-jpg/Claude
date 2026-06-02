"""Core betting math: odds conversions, de-vigging, EV, and Kelly staking.

All functions are pure and dependency-free so they are easy to test and reuse.

Conventions
-----------
* "american"  : American odds as an int (e.g. -110, +120).
* "decimal"   : Decimal odds as a float >= 1.0 (e.g. 1.91).
* "implied"   : Implied win probability as a float in (0, 1). Raw implied
                probabilities include the bookmaker's margin ("vig"), so a
                two-way market sums to > 1.0 until it is de-vigged.
"""

from __future__ import annotations

import math


def american_to_decimal(american: int) -> float:
    """Convert American odds to decimal odds."""
    if american > 0:
        return 1.0 + american / 100.0
    if american < 0:
        return 1.0 + 100.0 / abs(american)
    raise ValueError("American odds cannot be 0")


def decimal_to_american(decimal: float) -> int:
    """Convert decimal odds to American odds (rounded to the nearest integer)."""
    if decimal <= 1.0:
        raise ValueError("Decimal odds must be > 1.0")
    if decimal >= 2.0:
        return round((decimal - 1.0) * 100.0)
    return round(-100.0 / (decimal - 1.0))


def american_to_implied(american: int) -> float:
    """Raw implied probability (includes vig) from American odds."""
    if american > 0:
        return 100.0 / (american + 100.0)
    if american < 0:
        return abs(american) / (abs(american) + 100.0)
    raise ValueError("American odds cannot be 0")


def decimal_to_implied(decimal: float) -> float:
    """Raw implied probability (includes vig) from decimal odds."""
    if decimal <= 1.0:
        raise ValueError("Decimal odds must be > 1.0")
    return 1.0 / decimal


def devig_proportional(implied: list[float]) -> list[float]:
    """Remove the bookmaker margin by proportional (normalisation) de-vig.

    Each raw implied probability is divided by the market's total ("the
    overround"), so the returned probabilities sum to 1.0. This is the most
    common de-vig method and works for any number of outcomes.
    """
    total = sum(implied)
    if total <= 0:
        raise ValueError("Implied probabilities must sum to a positive number")
    return [p / total for p in implied]


def devig_shin(implied: list[float], max_iter: int = 100, tol: float = 1e-10) -> list[float]:
    """Remove the bookmaker margin using Shin's method.

    Shin models the margin as compensation for informed ("insider") bettors
    rather than spreading it proportionally. This shrinks favourites slightly
    less than proportional de-vig and tends to produce better-calibrated
    probabilities (it counteracts the favourite-longshot bias). The insider
    proportion ``z`` is solved by bisection so the fair probabilities sum to 1.
    """
    q = sum(implied)
    if q <= 0:
        raise ValueError("Implied probabilities must sum to a positive number")

    def probs_for(z: float) -> list[float]:
        denom = 2.0 * (1.0 - z)
        return [
            (math.sqrt(z * z + 4.0 * (1.0 - z) * qi * qi / q) - z) / denom
            for qi in implied
        ]

    # sum(probs) is monotonically decreasing in z; it is > 1 at z=0.
    lo, hi = 0.0, 0.999999
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        if sum(probs_for(mid)) > 1.0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return probs_for((lo + hi) / 2.0)


def devig(implied: list[float], method: str = "proportional") -> list[float]:
    """De-vig dispatcher: ``method`` is "proportional" (default) or "shin"."""
    if method == "proportional":
        return devig_proportional(implied)
    if method == "shin":
        return devig_shin(implied)
    raise ValueError(f"Unknown de-vig method: {method!r}")


def market_overround(implied: list[float]) -> float:
    """The bookmaker margin as a fraction (e.g. 0.045 == a 4.5% hold)."""
    return sum(implied) - 1.0


def expected_value(true_prob: float, decimal: float) -> float:
    """Expected profit per 1 unit staked.

    EV = p * (decimal - 1) - (1 - p) = p * decimal - 1.
    A value of 0.05 means +5% expected return on stake.
    """
    return true_prob * decimal - 1.0


def closing_line_value(your_price: int, closing_price: int) -> float:
    """Closing line value (CLV) as a fraction.

    CLV = your_decimal / closing_decimal - 1. A positive value means you got a
    better price than the market's closing line (you "beat the close"), which
    is the strongest available signal that a bet was made at value.
    """
    return american_to_decimal(your_price) / american_to_decimal(closing_price) - 1.0


def kelly_fraction(true_prob: float, decimal: float) -> float:
    """Full-Kelly stake as a fraction of bankroll.

    f* = (b * p - q) / b, where b = decimal - 1, q = 1 - p.
    Clamped at 0 because a negative Kelly means "do not bet".
    """
    b = decimal - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - true_prob
    f = (b * true_prob - q) / b
    return max(0.0, f)
