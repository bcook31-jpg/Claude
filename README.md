# Edge — Odds Comparison & Value-Betting Engine

A small, dependency-free Python engine that does what EdgeTerminal-style tools
do at their core: pull odds from multiple sportsbooks, strip out the
bookmaker margin ("vig"), estimate each outcome's **fair probability** from the
market, and surface **positive expected-value (+EV)** bets — with Kelly stake
sizing and a bet journal to track ROI.

> The market is the model. Instead of predicting games from scratch, the engine
> uses the consensus of sharp, efficient books as fair value and flags any book
> pricing a selection better than that fair value.

## How it works

```
odds (many books)  ─▶  de-vig each book  ─▶  fair probability  ─▶  EV per price  ─▶  +EV bets
                       (remove margin)        (consensus or            (p·dec − 1)     (sorted, with
                                               a sharp book)                            Kelly stakes)
```

1. **De-vig** — each book's market is normalised so its outcomes sum to 100%,
   removing the hold.
2. **Fair value** — for each selection, fair probability is the *consensus of
   the other books* (default), or a single designated **sharp book**
   (`--sharp Pinnacle`). The book being priced is excluded from its own
   benchmark, so the question is always "is this book off vs the rest of the
   market?".
3. **EV & Kelly** — `EV = fair_prob × decimal_odds − 1`; Kelly fraction sizes
   the stake.

Coverage: **NFL, NBA, MLB, NHL** across **moneyline (h2h), spreads, and
totals**.

## Install

```bash
pip install -e .            # installs the `edge` CLI
pip install -e ".[dev]"     # plus pytest
```

No third-party dependencies are required for the core engine.

## CLI

```bash
# Scan bundled sample odds for +EV bets (works offline)
edge scan

# Only show edges of +3% or better, with $1,000 Kelly stake sizing
edge scan --min-ev 0.03 --bankroll 1000

# Filter by sport / market, or benchmark against a sharp book
edge scan --sport nfl --market h2h
edge scan --sharp Pinnacle

# Use live odds from The Odds API instead of sample data
export ODDS_API_KEY=your_key_here
edge scan --live --sport nfl
```

Example output:

```
Found 12 +EV bet(s). Fair value = market consensus.

EV%   Sport  Matchup                             Market     Selection      Book     Odds  Fair%  Kelly  Stake$
+6.5  NFL    Buffalo Bills @ Kansas City Chiefs  Moneyline  Buffalo Bills  Caesars  +135  45.3   4.8%   48.46
...
```

### Bet journal

```bash
edge journal add --event "Bills @ Chiefs" --market h2h \
    --selection "Buffalo Bills" --book Caesars --price 135 --stake 50
edge journal settle 1 win
edge journal list
edge journal summary        # record, profit, ROI
```

The journal is a plain CSV (default `~/.edge/journal.csv`).

## Library

```python
from edge import MockProvider, find_value_bets

events = MockProvider().get_odds()              # or TheOddsApiProvider()
bets = find_value_bets(events, min_ev=0.03, sharp_book="Pinnacle")
for b in bets:
    print(b.matchup, b.selection, b.price, f"{b.ev_pct:.1f}% EV")
```

## Live odds

`TheOddsApiProvider` talks to [The Odds API](https://the-odds-api.com) using
only the standard library. Drop in an `ODDS_API_KEY` and the exact same engine
runs on real lines — the data model mirrors that API's response shape, so the
mock and live providers are interchangeable.

## Project layout

```
edge/
  odds_math.py        # conversions, de-vig, EV, Kelly (pure functions)
  models.py           # Event / Bookmaker / Outcome (The Odds API shape)
  engine.py           # de-vig → fair value → +EV finder
  journal.py          # CSV bet journal (record / profit / ROI)
  cli.py              # `edge scan` and `edge journal`
  providers/          # MockProvider, TheOddsApiProvider (pluggable seam)
  data/sample_odds.json
tests/                # pytest suite (odds math + engine)
```

## Tests

```bash
pytest
```

## Responsible use

This is an analytical and educational tool. Sports betting carries financial
risk; bet only what you can afford to lose, follow the laws in your
jurisdiction, and treat all model output as one input among many — not a
guarantee.
