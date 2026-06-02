"""A simple CSV-backed bet journal.

Tracks placed bets and computes record / profit / ROI. Persistence is a plain
CSV file (stdlib only) so it is easy to inspect or import into a spreadsheet.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import odds_math as om

FIELDNAMES = [
    "id", "placed_at", "event", "market", "selection", "point",
    "book", "price", "stake", "status", "profit",
]

VALID_STATUS = {"pending", "win", "loss", "push"}


@dataclass
class Bet:
    id: str
    placed_at: str
    event: str
    market: str
    selection: str
    point: Optional[float]
    book: str
    price: int            # American odds
    stake: float
    status: str = "pending"
    profit: float = 0.0


class Journal:
    def __init__(self, path: Path):
        self.path = Path(path)

    # -- persistence -------------------------------------------------------
    def _read(self) -> list[Bet]:
        if not self.path.exists():
            return []
        bets: list[Bet] = []
        with self.path.open(newline="") as f:
            for row in csv.DictReader(f):
                bets.append(
                    Bet(
                        id=row["id"],
                        placed_at=row["placed_at"],
                        event=row["event"],
                        market=row["market"],
                        selection=row["selection"],
                        point=float(row["point"]) if row["point"] else None,
                        book=row["book"],
                        price=int(row["price"]),
                        stake=float(row["stake"]),
                        status=row["status"],
                        profit=float(row["profit"]),
                    )
                )
        return bets

    def _write(self, bets: list[Bet]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for b in bets:
                writer.writerow(asdict(b))

    # -- operations --------------------------------------------------------
    def add(
        self,
        event: str,
        market: str,
        selection: str,
        book: str,
        price: int,
        stake: float,
        point: Optional[float] = None,
    ) -> Bet:
        bets = self._read()
        bet = Bet(
            id=_next_id(bets),
            placed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            event=event,
            market=market,
            selection=selection,
            point=point,
            book=book,
            price=price,
            stake=stake,
        )
        bets.append(bet)
        self._write(bets)
        return bet

    def settle(self, bet_id: str, status: str) -> Bet:
        if status not in VALID_STATUS:
            raise ValueError(f"status must be one of {sorted(VALID_STATUS)}")
        bets = self._read()
        for b in bets:
            if b.id == bet_id:
                b.status = status
                b.profit = _profit(b.price, b.stake, status)
                self._write(bets)
                return b
        raise KeyError(f"No bet with id {bet_id!r}")

    def list(self) -> list[Bet]:
        return self._read()

    def summary(self) -> dict:
        bets = self._read()
        settled = [b for b in bets if b.status in {"win", "loss", "push"}]
        staked = sum(b.stake for b in settled)
        profit = sum(b.profit for b in settled)
        return {
            "total_bets": len(bets),
            "pending": sum(1 for b in bets if b.status == "pending"),
            "wins": sum(1 for b in bets if b.status == "win"),
            "losses": sum(1 for b in bets if b.status == "loss"),
            "pushes": sum(1 for b in bets if b.status == "push"),
            "staked": staked,
            "profit": profit,
            "roi": (profit / staked) if staked > 0 else 0.0,
        }


def _profit(price: int, stake: float, status: str) -> float:
    if status == "win":
        return stake * (om.american_to_decimal(price) - 1.0)
    if status == "loss":
        return -stake
    return 0.0  # push


def _next_id(bets: list[Bet]) -> str:
    nums = [int(b.id) for b in bets if b.id.isdigit()]
    return str((max(nums) + 1) if nums else 1)
