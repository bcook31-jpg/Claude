"""Backtesting: replay a strategy over historical odds + results.

Given settled events (the odds that were available, plus the final score), this
runs a bet-finding strategy on each event's odds, "places" the recommended
bets, settles them against the actual result, and reports record, ROI and --
when closing lines are supplied -- closing line value (CLV).

A settled event is a dict:

    {
      "event":   { ...The Odds API shape... },   # odds available when betting
      "result":  {"home_score": 27, "away_score": 24},
      "closing": { ...The Odds API shape... }     # optional, for CLV
    }
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from . import odds_math as om
from .engine import ValueBet
from .models import H2H, SPREADS, TOTALS, Event, event_from_dict

# A strategy maps a list of events to the bets it would place.
Strategy = Callable[[list[Event]], list[ValueBet]]


def grade(
    market_key: str,
    name: str,
    point: Optional[float],
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
) -> Optional[str]:
    """Settle a single bet against a final score: 'win' / 'loss' / 'push'.

    Returns None if the bet cannot be graded (e.g. an unrecognised selection).
    """
    if market_key == H2H:
        if home_score == away_score:
            return "push"
        winner = home_team if home_score > away_score else away_team
        return "win" if name == winner else "loss"

    if market_key == SPREADS:
        if point is None:
            return None
        if name == home_team:
            margin = home_score - away_score
        elif name == away_team:
            margin = away_score - home_score
        else:
            return None
        adjusted = margin + point
        if adjusted > 0:
            return "win"
        if adjusted < 0:
            return "loss"
        return "push"

    if market_key == TOTALS:
        if point is None:
            return None
        total = home_score + away_score
        if total == point:
            return "push"
        over = total > point
        label = name.lower()
        if label == "over":
            return "win" if over else "loss"
        if label == "under":
            return "win" if not over else "loss"
        return None

    return None


@dataclass
class BacktestSummary:
    bets: int
    wins: int
    losses: int
    pushes: int
    staked: float
    profit: float
    roi: float
    start_bankroll: float
    end_bankroll: float
    clv_count: int
    avg_clv: float
    beat_close_rate: float


def run_backtest(
    settled_events: Iterable[dict],
    strategy: Strategy,
    *,
    stake: str = "flat",
    unit: float = 1.0,
    bankroll: float = 1000.0,
) -> BacktestSummary:
    """Replay ``strategy`` over settled events and summarise performance.

    ``stake`` is "flat" (``unit`` per bet) or "kelly" (the bet's Kelly fraction
    of the running bankroll). Events are processed in order so Kelly compounds.
    """
    wins = losses = pushes = 0
    staked = profit = 0.0
    clvs: list[float] = []
    bank = bankroll

    for item in settled_events:
        event = event_from_dict(item["event"])
        result = item["result"]
        hs, as_ = int(result["home_score"]), int(result["away_score"])
        close_event = event_from_dict(item["closing"]) if item.get("closing") else None

        for bet in strategy([event]):
            amount = max(0.0, bet.kelly) * bank if stake == "kelly" else unit
            if amount <= 0:
                continue
            outcome = grade(bet.market, bet.selection, bet.point,
                            event.home_team, event.away_team, hs, as_)
            if outcome is None:
                continue

            pnl = _settle(outcome, bet.price, amount)
            staked += amount
            profit += pnl
            bank += pnl
            wins += outcome == "win"
            losses += outcome == "loss"
            pushes += outcome == "push"

            if close_event is not None:
                close_price = _closing_price(close_event, bet.market, bet.selection, bet.point)
                if close_price is not None:
                    clvs.append(om.closing_line_value(bet.price, close_price))

    n = wins + losses + pushes
    return BacktestSummary(
        bets=n,
        wins=wins,
        losses=losses,
        pushes=pushes,
        staked=staked,
        profit=profit,
        roi=(profit / staked) if staked > 0 else 0.0,
        start_bankroll=bankroll,
        end_bankroll=bank,
        clv_count=len(clvs),
        avg_clv=(sum(clvs) / len(clvs)) if clvs else 0.0,
        beat_close_rate=(sum(1 for c in clvs if c > 0) / len(clvs)) if clvs else 0.0,
    )


def _settle(outcome: str, price: int, stake: float) -> float:
    if outcome == "win":
        return stake * (om.american_to_decimal(price) - 1.0)
    if outcome == "loss":
        return -stake
    return 0.0  # push


def _closing_price(
    event: Event, market_key: str, name: str, point: Optional[float]
) -> Optional[int]:
    """Best (most favourable) closing American price for a selection."""
    best_decimal = None
    best_price = None
    for bm in event.bookmakers:
        offer = bm.market(market_key)
        if offer is None:
            continue
        for o in offer.outcomes:
            if o.name == name and o.point == point:
                decimal = om.american_to_decimal(o.price)
                if best_decimal is None or decimal > best_decimal:
                    best_decimal, best_price = decimal, o.price
    return best_price
