"""
Low-level HTTP client for the official OSRS hiscores JSON endpoint.

This file intentionally stays tiny: build URL → fetch JSON → raise a clean error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .constants import DEFAULT_HISCORES_BASE_URL, DEFAULT_TIMEOUT
from .exceptions import FetchError


@dataclass(slots=True)
class HiscoresClient:
    """
    Tiny HTTP client for the official OSRS JSON hiscores API.

    Parameters
    ----------
    base_url:
        Root URL for hiscores. Defaults to Old School RuneScape hiscores.
    timeout:
        Requests timeout in seconds.

    Notes
    -----
    The OSRS hiscores endpoint uses different URL suffixes for modes.
    If multiple modes are passed, the most specific mode wins.

    Precedence (highest → lowest):
        seasonal > deadman > ultimate > hardcore_ironman > ironman > normal
    """

    base_url: str = DEFAULT_HISCORES_BASE_URL
    timeout: int = DEFAULT_TIMEOUT

    def _mode_suffix(
        self,
        *,
        ironman: bool = False,
        hardcore: bool = False,
        ultimate: bool = False,
        deadman: bool = False,
        seasonal: bool = False,
    ) -> str:
        """
        Convert mode flags into the hiscores endpoint suffix.

        Returns
        -------
        str
            URL suffix such as "_ironman" or "_hardcore_ironman".
        """
        if seasonal:
            return "_seasonal"
        if deadman:
            return "_deadman"
        if ultimate:
            return "_ultimate"
        if hardcore:
            return "_hardcore_ironman"
        if ironman:
            return "_ironman"
        return ""

    def fetch_index_lite_json(self, username: str, **modes: Any) -> dict[str, Any]:
        """
        Fetch `/index_lite.json` for a player and return parsed JSON.

        Parameters
        ----------
        username:
            RuneScape display name.
        **modes:
            Mode flags forwarded to `_mode_suffix`.

        Returns
        -------
        dict[str, Any]
            Parsed JSON response from the hiscores API.

        Raises
        ------
        FetchError
            If the request fails or returns invalid JSON.
        """
        mode = self._mode_suffix(**modes)
        url = f"{self.base_url}{mode}/index_lite.json"
        try:
            r = requests.get(url, params={"player": username}, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise FetchError(f"Failed to fetch hiscores for '{username}': {e}") from e
