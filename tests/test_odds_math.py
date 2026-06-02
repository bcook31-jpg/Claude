import math

import pytest

from edge import odds_math as om


def test_american_to_decimal_roundtrip():
    for american in (-250, -110, -100, 100, 120, 350):
        if american == -100:
            continue  # -100 == +100 boundary, skip the ambiguous case
        dec = om.american_to_decimal(american)
        assert om.decimal_to_american(dec) == american


def test_american_to_decimal_known_values():
    assert om.american_to_decimal(100) == pytest.approx(2.0)
    assert om.american_to_decimal(-110) == pytest.approx(1.9090909, abs=1e-6)
    assert om.american_to_decimal(150) == pytest.approx(2.5)


def test_implied_probabilities():
    assert om.american_to_implied(-110) == pytest.approx(0.5238, abs=1e-4)
    assert om.american_to_implied(100) == pytest.approx(0.5)
    assert om.american_to_implied(150) == pytest.approx(0.4)


def test_devig_sums_to_one():
    implied = [om.american_to_implied(-110), om.american_to_implied(-110)]
    fair = om.devig_proportional(implied)
    assert math.isclose(sum(fair), 1.0)
    assert fair[0] == pytest.approx(0.5)


def test_overround_positive_for_real_market():
    implied = [om.american_to_implied(-130), om.american_to_implied(110)]
    assert om.market_overround(implied) > 0


def test_expected_value_zero_at_fair_odds():
    # Fair coin at +100 (decimal 2.0) has zero EV.
    assert om.expected_value(0.5, 2.0) == pytest.approx(0.0)


def test_expected_value_positive_when_underpriced():
    # True 50% chance offered at +120 (decimal 2.2) is +EV.
    assert om.expected_value(0.5, 2.2) == pytest.approx(0.1)


def test_kelly_fraction():
    # p=0.55, decimal 2.0 (b=1): f = (1*0.55 - 0.45)/1 = 0.10
    assert om.kelly_fraction(0.55, 2.0) == pytest.approx(0.10)


def test_kelly_zero_when_no_edge():
    assert om.kelly_fraction(0.5, 1.9) == 0.0


def test_closing_line_value():
    # Got +135 (2.35), closed at +120 (2.20) -> beat the close.
    clv = om.closing_line_value(135, 120)
    assert clv == pytest.approx(2.35 / 2.20 - 1.0, abs=1e-9)
    assert clv > 0


def test_closing_line_value_negative_when_worse_than_close():
    # Got +110, closed at +135 -> you got a worse price than the close.
    assert om.closing_line_value(110, 135) < 0


def test_closing_line_value_zero_at_same_price():
    assert om.closing_line_value(-110, -110) == pytest.approx(0.0)


def test_zero_odds_rejected():
    with pytest.raises(ValueError):
        om.american_to_decimal(0)
