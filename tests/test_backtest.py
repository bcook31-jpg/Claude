import json
from pathlib import Path

import pytest

from edge.backtest import grade, run_backtest
from edge.engine import find_value_bets

BUNDLED = Path(__file__).resolve().parents[1] / "edge" / "data" / "backtest_events.json"


# -- grader ---------------------------------------------------------------
def test_grade_moneyline():
    assert grade("h2h", "Home", None, "Home", "Away", 27, 24) == "win"
    assert grade("h2h", "Away", None, "Home", "Away", 27, 24) == "loss"
    assert grade("h2h", "Home", None, "Home", "Away", 20, 20) == "push"


def test_grade_spread():
    # Home favoured by 2.5, wins by 3 -> covers.
    assert grade("spreads", "Home", -2.5, "Home", "Away", 27, 24) == "win"
    # Home -3.5, wins by exactly 3 -> does not cover.
    assert grade("spreads", "Home", -3.5, "Home", "Away", 27, 24) == "loss"
    # Away +2.5, loses by 3 -> does not cover.
    assert grade("spreads", "Away", 2.5, "Home", "Away", 27, 24) == "loss"
    # Push on the exact number.
    assert grade("spreads", "Home", -3.0, "Home", "Away", 27, 24) == "push"


def test_grade_total():
    assert grade("totals", "Over", 47.5, "H", "A", 27, 24) == "win"   # 51 > 47.5
    assert grade("totals", "Under", 47.5, "H", "A", 27, 24) == "loss"
    assert grade("totals", "Over", 51.0, "H", "A", 27, 24) == "push"  # exact
    assert grade("totals", "Under", 60.0, "H", "A", 27, 24) == "win"


def test_grade_unknown_returns_none():
    assert grade("h2h", "Nobody", None, "Home", "Away", 1, 0) == "loss"
    assert grade("spreads", "Nobody", -1.5, "Home", "Away", 1, 0) is None


# -- backtest runner ------------------------------------------------------
@pytest.fixture
def settled():
    return json.loads(BUNDLED.read_text())


def _market_strategy(events):
    return find_value_bets(events, min_ev=0.0)


def test_backtest_runs_and_grades(settled):
    s = run_backtest(settled, _market_strategy, stake="flat", unit=1.0)
    assert s.bets > 0
    assert s.bets == s.wins + s.losses + s.pushes
    assert s.staked == pytest.approx(s.bets * 1.0)
    # Profit must equal stake-weighted settlement.
    assert isinstance(s.roi, float)


def test_backtest_reports_clv(settled):
    s = run_backtest(settled, _market_strategy)
    # The bundled data includes closing lines, so CLV should be measured.
    assert s.clv_count > 0
    assert -1.0 < s.avg_clv < 1.0
    assert 0.0 <= s.beat_close_rate <= 1.0


def test_kelly_tracks_bankroll(settled):
    s = run_backtest(settled, _market_strategy, stake="kelly", bankroll=1000.0)
    assert s.start_bankroll == 1000.0
    assert s.end_bankroll == pytest.approx(1000.0 + s.profit)


def test_empty_strategy_places_no_bets(settled):
    s = run_backtest(settled, lambda evs: [], stake="flat")
    assert s.bets == 0
    assert s.profit == 0.0
    assert s.roi == 0.0
