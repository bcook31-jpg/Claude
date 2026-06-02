import math
from pathlib import Path

import pytest

from edge.engine import find_model_value_bets
from edge.model import EloModel, TeamModel, load_results
from edge.models import Bookmaker, Event, MarketOffer, Outcome
from edge.providers import MockProvider

BUNDLED_RESULTS = Path(__file__).resolve().parents[1] / "edge" / "data" / "historical_results.csv"


def test_equal_ratings_no_home_advantage_is_coin_flip():
    m = EloModel(home_advantage=0.0)
    assert m.win_probability("A", "B") == pytest.approx(0.5)


def test_home_advantage_raises_home_probability():
    m = EloModel(home_advantage=65.0)
    assert m.win_probability("A", "B") > 0.5


def test_update_moves_and_conserves_ratings():
    m = EloModel(home_advantage=0.0)
    before = 2 * m.base_rating
    m.update("A", "B", home_score=3, away_score=1)  # A wins at home
    assert m.rating("A") > m.base_rating
    assert m.rating("B") < m.base_rating
    # Symmetric update conserves total rating.
    assert math.isclose(m.rating("A") + m.rating("B"), before)


def test_predict_sums_to_one():
    m = EloModel()
    probs = m.predict("A", "B")
    assert math.isclose(sum(probs.values()), 1.0)
    assert set(probs) == {"A", "B"}


def test_training_differentiates_teams():
    games = load_results(BUNDLED_RESULTS)
    m = EloModel().train(games)
    # Dominant teams in the bundled data outrank their rivals.
    assert m.rating("Los Angeles Lakers") > m.rating("Boston Celtics")
    assert m.rating("New York Yankees") > m.rating("Boston Red Sox")
    assert m.rating("Colorado Avalanche") > m.rating("Edmonton Oilers")
    # Miami Dolphins lost every game -> clearly the weakest NFL team.
    assert m.rating("Kansas City Chiefs") > m.rating("Miami Dolphins")
    assert m.rating("Buffalo Bills") > m.rating("Miami Dolphins")


def test_save_load_roundtrip(tmp_path):
    m = EloModel().train(load_results(BUNDLED_RESULTS))
    path = tmp_path / "elo.json"
    m.save(path)
    loaded = EloModel.load(path)
    assert loaded.ratings == m.ratings
    assert loaded.k == m.k
    assert loaded.home_advantage == m.home_advantage


def _h2h_event(home_price: int, away_price: int) -> Event:
    return Event(
        id="t", sport_key="x", sport_title="Test",
        commence_time="2026-01-01T00:00:00Z",
        home_team="A", away_team="B",
        bookmakers=[Bookmaker("bk", "Bk", [
            MarketOffer("h2h", [
                Outcome("A", home_price), Outcome("B", away_price),
            ])
        ])],
    )


def test_model_finds_value_when_market_disagrees():
    # Model thinks A is a strong favourite; the book prices A as an underdog.
    m = EloModel(home_advantage=0.0)
    m.ratings = {"A": 1700.0, "B": 1500.0}  # A ~76% to win
    event = _h2h_event(home_price=150, away_price=-170)  # A at +150 (underpriced)
    bets = find_model_value_bets([event], m)
    assert bets
    assert bets[0].selection == "A"
    assert bets[0].ev > 0


def test_model_only_evaluates_moneyline():
    m = EloModel().train(load_results(BUNDLED_RESULTS))
    events = MockProvider().get_odds()
    bets = find_model_value_bets(events, m)
    assert bets  # produces some moneyline edges on the sample data
    assert all(b.market == "h2h" for b in bets)
    assert all(b.ev > 0 for b in bets)


# -- TeamModel (all-markets Gaussian model) -------------------------------
@pytest.fixture
def team_model():
    return TeamModel().train(load_results(BUNDLED_RESULTS))


def _nhl_event() -> Event:
    return Event(
        id="e", sport_key="icehockey_nhl", sport_title="NHL",
        commence_time="t", home_team="Colorado Avalanche",
        away_team="Edmonton Oilers", bookmakers=[],
    )


def test_team_model_probabilities_are_coherent(team_model):
    ev = _nhl_event()
    over = team_model.outcome_probability(ev, "totals", Outcome("Over", -110, 6.5))
    under = team_model.outcome_probability(ev, "totals", Outcome("Under", -110, 6.5))
    assert math.isclose(over + under, 1.0, abs_tol=1e-9)

    home = team_model.outcome_probability(ev, "spreads", Outcome("Colorado Avalanche", -110, -1.5))
    away = team_model.outcome_probability(ev, "spreads", Outcome("Edmonton Oilers", -110, 1.5))
    assert math.isclose(home + away, 1.0, abs_tol=1e-9)

    hw = team_model.outcome_probability(ev, "h2h", Outcome("Colorado Avalanche", -110))
    aw = team_model.outcome_probability(ev, "h2h", Outcome("Edmonton Oilers", 110))
    assert math.isclose(hw + aw, 1.0, abs_tol=1e-9)
    for p in (over, under, home, away, hw, aw):
        assert 0.0 < p < 1.0


def test_team_model_prices_all_markets(team_model):
    events = MockProvider().get_odds()
    bets = find_model_value_bets(events, team_model)
    markets = {b.market for b in bets}
    assert {"h2h", "spreads", "totals"} <= markets
    assert all(b.ev > 0 for b in bets)


def test_team_model_unknown_sport_or_team_returns_none(team_model):
    unknown_sport = Event(
        id="e", sport_key="cricket", sport_title="?", commence_time="t",
        home_team="A", away_team="B", bookmakers=[],
    )
    assert team_model.outcome_probability(unknown_sport, "h2h", Outcome("A", -110)) is None

    unknown_team = Event(
        id="e", sport_key="icehockey_nhl", sport_title="NHL", commence_time="t",
        home_team="Nonexistent FC", away_team="Edmonton Oilers", bookmakers=[],
    )
    assert team_model.outcome_probability(unknown_team, "h2h", Outcome("Edmonton Oilers", 110)) is None


def test_team_model_shrinkage_pulls_toward_mean():
    # With heavy shrinkage, a small sample is pulled toward the league average,
    # so an extreme single-game result barely moves the rating.
    games = [
        {"sport_key": "x", "home_team": "A", "away_team": "B",
         "home_score": "10", "away_score": "0"},
    ]
    weak = TeamModel(shrink=0.0).train(games)
    strong = TeamModel(shrink=50.0).train(games)
    ev = Event("e", "x", "X", "t", "A", "B", [])
    p_weak = weak.outcome_probability(ev, "h2h", Outcome("A", -110))
    p_strong = strong.outcome_probability(ev, "h2h", Outcome("A", -110))
    # Heavily shrunk model is far less confident A is better.
    assert p_strong < p_weak


def test_team_model_save_load_roundtrip(team_model, tmp_path):
    path = tmp_path / "team.json"
    team_model.save(path)
    loaded = TeamModel.load(path)
    ev = _nhl_event()
    out = Outcome("Over", -110, 6.5)
    assert loaded.outcome_probability(ev, "totals", out) == pytest.approx(
        team_model.outcome_probability(ev, "totals", out)
    )
