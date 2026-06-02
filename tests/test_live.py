"""Live smoke test against The Odds API.

Skipped automatically unless ODDS_API_KEY is set, so the default test run stays
offline and deterministic. Run it explicitly with a real key to confirm the
live provider and engine work end-to-end against real odds:

    ODDS_API_KEY=your_key pytest tests/test_live.py -v
"""

import os

import pytest

from edge.engine import find_value_bets
from edge.models import Event
from edge.providers import TheOddsApiProvider

pytestmark = pytest.mark.skipif(
    not os.environ.get("ODDS_API_KEY"),
    reason="set ODDS_API_KEY to run the live API smoke test",
)


def test_live_provider_returns_events_and_engine_runs():
    provider = TheOddsApiProvider()
    events = provider.get_odds(["americanfootball_nfl"], ["h2h"])

    assert isinstance(events, list)
    # Off-season can legitimately return zero events; only validate shape if any.
    for e in events:
        assert isinstance(e, Event)
        assert e.home_team and e.away_team
        for bm in e.bookmakers:
            for market in bm.markets:
                assert market.outcomes

    # The engine must run on real data without raising.
    bets = find_value_bets(events)
    assert all(b.ev >= 0 for b in bets)
