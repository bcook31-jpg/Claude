import pytest

from edge.engine import find_value_bets
from edge.models import (
    Bookmaker,
    Event,
    MarketOffer,
    Outcome,
    event_from_dict,
)
from edge.providers import MockProvider


def _two_book_event(price_b_book2: int) -> Event:
    """Event where book2 prices the underdog at ``price_b_book2``."""
    def book(title, a, b):
        return Bookmaker(
            key=title.lower(),
            title=title,
            markets=[MarketOffer("h2h", [
                Outcome("Team A", a), Outcome("Team B", b),
            ])],
        )

    return Event(
        id="t", sport_key="x", sport_title="Test",
        commence_time="2026-01-01T00:00:00Z",
        home_team="Team A", away_team="Team B",
        bookmakers=[
            book("Book1", -120, 100),
            book("Book2", -120, price_b_book2),
        ],
    )


def test_finds_value_when_book_is_off():
    # Book2 offers Team B at +150 while the rest of the market implies ~+100.
    event = _two_book_event(150)
    bets = find_value_bets([event])
    assert bets, "expected a +EV bet"
    top = bets[0]
    assert top.selection == "Team B"
    assert top.book == "Book2"
    assert top.ev > 0
    assert 0.0 < top.fair_prob < 1.0


def test_no_value_when_books_agree():
    event = _two_book_event(100)  # both books identical
    bets = find_value_bets([event], min_ev=0.001)
    assert bets == []


def test_min_ev_filter():
    event = _two_book_event(150)
    everything = find_value_bets([event], min_ev=0.0)
    filtered = find_value_bets([event], min_ev=0.20)
    assert len(filtered) <= len(everything)
    assert all(b.ev >= 0.20 for b in filtered)


def test_sharp_book_mode_excludes_reference():
    event = _two_book_event(150)
    bets = find_value_bets([event], sharp_book="Book1")
    # Sharp book itself is never reported as a bet.
    assert all(b.book != "Book1" for b in bets)


def test_single_book_market_yields_nothing():
    event = Event(
        id="t", sport_key="x", sport_title="Test",
        commence_time="2026-01-01T00:00:00Z",
        home_team="A", away_team="B",
        bookmakers=[Bookmaker("only", "Only", [
            MarketOffer("h2h", [Outcome("A", -110), Outcome("B", -110)])
        ])],
    )
    assert find_value_bets([event]) == []


def test_sample_data_produces_value_bets():
    events = MockProvider().get_odds()
    bets = find_value_bets(events)
    assert len(bets) >= 4  # at least one per sport
    # Every reported bet must be genuinely +EV.
    assert all(b.ev > 0 for b in bets)


def test_event_from_dict_roundtrips_points():
    data = {
        "id": "e", "sport_key": "x", "sport_title": "X",
        "commence_time": "2026-01-01T00:00:00Z",
        "home_team": "A", "away_team": "B",
        "bookmakers": [{
            "key": "bk", "title": "Bk",
            "markets": [{"key": "spreads", "outcomes": [
                {"name": "A", "price": -110, "point": -3.5},
                {"name": "B", "price": -110, "point": 3.5},
            ]}],
        }],
    }
    event = event_from_dict(data)
    spread = event.bookmakers[0].market("spreads")
    assert spread.outcomes[0].point == -3.5
    assert spread.outcomes[1].selection_id == ("B", 3.5)
