import pytest

from edge.model import load_results, results_from_scores


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def test_loads_canonical_headers(tmp_path):
    path = _write(tmp_path, "r.csv",
                  "sport_key,date,home_team,away_team,home_score,away_score\n"
                  "nfl,2025-01-01,A,B,21,17\n")
    rows = load_results(path)
    assert rows == [{
        "sport_key": "nfl", "date": "2025-01-01",
        "home_team": "A", "away_team": "B",
        "home_score": "21", "away_score": "17",
    }]


def test_auto_detects_aliases(tmp_path):
    # football-data.co.uk style: HomeTeam/AwayTeam/FTHG/FTAG, no sport_key.
    path = _write(tmp_path, "r.csv",
                  "Date,HomeTeam,AwayTeam,FTHG,FTAG\n"
                  "2025-01-01,Arsenal,Chelsea,2,1\n")
    rows = load_results(path, default_sport="soccer_epl")
    assert rows[0]["home_team"] == "Arsenal"
    assert rows[0]["away_team"] == "Chelsea"
    assert rows[0]["home_score"] == "2"
    assert rows[0]["sport_key"] == "soccer_epl"


def test_explicit_mapping_overrides(tmp_path):
    path = _write(tmp_path, "r.csv",
                  "h,a,hs,as\nHomeClub,AwayClub,3,0\n")
    rows = load_results(path, mapping={
        "home_team": "h", "away_team": "a",
        "home_score": "hs", "away_score": "as",
    }, default_sport="x")
    assert rows[0]["home_team"] == "HomeClub"
    assert rows[0]["home_score"] == "3"


def test_skips_bad_rows(tmp_path):
    path = _write(tmp_path, "r.csv",
                  "home_team,away_team,home_score,away_score\n"
                  "A,B,21,17\n"
                  "C,D,,\n"            # missing scores
                  "E,F,x,y\n"          # non-integer scores
                  "G,H,3,2\n")
    rows = load_results(path, default_sport="x")
    assert [r["home_team"] for r in rows] == ["A", "G"]


def test_missing_required_column_raises(tmp_path):
    path = _write(tmp_path, "r.csv", "home_team,home_score\nA,21\n")
    with pytest.raises(ValueError):
        load_results(path)


# -- results_from_scores (The Odds API /scores payload) -------------------
def test_results_from_scores_keeps_completed_games():
    payload = [
        {
            "sport_key": "americanfootball_nfl", "completed": True,
            "commence_time": "2025-09-14T20:25:00Z",
            "home_team": "Kansas City Chiefs", "away_team": "Buffalo Bills",
            "scores": [
                {"name": "Kansas City Chiefs", "score": "24"},
                {"name": "Buffalo Bills", "score": "27"},
            ],
        },
    ]
    rows = results_from_scores(payload)
    assert rows == [{
        "sport_key": "americanfootball_nfl", "date": "2025-09-14",
        "home_team": "Kansas City Chiefs", "away_team": "Buffalo Bills",
        "home_score": "24", "away_score": "27",
    }]


def test_results_from_scores_skips_incomplete_and_null():
    payload = [
        {"completed": False, "home_team": "A", "away_team": "B", "scores": None},
        {"completed": True, "home_team": "C", "away_team": "D", "scores": None},
        {"completed": True, "home_team": "E", "away_team": "F",
         "scores": [{"name": "E", "score": "x"}, {"name": "F", "score": "2"}]},
    ]
    assert results_from_scores(payload) == []


def test_results_from_scores_feeds_model_training():
    from edge.model import TeamModel
    payload = [
        {"sport_key": "x", "completed": True, "commence_time": "2025-01-01T00:00:00Z",
         "home_team": "A", "away_team": "B",
         "scores": [{"name": "A", "score": "5"}, {"name": "B", "score": "1"}]},
        {"sport_key": "x", "completed": True, "commence_time": "2025-01-02T00:00:00Z",
         "home_team": "B", "away_team": "A",
         "scores": [{"name": "B", "score": "0"}, {"name": "A", "score": "3"}]},
    ]
    rows = results_from_scores(payload)
    model = TeamModel().train(rows)
    assert "x" in model.sports
