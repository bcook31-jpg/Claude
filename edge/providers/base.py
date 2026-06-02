"""The pluggable provider seam.

Any odds source (mock data, The Odds API, a future scraper, a database)
implements ``OddsProvider`` and returns the same ``Event`` objects, so the
engine and CLI never need to know where the odds came from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..models import Event


class OddsProvider(ABC):
    @abstractmethod
    def get_odds(
        self,
        sport_keys: Optional[Iterable[str]] = None,
        markets: Optional[Iterable[str]] = None,
    ) -> list[Event]:
        """Return events with bookmaker odds.

        ``sport_keys`` and ``markets`` are optional filters; a provider may
        return everything it has if they are omitted.
        """
        raise NotImplementedError
