"""Live provider for The Odds API (https://the-odds-api.com).

Uses only the standard library (urllib) so the core package stays
dependency-free. Supply an API key via the constructor or the
``ODDS_API_KEY`` environment variable. The free tier is enough to try it.

Example
-------
    provider = TheOddsApiProvider()  # reads ODDS_API_KEY
    events = provider.get_odds(["americanfootball_nfl"], ["h2h", "spreads"])
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Iterable, Optional

from ..models import Event, event_from_dict
from .base import OddsProvider

BASE_URL = "https://api.the-odds-api.com/v4"
DEFAULT_SPORTS = (
    "americanfootball_nfl",
    "basketball_nba",
    "baseball_mlb",
    "icehockey_nhl",
)


class TheOddsApiProvider(OddsProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        regions: str = "us",
        odds_format: str = "american",
        timeout: float = 15.0,
    ):
        self.api_key = api_key or os.environ.get("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key. Pass api_key=... or set ODDS_API_KEY in the environment."
            )
        self.regions = regions
        self.odds_format = odds_format
        self.timeout = timeout

    def get_sports(self, all_sports: bool = False) -> list[dict]:
        """List available sports.

        By default returns only in-season ("active") sports. Pass
        ``all_sports=True`` to include out-of-season ones. This hits the free
        ``/sports`` endpoint and does not consume request quota. Each item has
        keys like ``key``, ``group``, ``title``, ``description`` and ``active``.
        """
        params = {"apiKey": self.api_key}
        if all_sports:
            params["all"] = "true"
        url = f"{BASE_URL}/sports/?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode())

    def get_events(self, sport_key: str) -> list[dict]:
        """Upcoming/live events for a sport, without odds.

        Hits the free ``/events`` endpoint (no quota cost). Useful for counting
        how many games are on the board for a sport. Each item has ``id``,
        ``commence_time``, ``home_team`` and ``away_team``.
        """
        params = urllib.parse.urlencode({"apiKey": self.api_key})
        url = f"{BASE_URL}/sports/{sport_key}/events/?{params}"
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode())

    def get_scores(self, sport_key: str, days_from: Optional[int] = 3) -> list[dict]:
        """Scores for live and recently-completed games.

        ``days_from`` (1-3) includes completed games from up to N days ago;
        omit it to get only live and upcoming games. Each item has ``id``,
        ``sport_key``, ``commence_time``, ``home_team``, ``away_team``,
        ``completed`` and a ``scores`` list of ``{"name", "score"}`` (null until
        the game has data). Hits the free ``/scores`` endpoint -- completed
        games cost a small amount of quota, upcoming ones are free.
        """
        params = {"apiKey": self.api_key}
        if days_from is not None:
            params["daysFrom"] = str(days_from)
        url = f"{BASE_URL}/sports/{sport_key}/scores/?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode())

    def get_odds(
        self,
        sport_keys: Optional[Iterable[str]] = None,
        markets: Optional[Iterable[str]] = None,
    ) -> list[Event]:
        sports = list(sport_keys) if sport_keys else list(DEFAULT_SPORTS)
        market_param = ",".join(markets) if markets else "h2h,spreads,totals"

        events: list[Event] = []
        for sport in sports:
            params = urllib.parse.urlencode(
                {
                    "apiKey": self.api_key,
                    "regions": self.regions,
                    "markets": market_param,
                    "oddsFormat": self.odds_format,
                }
            )
            url = f"{BASE_URL}/sports/{sport}/odds/?{params}"
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode())
            events.extend(event_from_dict(e) for e in payload)
        return events
