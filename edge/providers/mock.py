"""Offline provider backed by a bundled sample odds file.

Lets the whole engine and CLI run with zero network access or API keys. The
sample data spans NFL/NBA/MLB/NHL across moneyline, spread and total markets,
and deliberately includes a few mispriced lines so ``edge scan`` surfaces
real +EV opportunities out of the box.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from ..models import Event, event_from_dict
from .base import OddsProvider

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "sample_odds.json"


class MockProvider(OddsProvider):
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = Path(data_path) if data_path else DEFAULT_DATA

    def get_odds(
        self,
        sport_keys: Optional[Iterable[str]] = None,
        markets: Optional[Iterable[str]] = None,
    ) -> list[Event]:
        raw = json.loads(self.data_path.read_text())
        events = [event_from_dict(e) for e in raw]

        if sport_keys:
            wanted = set(sport_keys)
            events = [e for e in events if e.sport_key in wanted]

        if markets:
            wanted_markets = set(markets)
            for e in events:
                for bm in e.bookmakers:
                    bm.markets = [m for m in bm.markets if m.key in wanted_markets]

        return events
