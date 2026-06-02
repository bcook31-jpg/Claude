"""Tests for the historical-odds -> backtest-dataset pipeline (offline)."""

import json

import edge.cli as cli
from edge.backtest import run_backtest
from edge.dataset import build_settled_events, scores_to_results
from edge.engine import find_value_bets


def _odds_event(event_id, home, away):
    """Minimal The Odds API style event with a mispriced underdog at Caesars."""
    return {
        "id": event_id, "sport_key": "americanfootball_nfl", "sport_title": "NFL",
        "commence_time": "2025-09-14T20:25:00Z", "home_team": home, "away_team": away,
        "bookmakers": [
            {"key": "draftkings", "title": "DraftKings", "markets": [
                {"key": "h2h", "outcomes": [{"name": home, "price": -130},
                                            {"name": away, "price": 110}]}]},
            {"key": "pinnacle", "title": "Pinnacle", "markets": [
                {"key": "h2h", "outcomes": [{"name": home, "price": -132},
                                            {"name": away, "price": 118}]}]},
            {"key": "caesars", "title": "Caesars", "markets": [
                {"key": "h2h", "outcomes": [{"name": home, "price": -150},
                                            {"name": away, "price": 135}]}]},
        ],
    }


def _score(event_id, home, away, hs, as_, completed=True):
    return {
        "id": event_id, "sport_key": "americanfootball_nfl", "completed": completed,
        "home_team": home, "away_team": away,
        "scores": None if not completed else [
            {"name": home, "score": str(hs)}, {"name": away, "score": str(as_)}],
    }


def test_scores_to_results_keeps_completed_only():
    scores = [
        _score("a", "H", "A", 24, 27),
        _score("b", "H", "A", 0, 0, completed=False),
    ]
    results = scores_to_results(scores)
    assert results == {"a": {"home_score": 24, "away_score": 27}}


def test_build_joins_by_id_and_attaches_closing():
    opening = [_odds_event("g1", "Chiefs", "Bills"),
               _odds_event("g2", "Eagles", "Cowboys")]
    closing = [_odds_event("g1", "Chiefs", "Bills")]  # only g1 has a closing snapshot
    scores = [_score("g1", "Chiefs", "Bills", 24, 27)]  # only g1 completed

    settled = build_settled_events(opening, scores, closing)
    assert len(settled) == 1                       # g2 dropped (no result)
    assert settled[0]["event"]["id"] == "g1"
    assert settled[0]["result"] == {"home_score": 24, "away_score": 27}
    assert "closing" in settled[0]                 # closing attached for g1


def test_build_without_closing_omits_clv_section():
    opening = [_odds_event("g1", "Chiefs", "Bills")]
    scores = [_score("g1", "Chiefs", "Bills", 30, 20)]
    settled = build_settled_events(opening, scores)
    assert "closing" not in settled[0]


def test_full_pipeline_build_then_backtest():
    """Built dataset must be directly consumable by run_backtest."""
    opening = [_odds_event("g1", "Chiefs", "Bills")]
    scores = [_score("g1", "Chiefs", "Bills", 24, 27)]  # Bills (underdog) win
    settled = build_settled_events(opening, scores)

    summary = run_backtest(settled, lambda evs: find_value_bets(evs, min_ev=0.02))
    assert summary.bets >= 1
    # The +EV underdog bet (Bills +135) won, so profit is positive.
    assert summary.profit > 0


def test_cli_build_dataset_round_trips(monkeypatch, tmp_path, capsys):
    opening_snapshot = {"timestamp": "t", "previous_timestamp": None,
                        "next_timestamp": None,
                        "data": [_odds_event("g1", "Chiefs", "Bills")]}

    class FakeProvider:
        def __init__(self, *a, **k):
            self.requests_remaining = 100
            self.requests_used = 5
            self.last_cost = 10

        def get_historical_odds(self, sport_key, date, regions=None, markets=None):
            return opening_snapshot

        def get_scores(self, sport_key, days_from=3):
            return [_score("g1", "Chiefs", "Bills", 24, 27)]

    monkeypatch.setattr(cli, "TheOddsApiProvider", FakeProvider)
    out = tmp_path / "ds.json"
    rc = cli.main(["build-dataset", "--sport", "nfl",
                   "--open-date", "2025-09-14T12:00:00Z", "--out", str(out)])
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert data[0]["event"]["id"] == "g1"
    assert data[0]["result"] == {"home_score": 24, "away_score": 27}
    assert "Wrote 1 settled event" in capsys.readouterr().out
