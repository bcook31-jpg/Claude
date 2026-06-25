# Portfolio Monitor — data & valuation layer

Layer 1 of an options + equity portfolio monitor. It loads a positions book,
pulls live market data (yfinance), computes Black-Scholes greeks locally,
snapshots the pulled option chains (JSON + SQLite), and values each position.
Modules are import-clean (no network at import time) so later layers — e.g. a
diff/alerting layer — can build on top.

## Install & run

```bash
pip install -r requirements.txt
python -m portfolio_monitor.cli --positions positions.json --asof 2026-06-15
```

Flags:

| flag | default | meaning |
|------|---------|---------|
| `--positions` | `positions.json` | positions book to load |
| `--asof YYYY-MM-DD` | today | run date stamped on all stored rows / snapshots, used for later diffing. **Marks still come from the current feed — there is no historical chain reconstruction.** |
| `--rate` | `0.045` | annual risk-free rate for greeks |
| `--db` | `portfolio.db` | single SQLite database |
| `--snapshots-dir` | `snapshots` | directory for dated JSON chain snapshots |

## positions.json

One book, two row types keyed by `asset_type`:

- **option**: `id` (optional — auto-generated from ticker+type+strike+expiry if
  omitted), `ticker`, `option_type` (`call`/`put`), `strike`, `expiry`
  (`YYYY-MM-DD`), `entry_price` (per-share premium), `contracts`, `entry_date`,
  optional `target_price` / `stop_price` (per share).
- **shares**: `id` (optional), `ticker`, `entry_price` (per share), `contracts`
  (= number of shares), `entry_date`, `target_price`, `stop_price`.

For **options every price is per share**. One contract controls 100 shares, so
per-contract dollar value is `price * 100`. See `positions.json` for examples.

## What it computes

- **Marks** — option mark = mid `(bid+ask)/2` when both are present, else last;
  share mark = current spot.
- **Greeks** (Black-Scholes, no external lib) — delta, gamma, theta, vega per
  share, from the contract's IV, a configurable risk-free rate, and actual
  calendar days to expiry. Conventions: theta per calendar day, vega per 1 IV
  percentage-point. Position-level greeks = per-share × contracts × 100.
- **Valuation** — mark, current value, unrealized P&L ($ and %), DTE (options),
  and progress to target / stop as percentages with a human phrase
  (0% = at entry, 100% = level reached).

## Storage

Everything goes to a single SQLite db (`runs`, `underlyings`, `chain_quotes`,
`valuations`). The full pulled chain per underlying is also written to
`snapshots/TICKER_YYYY-MM-DD.json` and mirrored into `chain_quotes`. Writes are
keyed on the run date, so re-running the same `--asof` replaces that date's rows.

Per underlying we pull the full chain for each **held expiry** and record the
complete available-expiry list — enough for a later layer to diff today vs a
prior run for new-strike / new-expiry detection and IV history.

## Tests

```bash
python -m pytest tests/ -q
```

Greeks, positions, and valuation are covered offline; the end-to-end run is
tested with a deterministic fake feed (no network required).

## Modules

| module | responsibility |
|--------|----------------|
| `positions.py` | load/validate the book, id generation |
| `marketdata.py` | yfinance pulls, mark logic, chain snapshots |
| `greeks.py` | Black-Scholes greeks |
| `valuation.py` | per-position P&L / DTE / progress |
| `storage.py` | SQLite schema + JSON snapshots |
| `cli.py` | orchestration, `--asof`, report |
