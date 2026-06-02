"""Build a backtest dataset by joining odds snapshots to results.

The Odds API uses a consistent event ``id`` across the ``/odds``, ``/scores``
and historical-odds endpoints, so a settled-events dataset (the format
:func:`edge.backtest.run_backtest` consumes) can be assembled by joining:

* an **opening** odds snapshot  -> the odds you would have bet,
* a **closing** odds snapshot   -> for CLV (optional),
* a **scores** payload          -> the final result,

all keyed by event id. The functions here are pure (they take already-fetched
payloads) so the join logic is provider-agnostic and testable offline.
"""

from __future__ import annotations

from typing import Optional


def scores_to_results(scores_payload: list[dict]) -> dict[str, dict]:
    """Map event id -> {"home_score", "away_score"} for completed games.

    Skips games that are not completed or lack numeric scores for both teams.
    """
    results: dict[str, dict] = {}
    for game in scores_payload:
        if not game.get("completed") or not game.get("scores"):
            continue
        by_name = {s.get("name"): s.get("score") for s in game["scores"]}
        home, away = game.get("home_team"), game.get("away_team")
        home_score, away_score = by_name.get(home), by_name.get(away)
        game_id = game.get("id")
        if not game_id or home_score is None or away_score is None:
            continue
        try:
            results[game_id] = {
                "home_score": int(home_score),
                "away_score": int(away_score),
            }
        except (TypeError, ValueError):
            continue
    return results


def build_settled_events(
    opening_events: list[dict],
    scores_payload: list[dict],
    closing_events: Optional[list[dict]] = None,
) -> list[dict]:
    """Join opening odds, closing odds and results into settled events.

    ``opening_events`` and ``closing_events`` are lists of event dicts in The
    Odds API shape (e.g. the ``data`` array of a historical-odds snapshot, or a
    live ``/odds`` payload). Only events that have a matching completed result
    are kept. The output is a list of
    ``{"event", "result", "closing"?}`` dicts ready for ``run_backtest``.
    """
    results = scores_to_results(scores_payload)
    closing_by_id = {e.get("id"): e for e in (closing_events or []) if e.get("id")}

    settled = []
    for event in opening_events:
        event_id = event.get("id")
        if event_id not in results:
            continue
        item = {"event": event, "result": results[event_id]}
        closing = closing_by_id.get(event_id)
        if closing is not None:
            item["closing"] = closing
        settled.append(item)
    return settled
