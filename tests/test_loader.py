import pytest

from edge.model import load_results


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
