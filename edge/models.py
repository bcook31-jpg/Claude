"""Domain models for odds data.

The shape intentionally mirrors The Odds API (the-odds-api.com) response
format so that a real provider and the bundled mock provider are
interchangeable, and raw API JSON maps onto these objects with no translation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Market keys used throughout the engine (same strings The Odds API uses).
H2H = "h2h"          # moneyline
SPREADS = "spreads"  # point spread / handicap
TOTALS = "totals"    # over/under

MARKET_KEYS = (H2H, SPREADS, TOTALS)

MARKET_LABELS = {
    H2H: "Moneyline",
    SPREADS: "Spread",
    TOTALS: "Total",
}


@dataclass(frozen=True)
class Outcome:
    """A single selection a book is pricing.

    ``point`` is None for moneylines and carries the line for spreads/totals
    (e.g. -3.5 for a spread, 45.5 for a total).
    """

    name: str
    price: int  # American odds
    point: Optional[float] = None

    @property
    def selection_id(self) -> tuple[str, Optional[float]]:
        """Identity used to compare like-for-like across books."""
        return (self.name, self.point)


@dataclass
class MarketOffer:
    """One bookmaker's set of outcomes for a single market type."""

    key: str  # one of MARKET_KEYS
    outcomes: list[Outcome]


@dataclass
class Bookmaker:
    key: str
    title: str
    markets: list[MarketOffer]

    def market(self, key: str) -> Optional[MarketOffer]:
        for m in self.markets:
            if m.key == key:
                return m
        return None


@dataclass
class Event:
    id: str
    sport_key: str
    sport_title: str
    commence_time: str  # ISO 8601 string
    home_team: str
    away_team: str
    bookmakers: list[Bookmaker]

    @property
    def matchup(self) -> str:
        return f"{self.away_team} @ {self.home_team}"


def event_from_dict(data: dict) -> Event:
    """Build an Event from a The Odds API style dict."""
    bookmakers = [
        Bookmaker(
            key=b["key"],
            title=b.get("title", b["key"]),
            markets=[
                MarketOffer(
                    key=m["key"],
                    outcomes=[
                        Outcome(
                            name=o["name"],
                            price=int(o["price"]),
                            point=o.get("point"),
                        )
                        for o in m["outcomes"]
                    ],
                )
                for m in b.get("markets", [])
            ],
        )
        for b in data.get("bookmakers", [])
    ]
    return Event(
        id=data["id"],
        sport_key=data["sport_key"],
        sport_title=data.get("sport_title", data["sport_key"]),
        commence_time=data["commence_time"],
        home_team=data["home_team"],
        away_team=data["away_team"],
        bookmakers=bookmakers,
    )
