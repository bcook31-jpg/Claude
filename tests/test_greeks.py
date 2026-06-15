"""Tests for Black-Scholes greeks against known reference values."""

import math

from portfolio_monitor.greeks import black_scholes_greeks, _norm_cdf


def test_norm_cdf_known_points():
    assert math.isclose(_norm_cdf(0.0), 0.5, abs_tol=1e-9)
    assert math.isclose(_norm_cdf(1.96), 0.9750021, abs_tol=1e-5)


def test_atm_call_reference():
    # S=K=100, 1y, iv=20%, r=5%. Standard textbook ATM-ish values.
    g = black_scholes_greeks(option_type="call", spot=100, strike=100,
                             days_to_expiry=365, iv=0.20, risk_free_rate=0.05)
    assert math.isclose(g.delta, 0.6368, abs_tol=1e-3)
    assert math.isclose(g.gamma, 0.01876, abs_tol=1e-4)
    # vega per 1 IV-pt ~= 0.3752 (annual vega 37.52 / 100)
    assert math.isclose(g.vega, 0.3752, abs_tol=1e-3)
    # theta per day is small and negative for a long option
    assert g.theta < 0


def test_put_call_delta_parity():
    kw = dict(spot=100, strike=105, days_to_expiry=180, iv=0.30, risk_free_rate=0.045)
    c = black_scholes_greeks(option_type="call", **kw)
    p = black_scholes_greeks(option_type="put", **kw)
    # call_delta - put_delta == 1 (no dividends)
    assert math.isclose(c.delta - p.delta, 1.0, abs_tol=1e-9)
    # gamma and vega are identical for calls and puts
    assert math.isclose(c.gamma, p.gamma, abs_tol=1e-12)
    assert math.isclose(c.vega, p.vega, abs_tol=1e-12)


def test_expired_option_returns_boundary_delta():
    itm = black_scholes_greeks(option_type="call", spot=120, strike=100,
                               days_to_expiry=0, iv=0.3)
    assert itm.delta == 1.0 and itm.gamma == 0.0 and itm.vega == 0.0
    otm = black_scholes_greeks(option_type="put", spot=120, strike=100,
                               days_to_expiry=0, iv=0.3)
    assert otm.delta == 0.0


def test_zero_iv_is_graceful():
    g = black_scholes_greeks(option_type="call", spot=100, strike=100,
                             days_to_expiry=30, iv=0.0)
    assert g.gamma == 0.0 and g.vega == 0.0
