import edge.cli as cli


def test_sports_missing_key_returns_error(monkeypatch, capsys):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    rc = cli.main(["sports"])
    assert rc == 1
    assert "Failed to fetch sports" in capsys.readouterr().err


def test_sports_lists_in_season(monkeypatch, capsys):
    class FakeProvider:
        def __init__(self, *a, **k):
            pass

        def get_sports(self, all_sports=False):
            assert all_sports is False
            return [
                {"key": "baseball_mlb", "group": "Baseball", "title": "MLB", "active": True},
                {"key": "americanfootball_nfl", "group": "American Football",
                 "title": "NFL", "active": True},
            ]

    monkeypatch.setattr(cli, "TheOddsApiProvider", FakeProvider)
    rc = cli.main(["sports"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "2 in-season sport(s)" in out
    assert "baseball_mlb" in out
    assert "americanfootball_nfl" in out


def test_scan_offline_runs(capsys):
    # The default scan uses bundled data and must work with no network/key.
    rc = cli.main(["scan", "--min-ev", "0.05"])
    assert rc == 0
    assert "+EV bet" in capsys.readouterr().out
