"""Black-Scholes option greeks, computed locally (no external library).

Conventions (per share of underlying, i.e. per 1.0 of contract multiplier):
  delta  - dValue/dSpot, dimensionless.
  gamma  - dDelta/dSpot, per $1 move in spot.
  theta  - time decay per CALENDAR DAY (annualised theta / 365).
  vega   - sensitivity to a 1 percentage-point change in IV (raw vega / 100).

To get position-level greeks, multiply by contracts * 100 (one option
contract controls 100 shares). See valuation.py.

Time to expiry uses actual calendar days: T = days_to_expiry / 365.
The risk-free rate is an annual continuously-compounded rate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SQRT_2 = math.sqrt(2.0)
SQRT_2PI = math.sqrt(2.0 * math.pi)


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1.0 + math.erf(x / SQRT_2))


def _norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / SQRT_2PI


@dataclass
class Greeks:
    delta: float
    gamma: float
    theta: float  # per calendar day
    vega: float   # per 1 IV percentage-point

    def as_dict(self) -> dict:
        return {"delta": self.delta, "gamma": self.gamma,
                "theta": self.theta, "vega": self.vega}


def black_scholes_greeks(
    *,
    option_type: str,
    spot: float,
    strike: float,
    days_to_expiry: float,
    iv: float,
    risk_free_rate: float = 0.045,
) -> Greeks:
    """Compute (delta, gamma, theta, vega) for a single option.

    Args:
        option_type: "call" or "put".
        spot: current underlying price.
        strike: option strike.
        days_to_expiry: actual calendar days until expiry (may be 0).
        iv: implied volatility as a decimal (e.g. 0.35 for 35%).
        risk_free_rate: annual continuously-compounded risk-free rate.

    Edge cases (expired or degenerate inputs) return delta at intrinsic
    boundary and zero for the other greeks, rather than raising.
    """
    opt = option_type.lower()
    if opt not in ("call", "put"):
        raise ValueError(f"option_type must be 'call' or 'put', got {option_type!r}")

    T = days_to_expiry / 365.0

    # Degenerate cases: no time left, no vol, or non-positive prices.
    if T <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
        if opt == "call":
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0
        return Greeks(delta=delta, gamma=0.0, theta=0.0, vega=0.0)

    sigma = iv
    sqrt_T = math.sqrt(T)
    d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * sigma * sigma) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T

    pdf_d1 = _norm_pdf(d1)
    discount = math.exp(-risk_free_rate * T)

    gamma = pdf_d1 / (spot * sigma * sqrt_T)
    vega_annual = spot * pdf_d1 * sqrt_T  # per 1.0 change in vol

    if opt == "call":
        delta = _norm_cdf(d1)
        theta_annual = (
            -(spot * pdf_d1 * sigma) / (2.0 * sqrt_T)
            - risk_free_rate * strike * discount * _norm_cdf(d2)
        )
    else:
        delta = _norm_cdf(d1) - 1.0
        theta_annual = (
            -(spot * pdf_d1 * sigma) / (2.0 * sqrt_T)
            + risk_free_rate * strike * discount * _norm_cdf(-d2)
        )

    return Greeks(
        delta=delta,
        gamma=gamma,
        theta=theta_annual / 365.0,  # per calendar day
        vega=vega_annual / 100.0,    # per 1 IV percentage-point
    )
