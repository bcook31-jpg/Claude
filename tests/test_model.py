import math
from pathlib import Path

import pytest

from edge.engine import find_model_value_bets
from edge.model import EloModel, load_results
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
