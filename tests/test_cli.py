import edge.cli as cli


def test_sports_missing_key_returns_error(monkeypatch, capsys):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    rc = cli.main(["sports"])
    assert rc == 1
    assert "Failed to fetch sports" in capsys.readouterr().err


class _FakeProvider:
    def __init__(self, *a, **k):
        pass

    def get_sports(self, all_sports=False):
        return [
            {"key": "baseball_mlb", "group": "Baseball", "title": "MLB", "active": True},
            {"key": "americanfootball_nfl", "group": "American Football",
             "title": "NFL", "active": True},
        ]

    def get_events(self, sport_key):
        return {"baseball_mlb": [{}, {}, {}], "americanfootball_nfl": []}[sport_key]


def test_sports_lists_in_season(monkeypatch, capsys):
    monkeypatch.setattr(cli, "TheOddsApiProvider", _FakeProvider)
    rc = cli.main(["sports"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "2 in-season sport(s)" in out
    assert "baseball_mlb" in out
    assert "americanfootball_nfl" in out
    assert "Events" not in out  # no counts column unless requested


def test_sports_with_event_counts(monkeypatch, capsys):
    monkeypatch.setattr(cli, "TheOddsApiProvider", _FakeProvider)
    rc = cli.main(["sports", "--counts"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Events" in out
    # MLB has 3 upcoming events in the fake data.
    mlb_line = next(line for line in out.splitlines() if "baseball_mlb" in line)
    assert mlb_line.strip().endswith("3")


def test_scan_offline_runs(capsys):
    # The default scan uses bundled data and must work with no network/key.
    rc = cli.main(["scan", "--min-ev", "0.05"])
    assert rc == 0
    assert "+EV bet" in capsys.readouterr().out


def test_train_live_uses_scores(monkeypatch, tmp_path, capsys):
    payload = [
        {"sport_key": "americanfootball_nfl", "completed": True,
         "commence_time": "2025-09-14T20:25:00Z",
         "home_team": "Chiefs", "away_team": "Bills",
         "scores": [{"name": "Chiefs", "score": "24"}, {"name": "Bills", "score": "27"}]},
    ]

    class FakeProvider:
        def __init__(self, *a, **k):
            pass

        def get_scores(self, sport_key, days_from=3):
            return payload if sport_key == "americanfootball_nfl" else []

    monkeypatch.setattr(cli, "TheOddsApiProvider", FakeProvider)
    out = tmp_path / "elo.json"
    rc = cli.main(["train", "--model", "elo", "--live", "--sport", "nfl", "--out", str(out)])
    assert rc == 0
    assert out.exists()
    assert "Trained Elo on 1 games" in capsys.readouterr().out


def test_train_live_handles_no_games(monkeypatch, capsys):
    class FakeProvider:
        def __init__(self, *a, **k):
            pass

        def get_scores(self, sport_key, days_from=3):
            return []

    monkeypatch.setattr(cli, "TheOddsApiProvider", FakeProvider)
    rc = cli.main(["train", "--live", "--sport", "nfl"])
    assert rc == 1
    assert "No completed games" in capsys.readouterr().err
