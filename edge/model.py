"""Predictive models: an independent view of fair value.

Unlike the market-based engine (which treats the consensus of books as fair
value), these models predict probabilities from historical results, with no
knowledge of the odds. Comparing their probabilities against book prices
surfaces bets the market may have mispriced relative to the model.

Two models are provided, sharing one interface --
``outcome_probability(event, market_key, outcome) -> float | None``:

* ``EloModel``  -- Elo ratings; prices the moneyline (head-to-head) only.
* ``TeamModel`` -- a Gaussian scoring model that prices the moneyline, spreads
  and totals. It learns each team's points-for / points-against, derives an
  expected margin and total for a matchup, and reads off cover/over
  probabilities from a normal distribution whose spread is estimated from the
  data (floored by sane per-sport defaults so it is never overconfident).

Both are transparent and dependency-free; the shared interface is the seam
where a heavier model (logistic regression, gradient boosting, ...) could be
dropped in.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .models import H2H, SPREADS, TOTALS, Event, Outcome

DEFAULT_RATING = 1500.0
DEFAULT_K = 20.0           # update step size
DEFAULT_HOME_ADV = 65.0   # home-field advantage, in Elo points


def _normal_cdf(z: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: list[float]) -> float:
    """Sample standard deviation (0 for fewer than two points)."""
    n = len(xs)
    if n < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def _shrink(xs: list[float], target: float, k: float) -> float:
    """Mean of ``xs`` regressed toward ``target`` by ``k`` pseudo-observations."""
    n = len(xs)
    return (sum(xs) + k * target) / (n + k) if (n + k) > 0 else target


class EloModel:
    def __init__(
        self,
        k: float = DEFAULT_K,
        home_advantage: float = DEFAULT_HOME_ADV,
        base_rating: float = DEFAULT_RATING,
    ):
        self.k = k
        self.home_advantage = home_advantage
        self.base_rating = base_rating
        self.ratings: dict[str, float] = {}

    def rating(self, team: str) -> float:
        return self.ratings.get(team, self.base_rating)

    def win_probability(self, home: str, away: str) -> float:
        """Probability the home team wins, given current ratings."""
        diff = self.rating(home) + self.home_advantage - self.rating(away)
        return 1.0 / (1.0 + 10.0 ** (-diff / 400.0))

    def update(self, home: str, away: str, home_score: int, away_score: int) -> None:
        """Update ratings after a single observed result."""
        expected = self.win_probability(home, away)
        if home_score > away_score:
            outcome = 1.0
        elif home_score < away_score:
            outcome = 0.0
        else:
            outcome = 0.5
        change = self.k * (outcome - expected)
        self.ratings[home] = self.rating(home) + change
        self.ratings[away] = self.rating(away) - change

    def train(self, games: Iterable[dict]) -> "EloModel":
        """Train on an iterable of game dicts (home_team/away_team/scores)."""
        for g in games:
            self.update(
                g["home_team"], g["away_team"],
                int(g["home_score"]), int(g["away_score"]),
            )
        return self

    def predict(self, home: str, away: str) -> dict[str, float]:
        """Win probabilities keyed by team name."""
        p_home = self.win_probability(home, away)
        return {home: p_home, away: 1.0 - p_home}

    def predict_event(self, event: Event) -> dict[str, float]:
        return self.predict(event.home_team, event.away_team)

    def outcome_probability(
        self, event: Event, market_key: str, outcome: Outcome
    ) -> Optional[float]:
        """Model probability for an outcome; Elo prices the moneyline only."""
        if market_key != H2H:
            return None
        return self.predict_event(event).get(outcome.name)

    # -- persistence -------------------------------------------------------
    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "k": self.k,
            "home_advantage": self.home_advantage,
            "base_rating": self.base_rating,
            "ratings": self.ratings,
        }, indent=2))

    @classmethod
    def load(cls, path: Path) -> "EloModel":
        data = json.loads(Path(path).read_text())
        model = cls(
            k=data["k"],
            home_advantage=data["home_advantage"],
            base_rating=data["base_rating"],
        )
        model.ratings = dict(data["ratings"])
        return model


# Per-sport floors for the margin / total standard deviations, so the model is
# never more confident than the sport's real-world variance allows.
DEFAULT_SIGMA: dict[str, tuple[float, float]] = {
    "americanfootball_nfl": (13.5, 10.5),
    "basketball_nba": (12.0, 18.0),
    "baseball_mlb": (4.0, 4.0),
    "icehockey_nhl": (2.2, 2.6),
}


@dataclass
class SportStats:
    pts_for: dict[str, float]      # mean points scored, per team
    pts_against: dict[str, float]  # mean points allowed, per team
    home_adv: float                # mean home margin (points)
    sigma_margin: float
    sigma_total: float


DEFAULT_SHRINK = 4.0  # pseudo-games pulling each team toward the league average


class TeamModel:
    """Gaussian scoring model covering moneyline, spreads and totals.

    Team scoring rates are shrunk toward the league average (empirical-Bayes
    style) by ``shrink`` pseudo-games, so teams with only a handful of results
    are not treated as confidently as teams with a long history. This keeps the
    model from becoming wildly overconfident on thin data.
    """

    def __init__(
        self,
        default_sigma: tuple[float, float] = (10.0, 10.0),
        shrink: float = DEFAULT_SHRINK,
    ):
        self.default_sigma = default_sigma
        self.shrink = shrink
        self.sports: dict[str, SportStats] = {}

    def train(self, games: Iterable[dict]) -> "TeamModel":
        by_sport: dict[str, list[dict]] = defaultdict(list)
        for g in games:
            by_sport[g.get("sport_key", "")].append(g)

        for sport, gs in by_sport.items():
            scored: dict[str, list[float]] = defaultdict(list)
            allowed: dict[str, list[float]] = defaultdict(list)
            margins: list[float] = []
            for g in gs:
                h, a = g["home_team"], g["away_team"]
                hs, as_ = int(g["home_score"]), int(g["away_score"])
                scored[h].append(hs); allowed[h].append(as_)
                scored[a].append(as_); allowed[a].append(hs)
                margins.append(hs - as_)

            # League average points per team-game, used as the shrinkage target.
            league_avg = _mean([v for vals in scored.values() for v in vals])
            pts_for = {t: _shrink(v, league_avg, self.shrink) for t, v in scored.items()}
            pts_against = {t: _shrink(v, league_avg, self.shrink) for t, v in allowed.items()}
            home_adv = _mean(margins)

            res_margin, res_total = [], []
            for g in gs:
                h, a = g["home_team"], g["away_team"]
                hs, as_ = int(g["home_score"]), int(g["away_score"])
                eh, ea = _expected_scores(pts_for, pts_against, home_adv, h, a)
                res_margin.append((hs - as_) - (eh - ea))
                res_total.append((hs + as_) - (eh + ea))

            floor_m, floor_t = DEFAULT_SIGMA.get(sport, self.default_sigma)
            self.sports[sport] = SportStats(
                pts_for=pts_for,
                pts_against=pts_against,
                home_adv=home_adv,
                sigma_margin=max(_std(res_margin), floor_m),
                sigma_total=max(_std(res_total), floor_t),
            )
        return self

    def expected(self, event: Event) -> Optional[tuple[float, float]]:
        """Expected (margin, total) for the matchup, or None if unknown."""
        s = self.sports.get(event.sport_key)
        if s is None or event.home_team not in s.pts_for or event.away_team not in s.pts_for:
            return None
        eh, ea = _expected_scores(
            s.pts_for, s.pts_against, s.home_adv, event.home_team, event.away_team
        )
        return eh - ea, eh + ea

    def outcome_probability(
        self, event: Event, market_key: str, outcome: Outcome
    ) -> Optional[float]:
        s = self.sports.get(event.sport_key)
        expected = self.expected(event)
        if s is None or expected is None:
            return None
        mu_margin, mu_total = expected
        home, away = event.home_team, event.away_team

        if market_key == H2H:
            if outcome.name == home:
                return _normal_cdf(mu_margin / s.sigma_margin)
            if outcome.name == away:
                return _normal_cdf(-mu_margin / s.sigma_margin)
            return None

        if market_key == SPREADS:
            if outcome.point is None:
                return None
            # Bet wins if (team_margin + point) > 0.
            if outcome.name == home:
                return _normal_cdf((mu_margin + outcome.point) / s.sigma_margin)
            if outcome.name == away:
                return _normal_cdf((outcome.point - mu_margin) / s.sigma_margin)
            return None

        if market_key == TOTALS:
            if outcome.point is None:
                return None
            z = (mu_total - outcome.point) / s.sigma_total
            name = outcome.name.lower()
            if name == "over":
                return _normal_cdf(z)
            if name == "under":
                return _normal_cdf(-z)
            return None

        return None

    # -- persistence -------------------------------------------------------
    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "default_sigma": list(self.default_sigma),
            "shrink": self.shrink,
            "sports": {
                sport: {
                    "pts_for": s.pts_for,
                    "pts_against": s.pts_against,
                    "home_adv": s.home_adv,
                    "sigma_margin": s.sigma_margin,
                    "sigma_total": s.sigma_total,
                }
                for sport, s in self.sports.items()
            },
        }, indent=2))

    @classmethod
    def load(cls, path: Path) -> "TeamModel":
        data = json.loads(Path(path).read_text())
        model = cls(
            default_sigma=tuple(data["default_sigma"]),
            shrink=data.get("shrink", DEFAULT_SHRINK),
        )
        model.sports = {
            sport: SportStats(
                pts_for={k: float(v) for k, v in s["pts_for"].items()},
                pts_against={k: float(v) for k, v in s["pts_against"].items()},
                home_adv=s["home_adv"],
                sigma_margin=s["sigma_margin"],
                sigma_total=s["sigma_total"],
            )
            for sport, s in data["sports"].items()
        }
        return model


def _expected_scores(
    pts_for: dict[str, float],
    pts_against: dict[str, float],
    home_adv: float,
    home: str,
    away: str,
) -> tuple[float, float]:
    """Expected (home_points, away_points) for a matchup."""
    eh = (pts_for[home] + pts_against[away]) / 2.0 + home_adv / 2.0
    ea = (pts_for[away] + pts_against[home]) / 2.0 - home_adv / 2.0
    return eh, ea


# Common header aliases so real-world result files load without manual mapping
# (covers e.g. football-data.co.uk's HomeTeam/FTHG style and generic exports).
_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "sport_key": ("sport_key", "sport", "league", "competition"),
    "date": ("date", "datetime", "commence_time", "game_date", "kickoff"),
    "home_team": ("home_team", "hometeam", "home", "home_name", "home_club"),
    "away_team": ("away_team", "awayteam", "away", "away_name", "away_club"),
    "home_score": ("home_score", "homescore", "home_goals", "fthg", "hg", "score_home"),
    "away_score": ("away_score", "awayscore", "away_goals", "ftag", "ag", "score_away"),
}
_REQUIRED = ("home_team", "away_team", "home_score", "away_score")


def load_results(
    path: Path,
    mapping: Optional[dict[str, str]] = None,
    default_sport: Optional[str] = None,
) -> list[dict]:
    """Load historical game results from a CSV into canonical row dicts.

    Canonical fields are ``sport_key, date, home_team, away_team, home_score,
    away_score``. Source columns are matched case-insensitively against a set
    of common aliases (so e.g. ``HomeTeam``/``FTHG`` style files load as-is);
    ``mapping`` overrides this per field (canonical -> source column).

    ``sport_key`` may be absent from the file -- supply ``default_sport`` to
    stamp every row with one (required by the TeamModel, optional for Elo).
    Rows missing a required field or with non-integer scores are skipped.
    """
    mapping = mapping or {}
    with Path(path).open(newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        resolved = _resolve_columns(headers, mapping, default_sport)
        rows = []
        for raw in reader:
            row = _canonicalise(raw, resolved, default_sport)
            if row is not None:
                rows.append(row)
    return rows


def _resolve_columns(
    headers: list[str], mapping: dict[str, str], default_sport: Optional[str]
) -> dict[str, str]:
    """Map each canonical field to an actual source column name."""
    lower = {h.lower(): h for h in headers}
    resolved: dict[str, str] = {}
    for field, aliases in _FIELD_ALIASES.items():
        if field in mapping:
            resolved[field] = mapping[field]
        else:
            for alias in aliases:
                if alias in lower:
                    resolved[field] = lower[alias]
                    break
    missing = [f for f in _REQUIRED if f not in resolved]
    if missing:
        raise ValueError(
            f"Could not find column(s) for {missing} in {headers}. "
            f"Pass an explicit mapping, e.g. home_team=Home."
        )
    return resolved


def _canonicalise(
    raw: dict, resolved: dict[str, str], default_sport: Optional[str]
) -> Optional[dict]:
    row = {field: (raw.get(col) or "").strip() for field, col in resolved.items()}
    if not row.get("sport_key"):
        row["sport_key"] = default_sport or ""
    if not all(row.get(f) for f in _REQUIRED):
        return None
    try:
        int(row["home_score"]); int(row["away_score"])
    except ValueError:
        return None
    return row
