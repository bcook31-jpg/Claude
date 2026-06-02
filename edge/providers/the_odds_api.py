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
        # Updated after every request from the API's quota response headers.
        self.requests_remaining: Optional[int] = None
        self.requests_used: Optional[int] = None
        self.last_cost: Optional[int] = None

    def _get_json(self, url: str):
        """Fetch JSON and record quota usage from the response headers."""
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode())
            self._record_quota(resp.headers)
        return body

    def _record_quota(self, headers) -> None:
        def as_int(value) -> Optional[int]:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        self.requests_remaining = as_int(headers.get("x-requests-remaining"))
        self.requests_used = as_int(headers.get("x-requests-used"))
        self.last_cost = as_int(headers.get("x-requests-last"))

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
        return self._get_json(f"{BASE_URL}/sports/?{urllib.parse.urlencode(params)}")

    def get_events(self, sport_key: str) -> list[dict]:
        """Upcoming/live events for a sport, without odds.

        Hits the free ``/events`` endpoint (no quota cost). Useful for counting
        how many games are on the board for a sport. Each item has ``id``,
        ``commence_time``, ``home_team`` and ``away_team``.
        """
        params = urllib.parse.urlencode({"apiKey": self.api_key})
        return self._get_json(f"{BASE_URL}/sports/{sport_key}/events/?{params}")

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
        return self._get_json(
            f"{BASE_URL}/sports/{sport_key}/scores/?{urllib.parse.urlencode(params)}")

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
            payload = self._get_json(f"{BASE_URL}/sports/{sport}/odds/?{params}")
            events.extend(event_from_dict(e) for e in payload)
        return events

    def get_historical_odds(
        self,
        sport_key: str,
        date: str,
        regions: Optional[str] = None,
        markets: Optional[str] = None,
    ) -> dict:
        """Odds snapshot at a past timestamp (paid plans only).

        ``date`` is ISO 8601 (e.g. ``2025-09-14T18:00:00Z``); the API returns
        the closest snapshot at or before it. The result is the raw envelope
        ``{"timestamp", "previous_timestamp", "next_timestamp", "data": [...]}``
        where ``data`` is a list of event dicts in the same shape as ``/odds``.
        ``previous_timestamp`` / ``next_timestamp`` let you walk through time.
        Quota cost is 10 x markets x regions, so use sparingly.
        """
        params = urllib.parse.urlencode({
            "apiKey": self.api_key,
            "regions": regions or self.regions,
            "markets": markets or "h2h,spreads,totals",
            "oddsFormat": self.odds_format,
            "date": date,
        })
        return self._get_json(
            f"{BASE_URL}/historical/sports/{sport_key}/odds/?{params}")
