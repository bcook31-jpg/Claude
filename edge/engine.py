"""The value-betting engine.

Pipeline (the market-based modelling approach):

1. For every book, de-vig each market it offers to get clean per-book
   probabilities (the book's own "fair" line, margin removed).
2. Estimate the *fair probability* of each selection from the rest of the
   market -- either the consensus of the other books, or a single designated
   sharp book (e.g. Pinnacle).
3. For every price a book is offering, compute EV against that fair
   probability. A book pricing a selection better than the market's fair value
   is a +EV opportunity.

This finds genuine line discrepancies without needing an independent
predictive model: the market itself is the model.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

from . import odds_math as om
from .models import MARKET_KEYS, MARKET_LABELS, Event


@dataclass
class ValueBet:
    sport_title: str
    commence_time: str
    matchup: str
    market: str          # market key (h2h/spreads/totals)
    market_label: str    # human label
    selection: str
    point: Optional[float]
    book: str            # book title offering the price
    price: int           # American odds
    decimal: float
    fair_prob: float
    ev: float            # expected profit per unit staked (0.05 == +5%)
    kelly: float         # full-Kelly fraction of bankroll
    sources: int         # how many books backed the fair estimate

    @property
    def ev_pct(self) -> float:
        return self.ev * 100.0


SelectionId = tuple[str, Optional[float]]


def _devigged_book_probs(
    event: Event, market_key: str
) -> dict[str, dict[SelectionId, float]]:
    """For each book, the de-vigged probability of each selection in a market."""
    out: dict[str, dict[SelectionId, float]] = {}
    for bm in event.bookmakers:
        offer = bm.market(market_key)
        if offer is None or len(offer.outcomes) < 2:
            continue
        implied = [om.american_to_implied(o.price) for o in offer.outcomes]
        fair = om.devig_proportional(implied)
        out[bm.title] = {
            o.selection_id: p for o, p in zip(offer.outcomes, fair)
        }
    return out


def _book_prices(
    event: Event, market_key: str
) -> dict[str, dict[SelectionId, int]]:
    """For each book, the American price it offers per selection."""
    out: dict[str, dict[SelectionId, int]] = {}
    for bm in event.bookmakers:
        offer = bm.market(market_key)
        if offer is None:
            continue
        out[bm.title] = {o.selection_id: o.price for o in offer.outcomes}
    return out


def find_value_bets(
    events: Iterable[Event],
    *,
    markets: Optional[Iterable[str]] = None,
    sharp_book: Optional[str] = None,
    min_ev: float = 0.0,
) -> list[ValueBet]:
    """Scan events and return +EV bets sorted by EV (descending).

    Parameters
    ----------
    markets:
        Market keys to inspect (defaults to all of h2h/spreads/totals).
    sharp_book:
        If given (matched case-insensitively against book titles), that book's
        de-vigged line is treated as fair value and every *other* book is
        priced against it. Otherwise the consensus of the other books is used.
    min_ev:
        Minimum EV to report (e.g. 0.02 for +2%). Defaults to 0 (any edge).
    """
    market_keys = tuple(markets) if markets else MARKET_KEYS
    results: list[ValueBet] = []

    for event in events:
        for market_key in market_keys:
            book_probs = _devigged_book_probs(event, market_key)
            book_prices = _book_prices(event, market_key)
            if len(book_probs) < 2:
                # Need at least two books to have a market to compare against.
                continue

            sharp_title = _resolve_sharp(book_probs, sharp_book)

            for book_title, prices in book_prices.items():
                if sharp_title and book_title == sharp_title:
                    continue  # never bet the reference line against itself
                for sel, price in prices.items():
                    fair_prob, sources = _fair_probability(
                        book_probs, sel, evaluating_book=book_title,
                        sharp_title=sharp_title,
                    )
                    if fair_prob is None:
                        continue
                    decimal = om.american_to_decimal(price)
                    ev = om.expected_value(fair_prob, decimal)
                    if ev < min_ev:
                        continue
                    results.append(
                        ValueBet(
                            sport_title=event.sport_title,
                            commence_time=event.commence_time,
                            matchup=event.matchup,
                            market=market_key,
                            market_label=MARKET_LABELS.get(market_key, market_key),
                            selection=sel[0],
                            point=sel[1],
                            book=book_title,
                            price=price,
                            decimal=decimal,
                            fair_prob=fair_prob,
                            ev=ev,
                            kelly=om.kelly_fraction(fair_prob, decimal),
                            sources=sources,
                        )
                    )

    results.sort(key=lambda v: v.ev, reverse=True)
    return results


def _resolve_sharp(
    book_probs: dict[str, dict[SelectionId, float]], sharp_book: Optional[str]
) -> Optional[str]:
    """Match a requested sharp book name to an actual book title."""
    if not sharp_book:
        return None
    target = sharp_book.lower()
    for title in book_probs:
        if title.lower() == target:
            return title
    return None


def _fair_probability(
    book_probs: dict[str, dict[SelectionId, float]],
    sel: SelectionId,
    *,
    evaluating_book: str,
    sharp_title: Optional[str],
) -> tuple[Optional[float], int]:
    """Fair probability for a selection, excluding the book being evaluated.

    In sharp mode the fair value is the sharp book's line. Otherwise it is the
    average de-vigged probability across all *other* books offering the exact
    same selection (same point). Excluding the evaluated book keeps the
    comparison honest: we ask "is this book off vs the rest of the market?".
    """
    if sharp_title:
        p = book_probs.get(sharp_title, {}).get(sel)
        return (p, 1) if p is not None else (None, 0)

    others = [
        probs[sel]
        for title, probs in book_probs.items()
        if title != evaluating_book and sel in probs
    ]
    if not others:
        return None, 0
    return sum(others) / len(others), len(others)
