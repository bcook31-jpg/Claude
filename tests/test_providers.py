import pytest

from edge.providers import MockProvider, TheOddsApiProvider


def test_mock_provider_filters_by_sport():
    events = MockProvider().get_odds(sport_keys=["americanfootball_nfl"])
    assert events
    assert all(e.sport_key == "americanfootball_nfl" for e in events)


def test_mock_provider_filters_by_market():
    events = MockProvider().get_odds(markets=["h2h"])
    for e in events:
        for bm in e.bookmakers:
            assert all(m.key == "h2h" for m in bm.markets)


def test_the_odds_api_requires_key(monkeypatch):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    with pytest.raises(ValueError):
        TheOddsApiProvider()


def test_records_quota_headers():
    provider = TheOddsApiProvider(api_key="x")
    provider._record_quota({
        "x-requests-remaining": "487",
        "x-requests-used": "13",
        "x-requests-last": "3",
    })
    assert provider.requests_remaining == 487
    assert provider.requests_used == 13
    assert provider.last_cost == 3


def test_quota_headers_default_to_none_when_absent():
    provider = TheOddsApiProvider(api_key="x")
    provider._record_quota({})
    assert provider.requests_remaining is None
    assert provider.last_cost is None
