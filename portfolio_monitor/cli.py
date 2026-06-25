"""Command-line entry point: pull data, snapshot, value, persist, report.

Usage:
    python -m portfolio_monitor.cli [--positions positions.json] [--asof YYYY-MM-DD]
        [--rate 0.045] [--db portfolio.db] [--snapshots-dir snapshots]

--asof stamps the run date used for storage and later diffing. Marks always
come from the current feed; there is no historical chain reconstruction.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from . import storage
from .marketdata import (ChainSnapshot, MarketDataProvider, find_quote)
from .positions import OptionPosition, SharePosition, load_positions
from .valuation import value_position


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Options + equity portfolio monitor (data + valuation layer).")
    p.add_argument("--positions", default="positions.json", help="positions JSON file")
    p.add_argument("--asof", default=None, help="run date YYYY-MM-DD (default: today)")
    p.add_argument("--rate", type=float, default=0.045, help="annual risk-free rate (default 0.045)")
    p.add_argument("--db", default="portfolio.db", help="SQLite database path")
    p.add_argument("--snapshots-dir", default="snapshots", help="directory for dated JSON snapshots")
    return p.parse_args(argv)


def _resolve_asof(value) -> date:
    if value is None:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def run(positions_path, asof, rate, db_path, snapshots_dir,
        provider: MarketDataProvider | None = None):
    """Pull data, snapshot, value, persist. Returns (valuations, snapshots)."""
    provider = provider or MarketDataProvider()
    positions = load_positions(positions_path)
    run_date = asof.isoformat()

    # Group the expiries we need to pull per ticker (held option expiries).
    expiries_by_ticker: dict[str, set[str]] = {}
    for pos in positions:
        expiries_by_ticker.setdefault(pos.ticker, set())
        if isinstance(pos, OptionPosition):
            expiries_by_ticker[pos.ticker].add(pos.expiry.isoformat())

    conn = storage.connect(db_path)
    storage.record_run(conn, run_date, rate)

    snapshots: dict[str, ChainSnapshot] = {}
    for ticker, expiries in expiries_by_ticker.items():
        snap = provider.get_chain_snapshot(ticker, sorted(expiries))
        snapshots[ticker] = snap
        storage.write_snapshot_json(snap, run_date, snapshots_dir)
        storage.mirror_snapshot_to_sqlite(conn, snap, run_date)

    valuations = []
    for pos in positions:
        snap = snapshots.get(pos.ticker)
        if isinstance(pos, OptionPosition):
            quote = find_quote(snap, pos.option_type, pos.strike,
                               pos.expiry.isoformat()) if snap else None
            mark = quote.mark if quote else None
            iv = quote.iv if quote else None
            spot = snap.spot if snap else None
            val = value_position(pos, mark, asof=asof, spot=spot, iv=iv,
                                 risk_free_rate=rate)
        else:  # SharePosition
            spot = snap.spot if snap else None
            val = value_position(pos, spot, asof=asof)
        valuations.append(val)

    storage.write_valuations(conn, valuations, run_date)
    conn.close()
    return valuations, snapshots


def _fmt(x, spec="", dash="—"):
    return dash if x is None else format(x, spec)


def print_report(valuations, run_date: str) -> None:
    print(f"\nPortfolio valuation — as of {run_date}\n" + "=" * 72)
    total_value = 0.0
    total_pnl = 0.0
    have_value = False
    for v in valuations:
        kind = v.asset_type.upper()
        print(f"\n[{kind}] {v.position_id}  ({v.ticker})")
        print(f"  mark={_fmt(v.mark, '.4f')}  "
              f"value={_fmt(v.current_value, ',.2f')}  cost={_fmt(v.cost_basis, ',.2f')}")
        print(f"  unrealized P&L: {_fmt(v.unrealized_pnl, ',.2f')} "
              f"({_fmt(v.unrealized_pnl_pct, '+.1f')}%)")
        if v.dte is not None:
            print(f"  DTE: {v.dte}")
        print(f"  progress: {v.progress_phrase}")
        if v.greeks:
            g = v.greeks
            print(f"  greeks (per share): delta={g['delta']:.4f} gamma={g['gamma']:.5f} "
                  f"theta={g['theta']:.4f}/day vega={g['vega']:.4f}/IV-pt")
        if v.current_value is not None:
            total_value += v.current_value
            total_pnl += v.unrealized_pnl or 0.0
            have_value = True
    print("\n" + "=" * 72)
    if have_value:
        print(f"TOTAL value={total_value:,.2f}  unrealized P&L={total_pnl:,.2f}")
    else:
        print("No marks available (market data could not be pulled).")


def main(argv=None) -> int:
    args = parse_args(argv)
    asof = _resolve_asof(args.asof)
    valuations, _ = run(
        positions_path=args.positions,
        asof=asof,
        rate=args.rate,
        db_path=args.db,
        snapshots_dir=args.snapshots_dir,
    )
    print_report(valuations, asof.isoformat())
    print(f"\nStored to {Path(args.db).resolve()} (run_date={asof.isoformat()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
