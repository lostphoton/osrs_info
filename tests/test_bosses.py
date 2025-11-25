"""
Unit tests for boss/activity classification inside Hiscores.parse().

This does not hit the network; we inject a raw_json fixture and parse it.
"""

from osrs_info.hiscores import Hiscores


def test_parse_bosses_from_fixture():
    hs = Hiscores("FixtureUser")
    hs.raw_json = {
        "name": "FixtureUser",
        "skills": [{"id": 0, "name": "Overall", "rank": 1, "level": 100, "xp": 0}],
        "activities": [
            {"id": 7, "name": "Clue Scrolls (all)", "rank": 5, "score": 1},
            {"id": 10, "name": "Bounty Hunter - Hunter", "rank": -1, "score": 3},
            {"id": 19, "name": "Collections Logged", "rank": -1, "score": 0},
            {"id": 87, "name": "Zulrah", "rank": 100, "score": 55},
            {"id": 83, "name": "Vorkath", "rank": -1, "score": 2},
        ],
    }
    hs.parse()

    # Boss bucket
    assert hs.boss("zulrah", "score") == 55
    assert hs.boss("vorkath", "score") == 2
    assert "zulrah" in hs.bosses

    # Non-boss buckets still populated correctly
    assert "clue_scrolls_all" in hs.clues
    assert "bounty_hunter_hunter" in hs.pvp
