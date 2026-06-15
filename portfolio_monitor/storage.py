"""Persistence: dated JSON chain snapshots + a single SQLite database.

Everything lands in one SQLite db so later layers can diff today vs a prior
run (new-strike / new-expiry detection, IV history). The full pulled chain per
underlying is also written to snapshots/TICKER_YYYY-MM-DD.json and mirrored
into the ``chain_quotes`` table.

Writes are keyed on the run date (``--asof``), so re-running the same as-of
date replaces that date's rows rather than duplicating them.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Union

from .marketdata import ChainSnapshot
from .valuation import Valuation

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_date        TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    risk_free_rate  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chain_quotes (
    run_date        TEXT NOT NULL,
    ticker          TEXT NOT NULL,
    expiry          TEXT NOT NULL,
    option_type     TEXT NOT NULL,
    strike          REAL NOT NULL,
    bid             REAL,
    ask             REAL,
    last            REAL,
    mark            REAL,
    iv              REAL,
    volume          REAL,
    open_interest   REAL,
    contract_symbol TEXT,
    in_the_money    INTEGER,
    PRIMARY KEY (run_date, ticker, expiry, option_type, strike)
);

CREATE TABLE IF NOT EXISTS underlyings (
    run_date     TEXT NOT NULL,
    ticker       TEXT NOT NULL,
    spot         REAL,
    all_expiries TEXT,
    PRIMARY KEY (run_date, ticker)
);

CREATE TABLE IF NOT EXISTS valuations (
    run_date              TEXT NOT NULL,
    position_id           TEXT NOT NULL,
    asset_type            TEXT NOT NULL,
    ticker                TEXT NOT NULL,
    contracts             REAL,
    contract_multiplier   INTEGER,
    entry_price           REAL,
    mark                  REAL,
    current_value         REAL,
    cost_basis            REAL,
    unrealized_pnl        REAL,
    unrealized_pnl_pct    REAL,
    dte                   INTEGER,
    target_price          REAL,
    stop_price            REAL,
    progress_to_target_pct REAL,
    progress_to_stop_pct  REAL,
    progress_phrase       TEXT,
    greeks_json           TEXT,
    position_greeks_json  TEXT,
    PRIMARY KEY (run_date, position_id)
);
"""


def connect(db_path: Union[str, Path]) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    return conn


def record_run(conn: sqlite3.Connection, run_date: str, risk_free_rate: float) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO runs (run_date, created_at, risk_free_rate) VALUES (?, ?, ?)",
        (run_date, datetime.now().isoformat(timespec="seconds"), risk_free_rate),
    )
    conn.commit()


def write_snapshot_json(snapshot: ChainSnapshot, run_date: str,
                        snapshots_dir: Union[str, Path]) -> Path:
    """Write the full pulled chain to snapshots/TICKER_YYYY-MM-DD.json."""
    out_dir = Path(snapshots_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{snapshot.ticker}_{run_date}.json"
    payload = {
        "run_date": run_date,
        "ticker": snapshot.ticker,
        "spot": snapshot.spot,
        "all_expiries": snapshot.all_expiries,
        "pulled_expiries": snapshot.pulled_expiries,
        "quotes": [asdict(q) for q in snapshot.quotes],
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def mirror_snapshot_to_sqlite(conn: sqlite3.Connection, snapshot: ChainSnapshot,
                              run_date: str) -> None:
    """Mirror the JSON snapshot into chain_quotes + underlyings."""
    conn.execute(
        "INSERT OR REPLACE INTO underlyings (run_date, ticker, spot, all_expiries) VALUES (?, ?, ?, ?)",
        (run_date, snapshot.ticker, snapshot.spot, json.dumps(snapshot.all_expiries)),
    )
    # Replace this run's rows for this ticker, then insert fresh.
    conn.execute(
        "DELETE FROM chain_quotes WHERE run_date = ? AND ticker = ?",
        (run_date, snapshot.ticker),
    )
    conn.executemany(
        """INSERT OR REPLACE INTO chain_quotes
           (run_date, ticker, expiry, option_type, strike, bid, ask, last, mark,
            iv, volume, open_interest, contract_symbol, in_the_money)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (run_date, q.ticker, q.expiry, q.option_type, q.strike, q.bid, q.ask,
             q.last, q.mark, q.iv, q.volume, q.open_interest, q.contract_symbol,
             None if q.in_the_money is None else int(q.in_the_money))
            for q in snapshot.quotes
        ],
    )
    conn.commit()


def write_valuations(conn: sqlite3.Connection, valuations: Iterable[Valuation],
                     run_date: str) -> None:
    conn.executemany(
        """INSERT OR REPLACE INTO valuations
           (run_date, position_id, asset_type, ticker, contracts, contract_multiplier,
            entry_price, mark, current_value, cost_basis, unrealized_pnl,
            unrealized_pnl_pct, dte, target_price, stop_price,
            progress_to_target_pct, progress_to_stop_pct, progress_phrase,
            greeks_json, position_greeks_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (run_date, v.position_id, v.asset_type, v.ticker, v.contracts,
             v.contract_multiplier, v.entry_price, v.mark, v.current_value,
             v.cost_basis, v.unrealized_pnl, v.unrealized_pnl_pct, v.dte,
             v.target_price, v.stop_price, v.progress_to_target_pct,
             v.progress_to_stop_pct, v.progress_phrase,
             json.dumps(v.greeks) if v.greeks else None,
             json.dumps(v.position_greeks) if v.position_greeks else None)
            for v in valuations
        ],
    )
    conn.commit()
