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
