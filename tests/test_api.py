"""
Integration-ish unit test for the OSRS_API hiscores entrypoint.

We monkeypatch the low-level HTTP call and assert that:
- Decoder wires HiscoresAPI correctly
- HiscoresAPI.get(fetch=True, parse=True) returns a parsed Hiscores object
- Bucket classification (skills/clues/pvp/bosses) works end-to-end
"""

from osrs_info import Decoder
import osrs_info.client as client_mod


class FakeResponse:
    """Minimal requests.Response stand-in for unit tests."""
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("bad status")

    def json(self):
        return self._payload


def test_hiscores_api_fixture(monkeypatch):
    fake_json = {
        "name": "FixtureUser",
        "skills": [
            {"id": 0, "name": "Overall", "rank": 1, "level": 99, "xp": 123},
            {"id": 1, "name": "Attack", "rank": 2, "level": 99, "xp": 13034431},
        ],
        "activities": [
            {"id": 0, "name": "League Points", "rank": -1, "score": 10},
            {"id": 7, "name": "Clue Scrolls (all)", "rank": 5, "score": 42},
            {"id": 10, "name": "Bounty Hunter - Hunter", "rank": -1, "score": 3},
            {"id": 19, "name": "Collections Logged", "rank": -1, "score": 0},
            {"id": 87, "name": "Zulrah", "rank": 100, "score": 55},
        ],
    }

    def fake_get(url, params=None, timeout=None, headers=None):
        # Ensure the right endpoint and query param are used.
        assert url.endswith("/index_lite.json")
        assert params["player"] == "FixtureUser"
        return FakeResponse(fake_json)

    monkeypatch.setattr(client_mod.requests, "get", fake_get)

    api = Decoder()
    hs = api.hiscores.get("FixtureUser")  # fetch + parse by default

    assert hs.skill("attack", "level") == 99
    assert hs.clue("clue_scrolls_all", "score") == 42
    assert hs.pvp_score("bounty_hunter_hunter") == 3
    assert hs.boss("zulrah", "score") == 55
