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


def market_overround(implied: list[float]) -> float:
    """The bookmaker margin as a fraction (e.g. 0.045 == a 4.5% hold)."""
    return sum(implied) - 1.0


def expected_value(true_prob: float, decimal: float) -> float:
    """Expected profit per 1 unit staked.

    EV = p * (decimal - 1) - (1 - p) = p * decimal - 1.
    A value of 0.05 means +5% expected return on stake.
    """
    return true_prob * decimal - 1.0


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
