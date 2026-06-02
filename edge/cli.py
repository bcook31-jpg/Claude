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

from .engine import ValueBet, find_model_value_bets, find_value_bets
from .journal import Journal
from .model import EloModel, TeamModel, load_results
from .providers import MockProvider, TheOddsApiProvider

# Friendly aliases -> The Odds API sport keys.
SPORT_ALIASES = {
    "nfl": "americanfootball_nfl",
    "nba": "basketball_nba",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
}

DEFAULT_JOURNAL = Path.home() / ".edge" / "journal.csv"
MODEL_PATHS = {
    "elo": Path.home() / ".edge" / "elo.json",
    "team": Path.home() / ".edge" / "team.json",
}
BUNDLED_RESULTS = Path(__file__).resolve().parent / "data" / "historical_results.csv"


def _default_model_path(model: Optional[str]) -> Path:
    return MODEL_PATHS.get(model or "team")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="edge", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    _add_scan_parser(sub)
    _add_journal_parser(sub)
    _add_train_parser(sub)
    _add_sports_parser(sub)

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
    p.add_argument("--devig", choices=["proportional", "shin"], default="proportional",
                   help="de-vig method for the market path (default proportional; "
                        "shin reduces favourite-longshot bias)")
    p.add_argument("--model", choices=["elo", "team"],
                   help="use a predictive model as fair value instead of the "
                        "market (elo: moneyline; team: all markets); train it "
                        "first with 'edge train'")
    p.add_argument("--ratings", type=Path, default=None,
                   help="trained model file for --model (default ~/.edge/<model>.json)")
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

    ratings_path = args.ratings or _default_model_path(args.model)
    if args.model and not ratings_path.exists():
        print(f"No trained model at {ratings_path}. Run 'edge train "
              f"--model {args.model}' first.", file=sys.stderr)
        return 1

    try:
        provider = TheOddsApiProvider() if args.live else MockProvider()
        events = provider.get_odds(sport_keys, markets)
    except Exception as exc:  # network / key / data errors -> friendly message
        print(f"Failed to fetch odds: {exc}", file=sys.stderr)
        return 1

    if args.model:
        model = (EloModel if args.model == "elo" else TeamModel).load(ratings_path)
        bets = find_model_value_bets(events, model, markets=markets, min_ev=args.min_ev)
        basis = f"model '{args.model}'"
    else:
        bets = find_value_bets(events, markets=markets, sharp_book=args.sharp,
                               min_ev=args.min_ev, method=args.devig)
        basis = f"sharp book '{args.sharp}'" if args.sharp else "market consensus"
        if args.devig != "proportional":
            basis += f" ({args.devig} de-vig)"

    _print_value_bets(bets, bankroll=args.bankroll, basis=basis)
    return 0


def _print_value_bets(bets: list[ValueBet], bankroll: Optional[float],
                       basis: str) -> None:
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


# -- train ----------------------------------------------------------------
def _add_train_parser(sub) -> None:
    p = sub.add_parser("train", help="train a predictive model on historical results")
    p.add_argument("--model", choices=["elo", "team"], default="team",
                   help="elo: moneyline ratings; team: all-markets scoring model "
                        "(default)")
    p.add_argument("--results", type=Path, default=BUNDLED_RESULTS,
                   help="CSV of results (sport_key,date,home_team,away_team,"
                        "home_score,away_score); default uses bundled sample data")
    p.add_argument("--out", type=Path, default=None,
                   help="where to save the model (default ~/.edge/<model>.json)")
    p.add_argument("--k", type=float, default=20.0, help="Elo update step (default 20)")
    p.add_argument("--home-adv", type=float, default=65.0,
                   help="Elo home-field advantage in rating points (default 65)")
    p.set_defaults(func=_run_train)


def _run_train(args) -> int:
    try:
        games = load_results(args.results)
    except FileNotFoundError:
        print(f"Results file not found: {args.results}", file=sys.stderr)
        return 1

    out = args.out or _default_model_path(args.model)
    if args.model == "elo":
        model = EloModel(k=args.k, home_advantage=args.home_adv).train(games)
        model.save(out)
        print(f"Trained Elo on {len(games)} games, {len(model.ratings)} teams. "
              f"Saved to {out}\n")
        rows = [[team, f"{rating:.0f}"]
                for team, rating in sorted(model.ratings.items(),
                                           key=lambda kv: kv[1], reverse=True)]
        _print_table(["Team", "Rating"], rows)
    else:
        model = TeamModel().train(games)
        model.save(out)
        print(f"Trained team scoring model on {len(games)} games, "
              f"{len(model.sports)} sport(s). Saved to {out}\n")
        rows = [[sport, f"{s.home_adv:+.1f}", f"{s.sigma_margin:.1f}",
                 f"{s.sigma_total:.1f}", str(len(s.pts_for))]
                for sport, s in sorted(model.sports.items())]
        _print_table(["Sport", "HomeAdv", "SigMargin", "SigTotal", "Teams"], rows)
    return 0


# -- sports ---------------------------------------------------------------
def _add_sports_parser(sub) -> None:
    p = sub.add_parser("sports", help="list in-season sports from The Odds API "
                                      "(requires ODDS_API_KEY)")
    p.add_argument("--all", action="store_true",
                   help="include out-of-season sports too")
    p.add_argument("--counts", action="store_true",
                   help="also show upcoming event counts (one free request per "
                        "sport; no quota cost)")
    p.set_defaults(func=_run_sports)


def _run_sports(args) -> int:
    try:
        provider = TheOddsApiProvider()
        sports = provider.get_sports(all_sports=args.all)
    except Exception as exc:  # missing key / network / API errors
        print(f"Failed to fetch sports: {exc}", file=sys.stderr)
        return 1

    if not sports:
        print("No sports returned.")
        return 0

    sports = sorted(sports, key=lambda s: (s.get("group", ""), s.get("title", "")))

    counts: dict[str, Optional[int]] = {}
    if args.counts:
        for s in sports:
            try:
                counts[s["key"]] = len(provider.get_events(s["key"]))
            except Exception:  # don't fail the whole listing on one sport
                counts[s["key"]] = None

    scope = "all" if args.all else "in-season"
    print(f"{len(sports)} {scope} sport(s):\n")
    header = ["Key", "Group", "Title", "Active"]
    if args.counts:
        header.append("Events")
    rows = []
    for s in sports:
        row = [s.get("key", ""), s.get("group", ""), s.get("title", ""),
               "yes" if s.get("active") else "no"]
        if args.counts:
            c = counts.get(s.get("key", ""))
            row.append("?" if c is None else str(c))
        rows.append(row)
    _print_table(header, rows)
    return 0


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
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # Downstream closed the pipe early (e.g. `| head`); exit quietly.
        sys.exit(0)
