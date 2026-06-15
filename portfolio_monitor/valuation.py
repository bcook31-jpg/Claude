"""Per-position valuation: mark, value, P&L, DTE, progress to target/stop."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Optional

from .greeks import Greeks, black_scholes_greeks
from .positions import OptionPosition, Position, SharePosition


@dataclass
class Valuation:
    position_id: str
    asset_type: str
    ticker: str
    contracts: float
    contract_multiplier: int
    entry_price: float
    mark: Optional[float]
    current_value: Optional[float]
    cost_basis: float
    unrealized_pnl: Optional[float]
    unrealized_pnl_pct: Optional[float]
    dte: Optional[int]
    target_price: Optional[float]
    stop_price: Optional[float]
    progress_to_target_pct: Optional[float]
    progress_to_stop_pct: Optional[float]
    progress_phrase: str
    greeks: Optional[dict] = None
    position_greeks: Optional[dict] = None

    def as_dict(self) -> dict:
        return asdict(self)


def _pct_progress(entry: float, level: Optional[float],
                  mark: Optional[float]) -> Optional[float]:
    """How far ``mark`` has travelled from entry toward ``level``, as a percent.

    0% = still at entry, 100% = reached the level. Works in either direction
    (target above entry, stop below it) because entry is the common origin.
    """
    if level is None or mark is None:
        return None
    denom = level - entry
    if denom == 0:
        return None
    return (mark - entry) / denom * 100.0


def _phrase(to_target: Optional[float], to_stop: Optional[float]) -> str:
    parts = []
    if to_target is not None:
        if to_target >= 100:
            parts.append("target reached")
        elif to_target <= 0:
            parts.append("moved away from target")
        else:
            parts.append(f"{to_target:.0f}% to target")
    if to_stop is not None:
        if to_stop >= 100:
            parts.append("stop hit")
        elif to_stop <= 0:
            parts.append("moving away from stop")
        else:
            parts.append(f"{to_stop:.0f}% to stop")
    return "; ".join(parts) if parts else "no target/stop set"


def value_position(
    position: Position,
    mark: Optional[float],
    *,
    asof: date,
    spot: Optional[float] = None,
    iv: Optional[float] = None,
    risk_free_rate: float = 0.045,
) -> Valuation:
    """Value a single position given its current mark.

    For options, pass ``spot`` and ``iv`` to also compute greeks. ``mark`` and
    the prices are PER SHARE; dollar figures apply the contract multiplier.
    """
    mult = position.contract_multiplier
    cost_basis = position.entry_price * position.contracts * mult

    if mark is None:
        current_value = None
        pnl = None
        pnl_pct = None
    else:
        current_value = mark * position.contracts * mult
        pnl = current_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100.0) if cost_basis else None

    dte: Optional[int] = None
    greeks_dict: Optional[dict] = None
    position_greeks: Optional[dict] = None
    if isinstance(position, OptionPosition):
        dte = (position.expiry - asof).days
        if spot is not None and iv is not None:
            g: Greeks = black_scholes_greeks(
                option_type=position.option_type,
                spot=spot,
                strike=position.strike,
                days_to_expiry=max(dte, 0),
                iv=iv,
                risk_free_rate=risk_free_rate,
            )
            greeks_dict = g.as_dict()
            scale = position.contracts * mult
            position_greeks = {k: v * scale for k, v in greeks_dict.items()}

    to_target = _pct_progress(position.entry_price, position.target_price, mark)
    to_stop = _pct_progress(position.entry_price, position.stop_price, mark)

    return Valuation(
        position_id=position.id,
        asset_type=position.asset_type,
        ticker=position.ticker,
        contracts=position.contracts,
        contract_multiplier=mult,
        entry_price=position.entry_price,
        mark=mark,
        current_value=current_value,
        cost_basis=cost_basis,
        unrealized_pnl=pnl,
        unrealized_pnl_pct=pnl_pct,
        dte=dte,
        target_price=position.target_price,
        stop_price=position.stop_price,
        progress_to_target_pct=to_target,
        progress_to_stop_pct=to_stop,
        progress_phrase=_phrase(to_target, to_stop),
        greeks=greeks_dict,
        position_greeks=position_greeks,
    )
