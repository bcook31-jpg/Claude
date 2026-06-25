"""Positions book: load and validate positions.json.

One book holds two row types, distinguished by ``asset_type``:
  - "option": ticker, option_type (call/put), strike, expiry, entry_price
    (per-share premium), contracts, entry_date, optional target/stop (per share).
  - "shares": ticker, entry_price (per share), contracts (= number of shares),
    entry_date, target/stop (per share).

For options, entry_price / target_price / stop_price are PER SHARE. Each
contract controls 100 shares, so the per-contract dollar value is price * 100.
``contract_multiplier`` exposes this (100 for options, 1 for shares).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union

OPTION_MULTIPLIER = 100  # shares per option contract


def _parse_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be YYYY-MM-DD, got {value!r}") from exc


@dataclass
class OptionPosition:
    ticker: str
    option_type: str  # "call" or "put"
    strike: float
    expiry: date
    entry_price: float  # per share premium
    contracts: float
    entry_date: date
    target_price: Optional[float] = None  # per share
    stop_price: Optional[float] = None    # per share
    id: str = ""

    asset_type: str = field(default="option", init=False)
    contract_multiplier: int = field(default=OPTION_MULTIPLIER, init=False)

    def __post_init__(self) -> None:
        self.option_type = self.option_type.lower()
        if self.option_type not in ("call", "put"):
            raise ValueError(
                f"option_type must be 'call' or 'put', got {self.option_type!r}"
            )
        if not self.id:
            self.id = self.auto_id()

    def auto_id(self) -> str:
        """Stable id from ticker + option_type + strike + expiry.

        option_type is included so a call and put at the same strike/expiry
        do not collide.
        """
        strike_str = f"{self.strike:g}"
        letter = "C" if self.option_type == "call" else "P"
        return f"{self.ticker.upper()}_{letter}_{strike_str}_{self.expiry.isoformat()}"


@dataclass
class SharePosition:
    ticker: str
    entry_price: float  # per share
    contracts: float    # number of shares
    entry_date: date
    target_price: Optional[float] = None
    stop_price: Optional[float] = None
    id: str = ""

    asset_type: str = field(default="shares", init=False)
    contract_multiplier: int = field(default=1, init=False)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"{self.ticker.upper()}_SHARES"


Position = Union[OptionPosition, SharePosition]


def _build_option(row: dict) -> OptionPosition:
    required = ["ticker", "option_type", "strike", "expiry", "entry_price",
                "contracts", "entry_date"]
    _require(row, required, "option")
    return OptionPosition(
        ticker=str(row["ticker"]).upper(),
        option_type=str(row["option_type"]),
        strike=float(row["strike"]),
        expiry=_parse_date(row["expiry"], "expiry"),
        entry_price=float(row["entry_price"]),
        contracts=float(row["contracts"]),
        entry_date=_parse_date(row["entry_date"], "entry_date"),
        target_price=_opt_float(row.get("target_price")),
        stop_price=_opt_float(row.get("stop_price")),
        id=str(row.get("id") or ""),
    )


def _build_shares(row: dict) -> SharePosition:
    required = ["ticker", "entry_price", "contracts", "entry_date"]
    _require(row, required, "shares")
    return SharePosition(
        ticker=str(row["ticker"]).upper(),
        entry_price=float(row["entry_price"]),
        contracts=float(row["contracts"]),
        entry_date=_parse_date(row["entry_date"], "entry_date"),
        target_price=_opt_float(row.get("target_price")),
        stop_price=_opt_float(row.get("stop_price")),
        id=str(row.get("id") or ""),
    )


def _require(row: dict, fields: list[str], kind: str) -> None:
    missing = [f for f in fields if row.get(f) is None]
    if missing:
        raise ValueError(f"{kind} row missing required field(s): {', '.join(missing)}")


def _opt_float(value) -> Optional[float]:
    return None if value is None else float(value)


def parse_position(row: dict) -> Position:
    asset_type = row.get("asset_type")
    if asset_type == "option":
        return _build_option(row)
    if asset_type == "shares":
        return _build_shares(row)
    raise ValueError(
        f"asset_type must be 'option' or 'shares', got {asset_type!r}"
    )


def load_positions(path: Union[str, Path]) -> list[Position]:
    """Load and validate positions.json. Returns a list of Position objects.

    The file may be a JSON list of rows, or an object with a "positions" key.
    Raises ValueError on the first invalid row, with the row index for context.
    """
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = data.get("positions", [])
    if not isinstance(data, list):
        raise ValueError("positions file must be a JSON list (or {'positions': [...]})")

    out: list[Position] = []
    seen_ids: set[str] = set()
    for i, row in enumerate(data):
        try:
            pos = parse_position(row)
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"positions[{i}]: {exc}") from exc
        if pos.id in seen_ids:
            raise ValueError(f"positions[{i}]: duplicate id {pos.id!r}")
        seen_ids.add(pos.id)
        out.append(pos)
    return out
