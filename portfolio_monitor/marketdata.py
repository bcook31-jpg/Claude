"""Market data pull via yfinance.

No network calls happen at import time. ``yfinance`` is imported lazily inside
the functions that need it, so this module (and the package) stays importable
even where yfinance is missing or the network is blocked.

Mark rules:
  - Option mark = mid = (bid + ask) / 2 when both bid and ask are present
    (> 0); otherwise fall back to last.
  - Share mark = current spot.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


def _is_pos(x) -> bool:
    try:
        return x is not None and float(x) > 0 and not math.isnan(float(x))
    except (TypeError, ValueError):
        return False


def _num(x) -> Optional[float]:
    """Coerce to float, mapping NaN/None to None."""
    try:
        if x is None:
            return None
        f = float(x)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def compute_mark(bid: Optional[float], ask: Optional[float],
                 last: Optional[float]) -> Optional[float]:
    """Mid when both bid and ask are positive, else last."""
    if _is_pos(bid) and _is_pos(ask):
        return (float(bid) + float(ask)) / 2.0
    return _num(last)


@dataclass
class OptionQuote:
    ticker: str
    expiry: str          # YYYY-MM-DD
    option_type: str     # "call" or "put"
    strike: float
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    iv: Optional[float]
    volume: Optional[float]
    open_interest: Optional[float]
    contract_symbol: Optional[str] = None
    in_the_money: Optional[bool] = None
    mark: Optional[float] = field(default=None)

    def __post_init__(self) -> None:
        if self.mark is None:
            self.mark = compute_mark(self.bid, self.ask, self.last)


@dataclass
class ChainSnapshot:
    """The full pulled chain for one underlying on one run."""
    ticker: str
    spot: Optional[float]
    all_expiries: list[str]            # every expiry yfinance lists
    pulled_expiries: list[str]         # expiries we actually pulled rows for
    quotes: list[OptionQuote]          # calls + puts across pulled_expiries


class MarketDataProvider:
    """Thin wrapper over yfinance. Subclass / replace for testing."""

    def _ticker(self, ticker: str):
        import yfinance as yf  # lazy import
        return yf.Ticker(ticker)

    def get_spot(self, ticker: str) -> Optional[float]:
        t = self._ticker(ticker)
        # fast_info is cheapest; fall back to recent close.
        try:
            price = t.fast_info.last_price
            if _is_pos(price):
                return float(price)
        except Exception:
            pass
        try:
            hist = t.history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
        except Exception:
            pass
        return None

    def list_expiries(self, ticker: str) -> list[str]:
        t = self._ticker(ticker)
        try:
            return list(t.options or [])
        except Exception:
            return []

    def get_expiry_quotes(self, ticker: str, expiry: str) -> list[OptionQuote]:
        """Pull all call and put rows for one (ticker, expiry)."""
        t = self._ticker(ticker)
        chain = t.option_chain(expiry)
        quotes: list[OptionQuote] = []
        for option_type, frame in (("call", chain.calls), ("put", chain.puts)):
            for row in frame.itertuples(index=False):
                d = row._asdict()
                quotes.append(OptionQuote(
                    ticker=ticker.upper(),
                    expiry=expiry,
                    option_type=option_type,
                    strike=float(d["strike"]),
                    bid=_num(d.get("bid")),
                    ask=_num(d.get("ask")),
                    last=_num(d.get("lastPrice")),
                    iv=_num(d.get("impliedVolatility")),
                    volume=_num(d.get("volume")),
                    open_interest=_num(d.get("openInterest")),
                    contract_symbol=d.get("contractSymbol"),
                    in_the_money=bool(d["inTheMoney"]) if d.get("inTheMoney") is not None else None,
                ))
        return quotes

    def get_chain_snapshot(self, ticker: str, expiries: list[str]) -> ChainSnapshot:
        """Pull spot, the list of all expiries, and full chains for ``expiries``."""
        spot = self.get_spot(ticker)
        all_expiries = self.list_expiries(ticker)
        pulled: list[str] = []
        quotes: list[OptionQuote] = []
        for expiry in expiries:
            try:
                rows = self.get_expiry_quotes(ticker, expiry)
            except Exception:
                continue
            pulled.append(expiry)
            quotes.extend(rows)
        return ChainSnapshot(
            ticker=ticker.upper(),
            spot=spot,
            all_expiries=all_expiries,
            pulled_expiries=pulled,
            quotes=quotes,
        )


def find_quote(snapshot: ChainSnapshot, option_type: str, strike: float,
               expiry: str) -> Optional[OptionQuote]:
    """Locate a specific held contract within a pulled chain snapshot."""
    for q in snapshot.quotes:
        if (q.option_type == option_type.lower()
                and q.expiry == expiry
                and math.isclose(q.strike, strike, rel_tol=0, abs_tol=1e-6)):
            return q
    return None
