"""Tests for per-position valuation and the end-to-end run with a fake feed."""

import math
from datetime import date

from portfolio_monitor.cli import run
from portfolio_monitor.marketdata import (ChainSnapshot, MarketDataProvider,
                                          OptionQuote, compute_mark)
from portfolio_monitor.positions import OptionPosition, SharePosition
from portfolio_monitor.valuation import value_position


def test_compute_mark_prefers_mid():
    assert compute_mark(1.0, 3.0, 5.0) == 2.0
    assert compute_mark(0, 0, 5.0) == 5.0   # no bid/ask -> last
    assert compute_mark(None, None, None) is None


def test_option_value_uses_100_multiplier():
    pos = OptionPosition(ticker="AAPL", option_type="call", strike=210,
                         expiry=date(2026, 9, 18), entry_price=8.45,
                         contracts=2, entry_date=date(2026, 5, 20),
                         target_price=18.0, stop_price=4.0)
    v = value_position(pos, mark=10.0, asof=date(2026, 6, 15),
                       spot=205.0, iv=0.30)
    # 2 contracts * 100 shares * $10 = $2000
    assert v.current_value == 2000.0
    assert v.cost_basis == 8.45 * 2 * 100
    assert math.isclose(v.unrealized_pnl, 2000.0 - 1690.0)
    assert v.dte == (date(2026, 9, 18) - date(2026, 6, 15)).days
    assert v.greeks is not None
    assert v.position_greeks["delta"] == v.greeks["delta"] * 200


def test_progress_to_target_and_stop():
    pos = OptionPosition(ticker="X", option_type="call", strike=10,
                         expiry=date(2026, 12, 18), entry_price=10.0,
                         contracts=1, entry_date=date(2026, 1, 1),
                         target_price=20.0, stop_price=5.0)
    # mark halfway from entry(10) to target(20)
    v = value_position(pos, mark=15.0, asof=date(2026, 6, 15), spot=11, iv=0.3)
    assert math.isclose(v.progress_to_target_pct, 50.0)
    # 15 vs stop: (15-10)/(5-10) = -100% -> moving away
    assert math.isclose(v.progress_to_stop_pct, -100.0)
    assert "to target" in v.progress_phrase


def test_share_value_and_missing_mark():
    pos = SharePosition(ticker="NVDA", entry_price=100.0, contracts=50,
                        entry_date=date(2026, 1, 1), target_price=160, stop_price=95)
    v = value_position(pos, mark=120.0, asof=date(2026, 6, 15))
    assert v.current_value == 6000.0
    assert v.dte is None
    nm = value_position(pos, mark=None, asof=date(2026, 6, 15))
    assert nm.current_value is None and nm.unrealized_pnl is None


class _FakeProvider(MarketDataProvider):
    """Deterministic feed so the orchestration can be tested offline."""

    def get_chain_snapshot(self, ticker, expiries):
        spot = {"AAPL": 215.0, "MSFT": 390.0, "NVDA": 130.0}[ticker]
        quotes = []
        for exp in expiries:
            quotes.append(OptionQuote(ticker=ticker, expiry=exp, option_type="call",
                                      strike=210, bid=11.0, ask=13.0, last=12.5,
                                      iv=0.31, volume=100, open_interest=500))
            quotes.append(OptionQuote(ticker=ticker, expiry=exp, option_type="put",
                                      strike=400, bid=14.0, ask=16.0, last=15.0,
                                      iv=0.28, volume=80, open_interest=300))
        return ChainSnapshot(ticker=ticker, spot=spot,
                             all_expiries=list(expiries), pulled_expiries=list(expiries),
                             quotes=quotes)


def test_end_to_end_run(tmp_path):
    db = tmp_path / "portfolio.db"
    snaps = tmp_path / "snapshots"
    valuations, snapshots = run(
        positions_path="positions.json", asof=date(2026, 6, 15), rate=0.045,
        db_path=db, snapshots_dir=snaps, provider=_FakeProvider(),
    )
    assert len(valuations) == 3
    # AAPL call mark = mid(11,13) = 12.0
    aapl = next(v for v in valuations if v.ticker == "AAPL")
    assert aapl.mark == 12.0
    assert aapl.greeks is not None
    # snapshot JSON written for each underlying that has options
    assert (snaps / "AAPL_2026-06-15.json").exists()
    assert (snaps / "MSFT_2026-06-15.json").exists()
    # NVDA is shares-only: no option expiries, but still snapshotted (spot)
    assert db.exists()
