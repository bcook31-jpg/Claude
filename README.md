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
   market?". The consensus uses an O(books) leave-one-out average. De-vig is
   proportional by default or **Shin** (`--devig shin`), which counteracts the
   favourite-longshot bias.
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

# Use Shin de-vig (reduces favourite-longshot bias) instead of proportional
edge scan --devig shin

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
edge journal close 1 120    # record the closing line to measure CLV
edge journal list
edge journal summary        # record, profit, ROI, and CLV
```

The journal is a plain CSV (default `~/.edge/journal.csv`).

**Closing line value (CLV)** is the strongest signal that a bet was placed at
value: `CLV = your_decimal / closing_decimal - 1`. Beating the close
consistently is a better long-run indicator of skill than short-term win/loss.
`edge journal summary` reports your average CLV and how often you beat the
close:

```
Staked: 95.00   Profit: +22.50   ROI: +23.7%
CLV: +2.1% avg over 12 bet(s), beat the close 75% of the time
```

## Predictive models

By default the engine treats the *market* as the model. As an alternative, it
ships two **independent** models that learn from historical results with no
knowledge of the odds. Comparing a model against book prices surfaces bets
where the model disagrees with the market.

| Model | Markets | What it does |
|-------|---------|--------------|
| `elo` | Moneyline | [Elo ratings](https://en.wikipedia.org/wiki/Elo_rating_system) — learns team strength and win probability. |
| `team` | Moneyline, spreads, totals | Gaussian scoring model — learns each team's points for/against, derives an expected **margin** and **total**, and reads cover/over probabilities off a normal distribution. |

```bash
edge train --model team                  # -> ~/.edge/team.json (all markets)
edge train --model elo                   # -> ~/.edge/elo.json  (moneyline)
edge train --model team --results my.csv # train on your own history

edge scan --model team --min-ev 0.03     # model-vs-market edges, all markets
edge scan --model elo                    # moneyline only
```

`--results` columns are **auto-detected** from common aliases (canonical
`sport_key,date,home_team,away_team,home_score,away_score`, but also
`HomeTeam`/`AwayTeam`/`FTHG`/`FTAG` and similar, so real exports like
football-data.co.uk load as-is). Override detection with `--map
home_team=Home` (repeatable) and stamp a constant sport with `--sport-key`
when the file has no sport column. Malformed rows are skipped.

Or skip CSVs entirely and **train on real results pulled live** from The Odds
API's `/scores` endpoint:

```bash
export ODDS_API_KEY=your_key
edge train --model team --live                 # all four majors, last 3 days
edge train --model team --live --sport nfl --days 3
```

**Precision safeguards.** The team model regresses each team's scoring rate
toward the league average (empirical-Bayes shrinkage), so teams with few games
are not treated as confidently as those with many; and the margin/total
standard deviations are floored at sane per-sport values so the model is never
more confident than the sport's real-world variance allows.

> **Caveat — a model is only as good as its data.** The bundled sample has just
> ~10 games per sport, so the models are **overconfident**: their "edges" mostly
> reflect disagreement with the market, not guaranteed value. Market consensus
> (the default) is the more reliable signal; treat the models as a second
> opinion, and train on a full season of real results before trusting the
> numbers. The `outcome_probability` interface is the seam where a stronger
> model (logistic regression, gradient boosting, ...) can be dropped in.

## Backtesting

Replay a strategy over historical odds + results to see how it would actually
have performed — including **CLV**, the best long-run skill signal.

```bash
edge backtest                          # market consensus, flat stake, sample data
edge backtest --min-ev 0.02 --devig shin
edge backtest --stake kelly --bankroll 1000
edge backtest --model team --stake kelly   # backtest a trained model
edge backtest --data my_settled_events.json
```

Each settled event supplies the odds that were available, the final score, and
(optionally) the closing lines:

```json
{
  "event":   { "...": "The Odds API shape — odds when betting" },
  "result":  {"home_score": 27, "away_score": 24},
  "closing": { "...": "The Odds API shape — closing lines (optional, for CLV)" }
}
```

The runner places every bet the strategy recommends, grades it against the
result (moneyline / spread / total, including pushes), and reports:

```
Bets: 12   Record: 7-5-0 (W-L-P)
Staked: 12.00   Profit: +3.55   ROI: +29.6%
CLV: +6.5% avg over 11 bet(s), beat the close 100% of the time
```

That 7-5 record with positive ROI and consistent +CLV is the point: a +EV
strategy wins long-term even when individual bets lose.

### Building a real dataset

`edge build-dataset` assembles settled events from **real** data by joining two
historical odds snapshots (opening + closing) to results, keyed by event id
(consistent across The Odds API's `/odds`, `/scores` and historical endpoints):

```bash
edge build-dataset --sport nfl \
    --open-date 2025-09-14T12:00:00Z \
    --close-date 2025-09-14T17:00:00Z \
    --out nfl_week2.json
edge backtest --data nfl_week2.json --stake kelly
```

Requirements and limits:

- The historical-odds endpoint needs a **paid** Odds API plan (and costs
  10 × markets × regions per snapshot — quota usage is printed after the run).
- Results come from `/scores`, which only covers the **last 3 days**, so the
  snapshot dates must be recent. For older history you'd need to capture scores
  at the time.

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

Every live command prints your remaining **quota** (from the API's
`x-requests-remaining` / `x-requests-last` headers), so you can see what each
call cost — handy because `/odds` is billed *markets × regions* per sport:

```
(quota remaining: 487, last call cost: 3, used: 13)
```

List which sports are currently in season (handy because off-season sports
return no odds). This hits the free `/sports` endpoint and costs no quota:

```bash
export ODDS_API_KEY=your_key
edge sports            # in-season sports and their keys
edge sports --all      # include out-of-season sports
edge sports --counts   # also show upcoming event counts per sport
```

A live smoke test confirms the round trip end-to-end. It is skipped unless a
key is present, so the default test run stays offline:

```bash
ODDS_API_KEY=your_key pytest tests/test_live.py -v
```

## Project layout

```
edge/
  odds_math.py        # conversions, de-vig (proportional/Shin), EV, Kelly, CLV
  models.py           # Event / Bookmaker / Outcome (The Odds API shape)
  engine.py           # de-vig → fair value → +EV finder (market + model)
  model.py            # predictive models: Elo + Gaussian team scoring model
  backtest.py         # bet grader + strategy replay (ROI / CLV)
  dataset.py          # join historical odds + results into a backtest dataset
  journal.py          # CSV bet journal (record / profit / ROI / CLV)
  cli.py              # scan, journal, train, sports, backtest, build-dataset
  providers/          # MockProvider, TheOddsApiProvider (pluggable seam)
  data/               # sample_odds.json, historical_results.csv, backtest_events.json
tests/                # pytest suite (math, engine, model, journal, loader, backtest, cli, live)
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
