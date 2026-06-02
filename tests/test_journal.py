import pytest

from edge.journal import Journal


@pytest.fixture
def journal(tmp_path):
    return Journal(tmp_path / "journal.csv")


def _add(journal, price=135, stake=50.0):
    return journal.add(
        event="Bills @ Chiefs", market="h2h", selection="Buffalo Bills",
        book="Caesars", price=price, stake=stake,
    )


def test_add_and_list(journal):
    bet = _add(journal)
    assert bet.id == "1"
    assert bet.status == "pending"
    assert journal.list()[0].selection == "Buffalo Bills"


def test_settle_win_profit(journal):
    bet = _add(journal, price=135, stake=50)
    settled = journal.settle(bet.id, "win")
    # +135 on 50 -> 50 * 1.35 profit
    assert settled.profit == pytest.approx(67.5)


def test_settle_loss_profit(journal):
    bet = _add(journal, stake=50)
    assert journal.settle(bet.id, "loss").profit == pytest.approx(-50.0)


def test_close_records_clv(journal):
    bet = _add(journal, price=135)
    closed = journal.close(bet.id, 120)  # closed shorter -> positive CLV
    assert closed.closing_price == 120
    assert closed.clv is not None and closed.clv > 0


def test_clv_none_before_close(journal):
    assert _add(journal).clv is None


def test_summary_includes_clv(journal):
    b1 = _add(journal, price=135)
    b2 = _add(journal, price=110)
    journal.settle(b1.id, "win")
    journal.settle(b2.id, "loss")
    journal.close(b1.id, 120)   # beat the close
    journal.close(b2.id, 130)   # did not beat the close
    s = journal.summary()
    assert s["with_closing"] == 2
    assert s["beat_close_rate"] == pytest.approx(0.5)
    assert s["roi"] != 0.0


def test_persistence_roundtrip_with_close(journal):
    bet = _add(journal)
    journal.close(bet.id, 120)
    journal.settle(bet.id, "win")
    # Re-read from disk via a fresh Journal instance.
    reloaded = Journal(journal.path).list()[0]
    assert reloaded.closing_price == 120
    assert reloaded.status == "win"
    assert reloaded.clv > 0


def test_unknown_id_raises(journal):
    with pytest.raises(KeyError):
        journal.close("999", 120)
