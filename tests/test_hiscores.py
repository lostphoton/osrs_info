"""
Unit tests for skills parsing and ordering.

We verify:
- stable ordering matches API order
- normalized lookup works
- new skills (e.g., Sailing) are handled automatically
"""

from osrs_info.hiscores import Hiscores


def test_parse_skills_from_fixture():
    hs = Hiscores("FixtureUser")
    hs.raw_json = {
        "name": "FixtureUser",
        "skills": [
            {"id": 0, "name": "Overall", "rank": 1, "level": 2277, "xp": 999999999},
            {"id": 1, "name": "Attack", "rank": 2, "level": 99, "xp": 13034431},
            {"id": 24, "name": "Sailing", "rank": -1, "level": 1, "xp": 0},
        ],
        "activities": [],
    }
    hs.parse()

    assert hs.skill_order == ["overall", "attack", "sailing"]
    assert hs.skill("attack", "level") == 99
    assert hs.skill("attack")["xp"] == 13034431
    assert "sailing" in hs.skills
