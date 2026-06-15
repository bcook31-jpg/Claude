"""Tests for positions loading, validation, and id auto-generation."""

import json

import pytest

from portfolio_monitor.positions import (OptionPosition, SharePosition,
                                         load_positions, parse_position)


def test_option_auto_id():
    pos = parse_position({
        "asset_type": "option", "ticker": "aapl", "option_type": "Call",
        "strike": 210, "expiry": "2026-09-18", "entry_price": 8.45,
        "contracts": 2, "entry_date": "2026-05-20",
    })
    assert isinstance(pos, OptionPosition)
    assert pos.id == "AAPL_C_210_2026-09-18"
    assert pos.option_type == "call"
    assert pos.contract_multiplier == 100


def test_explicit_id_preserved():
    pos = parse_position({
        "id": "MY-HEDGE", "asset_type": "option", "ticker": "MSFT",
        "option_type": "put", "strike": 400, "expiry": "2026-07-17",
        "entry_price": 12.3, "contracts": 1, "entry_date": "2026-06-01",
    })
    assert pos.id == "MY-HEDGE"


def test_shares_multiplier_is_one():
    pos = parse_position({
        "asset_type": "shares", "ticker": "NVDA", "entry_price": 118.4,
        "contracts": 50, "entry_date": "2026-03-10",
    })
    assert isinstance(pos, SharePosition)
    assert pos.contract_multiplier == 1
    assert pos.id == "NVDA_SHARES"


def test_bad_option_type_rejected():
    with pytest.raises(ValueError):
        parse_position({
            "asset_type": "option", "ticker": "AAPL", "option_type": "straddle",
            "strike": 1, "expiry": "2026-01-01", "entry_price": 1,
            "contracts": 1, "entry_date": "2026-01-01",
        })


def test_missing_required_field_reports_field():
    with pytest.raises(ValueError, match="strike"):
        parse_position({
            "asset_type": "option", "ticker": "AAPL", "option_type": "call",
            "expiry": "2026-01-01", "entry_price": 1, "contracts": 1,
            "entry_date": "2026-01-01",
        })


def test_duplicate_ids_rejected(tmp_path):
    book = tmp_path / "positions.json"
    book.write_text(json.dumps([
        {"asset_type": "shares", "ticker": "NVDA", "entry_price": 1,
         "contracts": 1, "entry_date": "2026-01-01"},
        {"asset_type": "shares", "ticker": "NVDA", "entry_price": 2,
         "contracts": 2, "entry_date": "2026-01-02"},
    ]))
    with pytest.raises(ValueError, match="duplicate id"):
        load_positions(book)


def test_load_example_book():
    positions = load_positions("positions.json")
    assert len(positions) == 3
    kinds = {p.asset_type for p in positions}
    assert kinds == {"option", "shares"}
