"""A simple, transparent predictive model: Elo ratings.

Unlike the market-based engine (which treats the consensus of books as fair
value), this is an *independent* model -- it predicts win probabilities from
team ratings learned from historical results, with no knowledge of the odds.
Comparing its probabilities against book prices surfaces bets the market may
have mispriced relative to the model.

Elo is deliberately chosen over a heavier ML model: it is well established in
sports forecasting, fully interpretable, needs no third-party libraries, and
produces calibrated win probabilities for moneyline (head-to-head) markets.
The ``predict``/``predict_event`` interface is the seam where a richer model
(logistic regression, gradient boosting, ...) could later be dropped in.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import Event

DEFAULT_RATING = 1500.0
DEFAULT_K = 20.0           # update step size
DEFAULT_HOME_ADV = 65.0   # home-field advantage, in Elo points


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


def load_results(path: Path) -> list[dict]:
    """Load historical game results from a CSV.

    Expected columns: date, home_team, away_team, home_score, away_score.
    """
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))
