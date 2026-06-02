"""Command-line interface for the Edge value-betting engine.

Examples
--------
    edge scan                          # scan bundled sample odds for +EV bets
    edge scan --min-ev 0.03            # only show edges of +3% or better
    edge scan --sport nfl --market h2h
    edge scan --sharp Pinnacle --bankroll 1000
    edge scan --live --sport nfl       # use The Odds API (needs ODDS_API_KEY)

    edge journal add --event "Bills @ Chiefs" --market h2h \\
        --selection "Buffalo Bills" --book Caesars --price 135 --stake 50
    edge journal list
    edge journal settle 1 win
    edge journal summary
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .engine import ValueBet, find_value_bets
from .journal import Journal
from .providers import MockProvider, TheOddsApiProvider

# Friendly aliases -> The Odds API sport keys.
SPORT_ALIASES = {
    "nfl": "americanfootball_nfl",
    "nba": "basketball_nba",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
}

DEFAULT_JOURNAL = Path.home() / ".edge" / "journal.csv"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="edge", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    _add_scan_parser(sub)
    _add_journal_parser(sub)

    args = parser.parse_args(argv)
    return args.func(args)


# -- scan -----------------------------------------------------------------
def _add_scan_parser(sub) -> None:
    p = sub.add_parser("scan", help="find +EV bets across books")
    p.add_argument("--sport", help="filter by sport (nfl/nba/mlb/nhl or a full key)")
    p.add_argument("--market", choices=["h2h", "spreads", "totals"],
                   help="filter by market (default: all)")
    p.add_argument("--min-ev", type=float, default=0.0,
                   help="minimum EV to report, e.g. 0.03 for +3%% (default 0)")
    p.add_argument("--sharp", help="treat this book as fair value (e.g. Pinnacle); "
                                   "default uses the consensus of other books")
    p.add_argument("--bankroll", type=float,
                   help="if set, show the suggested Kelly stake in dollars")
    p.add_argument("--live", action="store_true",
                   help="use The Odds API instead of bundled sample data "
                        "(requires ODDS_API_KEY)")
    p.set_defaults(func=_run_scan)


def _run_scan(args) -> int:
    sport_keys = None
    if args.sport:
        sport_keys = [SPORT_ALIASES.get(args.sport.lower(), args.sport)]
    markets = [args.market] if args.market else None

    try:
        provider = TheOddsApiProvider() if args.live else MockProvider()
        events = provider.get_odds(sport_keys, markets)
    except Exception as exc:  # network / key / data errors -> friendly message
        print(f"Failed to fetch odds: {exc}", file=sys.stderr)
        return 1

    bets = find_value_bets(events, markets=markets, sharp_book=args.sharp,
                           min_ev=args.min_ev)
    _print_value_bets(bets, bankroll=args.bankroll, sharp=args.sharp)
    return 0


def _print_value_bets(bets: list[ValueBet], bankroll: Optional[float],
                       sharp: Optional[str]) -> None:
    basis = f"sharp book '{sharp}'" if sharp else "market consensus"
    if not bets:
        print(f"No +EV bets found (fair value = {basis}).")
        return

    print(f"Found {len(bets)} +EV bet(s). Fair value = {basis}.\n")
    header = ["EV%", "Sport", "Matchup", "Market", "Selection", "Book", "Odds", "Fair%", "Kelly"]
    if bankroll:
        header.append("Stake$")
    rows = []
    for b in bets:
        sel = b.selection + (f" {b.point:+g}" if b.point is not None else "")
        row = [
            f"+{b.ev_pct:.1f}",
            b.sport_title,
            b.matchup,
            b.market_label,
            sel,
            b.book,
            _fmt_american(b.price),
            f"{b.fair_prob * 100:.1f}",
            f"{b.kelly * 100:.1f}%",
        ]
        if bankroll:
            row.append(f"{b.kelly * bankroll:,.2f}")
        rows.append(row)
    _print_table(header, rows)


# -- journal --------------------------------------------------------------
def _add_journal_parser(sub) -> None:
    p = sub.add_parser("journal", help="track placed bets and ROI")
    p.add_argument("--file", type=Path, default=DEFAULT_JOURNAL,
                   help=f"journal CSV path (default {DEFAULT_JOURNAL})")
    jsub = p.add_subparsers(dest="action", required=True)

    add = jsub.add_parser("add", help="record a placed bet")
    add.add_argument("--event", required=True)
    add.add_argument("--market", required=True)
    add.add_argument("--selection", required=True)
    add.add_argument("--book", required=True)
    add.add_argument("--price", type=int, required=True, help="American odds")
    add.add_argument("--stake", type=float, required=True)
    add.add_argument("--point", type=float, default=None)

    settle = jsub.add_parser("settle", help="settle a bet")
    settle.add_argument("id")
    settle.add_argument("status", choices=["win", "loss", "push"])

    close = jsub.add_parser("close", help="record the closing line to measure CLV")
    close.add_argument("id")
    close.add_argument("price", type=int, help="closing American odds for the selection")

    jsub.add_parser("list", help="list all bets")
    jsub.add_parser("summary", help="show record, profit and ROI")

    p.set_defaults(func=_run_journal)


def _run_journal(args) -> int:
    journal = Journal(args.file)
    if args.action == "add":
        bet = journal.add(args.event, args.market, args.selection, args.book,
                          args.price, args.stake, args.point)
        print(f"Logged bet #{bet.id}: {bet.selection} @ {_fmt_american(bet.price)} "
              f"({bet.book}) for {bet.stake:g}")
        return 0
    if args.action == "settle":
        bet = journal.settle(args.id, args.status)
        print(f"Bet #{bet.id} settled {bet.status}: profit {bet.profit:+.2f}")
        return 0
    if args.action == "close":
        bet = journal.close(args.id, args.price)
        print(f"Bet #{bet.id} closing line {_fmt_american(bet.price)} -> "
              f"{_fmt_american(args.price)}: CLV {bet.clv * 100:+.1f}%")
        return 0
    if args.action == "list":
        _print_journal(journal)
        return 0
    if args.action == "summary":
        _print_summary(journal)
        return 0
    return 1


def _print_journal(journal: Journal) -> None:
    bets = journal.list()
    if not bets:
        print("No bets logged yet.")
        return
    header = ["ID", "Placed", "Event", "Selection", "Book", "Odds", "Stake",
              "Status", "Profit", "Close", "CLV%"]
    rows = [
        [b.id, b.placed_at, b.event,
         b.selection + (f" {b.point:+g}" if b.point is not None else ""),
         b.book, _fmt_american(b.price), f"{b.stake:g}", b.status, f"{b.profit:+.2f}",
         _fmt_american(b.closing_price) if b.closing_price is not None else "-",
         f"{b.clv * 100:+.1f}" if b.clv is not None else "-"]
        for b in bets
    ]
    _print_table(header, rows)


def _print_summary(journal: Journal) -> None:
    s = journal.summary()
    print(f"Bets: {s['total_bets']}  (pending {s['pending']})")
    print(f"Record: {s['wins']}-{s['losses']}-{s['pushes']} (W-L-P)")
    print(f"Staked: {s['staked']:.2f}   Profit: {s['profit']:+.2f}   "
          f"ROI: {s['roi'] * 100:+.1f}%")
    if s["with_closing"]:
        print(f"CLV: {s['avg_clv'] * 100:+.1f}% avg over {s['with_closing']} bet(s), "
              f"beat the close {s['beat_close_rate'] * 100:.0f}% of the time")


# -- formatting helpers ----------------------------------------------------
def _fmt_american(price: int) -> str:
    return f"+{price}" if price > 0 else str(price)


def _print_table(header: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(header))
    print(line)
    print("  ".join("-" * widths[i] for i in range(len(header))))
    for row in rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))


if __name__ == "__main__":
    raise SystemExit(main())
