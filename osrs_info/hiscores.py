"""
Hiscores parsing and access model.

The official OSRS hiscores JSON endpoint returns:
- `skills`: a list of skill rows in a stable order
- `activities`: a mixed list of clues, PvP activities, bosses, and other items

This module fetches the JSON, normalizes names, and splits output into
explicit buckets with stable iteration order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from .client import HiscoresClient
from .constants import NON_BOSS_ACTIVITY_KEYS, PVP_ACTIVITY_KEYS


def normalize_name(name: str) -> str:
    """
    Convert API display names into stable snake_case keys.

    Parameters
    ----------
    name:
        Name as provided by the hiscores API.

    Returns
    -------
    str
        A normalized key suitable for dictionary lookups.
    """
    s = name.strip().lower()
    s = s.replace("'", "")
    for ch in ("-", ":", "(", ")", ","):
        s = s.replace(ch, " ")
    return "_".join(s.split())


@dataclass(slots=True)
class Hiscores:
    """
    Parsed hiscores for a single player.

    Parameters
    ----------
    username:
        RuneScape display name.
    client:
        Low-level HTTP client used to fetch hiscores JSON.

    Notes
    -----
    Call `fetch()` to retrieve raw JSON and `parse()` to populate buckets.
    High-level users can instead use `HiscoresAPI.get()`.
    """

    username: str
    client: HiscoresClient = field(default_factory=HiscoresClient)

    raw_json: dict[str, Any] | None = None
    fetched: bool = False
    parsed: bool = False

    # Orders preserve the API order for stable iteration.
    skill_order: list[str] = field(default_factory=list)
    clue_order: list[str] = field(default_factory=list)
    pvp_order: list[str] = field(default_factory=list)
    activity_order: list[str] = field(default_factory=list)
    boss_order: list[str] = field(default_factory=list)

    # Parsed data buckets.
    skills: dict[str, dict[str, Any]] = field(default_factory=dict)
    clues: dict[str, dict[str, Any]] = field(default_factory=dict)
    pvp: dict[str, dict[str, Any]] = field(default_factory=dict)
    activities: dict[str, dict[str, Any]] = field(default_factory=dict)
    bosses: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ---------------------------
    # Fetch / parse
    # ---------------------------
    def fetch(self, **modes: Any) -> "Hiscores":
        """
        Fetch raw JSON from the hiscores endpoint.

        Parameters
        ----------
        **modes:
            Mode flags (ironman, hardcore, etc.) forwarded to HiscoresClient.

        Returns
        -------
        Hiscores
            Self, to allow chaining.

        Raises
        ------
        FetchError
            If the hiscores endpoint cannot be fetched.
        """
        self.raw_json = self.client.fetch_index_lite_json(self.username, **modes)
        self.fetched = True
        self.parsed = False
        return self

    def parse(self) -> "Hiscores":
        """
        Parse `raw_json` into structured buckets.

        Returns
        -------
        Hiscores
            Self, to allow chaining.

        Raises
        ------
        ValueError
            If called before fetch() or raw_json is empty.
        """
        if not self.raw_json:
            raise ValueError("No raw JSON to parse. Call fetch() first.")

        self._parse_skills(self.raw_json.get("skills", []))
        self._parse_activities(self.raw_json.get("activities", []))

        self.parsed = True
        return self

    def _parse_skills(self, skills: list[dict[str, Any]]) -> None:
        """Internal: parse the skills list into a dict, preserving order."""
        self.skills.clear()
        self.skill_order = []

        for row in skills:
            key = normalize_name(row["name"])
            self.skill_order.append(key)
            self.skills[key] = {
                "id": row.get("id"),
                "name": row.get("name"),
                "rank": row.get("rank"),
                "level": row.get("level"),
                "xp": row.get("xp"),
            }

    def _parse_activities(self, acts: list[dict[str, Any]]) -> None:
        """
        Internal: split activities into clues, PvP, misc activities, and bosses.
        """
        self.clues.clear()
        self.pvp.clear()
        self.activities.clear()
        self.bosses.clear()

        self.clue_order = []
        self.pvp_order = []
        self.activity_order = []
        self.boss_order = []

        for row in acts:
            key = normalize_name(row["name"])
            data = {
                "id": row.get("id"),
                "name": row.get("name"),
                "rank": row.get("rank"),
                "score": row.get("score"),
            }

            if key.startswith("clue_scrolls_"):
                self.clue_order.append(key)
                self.clues[key] = data
            elif key in PVP_ACTIVITY_KEYS:
                self.pvp_order.append(key)
                self.pvp[key] = data
            elif (
                key in NON_BOSS_ACTIVITY_KEYS
                or key.endswith("_points")
                or key.endswith("_rank")
            ):
                self.activity_order.append(key)
                self.activities[key] = data
            else:
                self.boss_order.append(key)
                self.bosses[key] = data

    # ---------------------------
    # Generic access helpers
    # ---------------------------
    def _get_bucket(
        self,
        bucket: dict[str, dict[str, Any]],
        key: str,
        field: str | None,
        default: Any,
    ) -> Any:
        """
        Internal helper for retrieving values from a bucket.

        Parameters
        ----------
        bucket:
            The dict to read from.
        key:
            User-provided key or display name.
        field:
            Optional field within the entry.
        default:
            Value to return if the key/field doesn't exist.

        Returns
        -------
        Any
            The full entry dict or a single field.

        Raises
        ------
        KeyError
            If key is unknown and default is None.
        """
        k = normalize_name(key)
        if k not in bucket:
            if default is not None:
                return default
            raise KeyError(f"Unknown key '{key}'")
        entry = bucket[k]
        return entry if field is None else entry.get(field, default)

    # Skills
    def skill(self, key: str, field: str | None = None, default: Any = None) -> Any:
        """
        Retrieve a skill entry or field.

        Examples
        --------
        hs.skill("attack")["xp"]
        hs.skill("attack", "level")
        """
        return self._get_bucket(self.skills, key, field, default)

    def skills_iter(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Iterate over skills in API order."""
        for k in self.skill_order:
            yield k, self.skills[k]

    # Clues
    def clue(self, key: str, field: str | None = None, default: Any = None) -> Any:
        """Retrieve a clue scroll entry or field."""
        return self._get_bucket(self.clues, key, field, default)

    def clues_iter(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Iterate over clue scrolls in API order."""
        for k in self.clue_order:
            yield k, self.clues[k]

    # PvP
    def pvp_activity(
        self, key: str, field: str | None = None, default: Any = None
    ) -> Any:
        """Retrieve a PvP activity entry or field."""
        return self._get_bucket(self.pvp, key, field, default)

    def pvp_iter(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Iterate over PvP activities in API order."""
        for k in self.pvp_order:
            yield k, self.pvp[k]

    # Misc activities
    def activity(self, key: str, field: str | None = None, default: Any = None) -> Any:
        """Retrieve a non-boss activity entry or field."""
        return self._get_bucket(self.activities, key, field, default)

    def activities_iter(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Iterate over misc activities in API order."""
        for k in self.activity_order:
            yield k, self.activities[k]

    # Bosses
    def boss(self, key: str, field: str | None = None, default: Any = None) -> Any:
        """Retrieve a boss entry or field."""
        return self._get_bucket(self.bosses, key, field, default)

    def bosses_iter(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Iterate over bosses in API order."""
        for k in self.boss_order:
            yield k, self.bosses[k]

    # ---------------------------
    # Back-compat sugar
    # ---------------------------
    def clue_score(self, key: str, default: Any = None) -> Any:
        """Back-compat convenience for clue(key, 'score')."""
        return self.clue(key, "score", default)

    def pvp_score(self, key: str, default: Any = None) -> Any:
        """Back-compat convenience for pvp_activity(key, 'score')."""
        return self.pvp_activity(key, "score", default)

    def activity_score(self, key: str, default: Any = None) -> Any:
        """Back-compat convenience for activity(key, 'score')."""
        return self.activity(key, "score", default)

    def boss_score(self, key: str, default: Any = None) -> Any:
        """Back-compat convenience for boss(key, 'score')."""
        return self.boss(key, "score", default)
