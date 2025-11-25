"""
High-level HiscoresAPI wrapper.

This provides a "single call" interface for most consumers so they don’t
need to manually instantiate Hiscores and call fetch/parse themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .client import HiscoresClient
from .hiscores import Hiscores


@dataclass(slots=True)
class HiscoresAPI:
    """
    Convenience wrapper around `Hiscores`.

    Parameters
    ----------
    client:
        Shared HiscoresClient instance. Allows connection reuse in larger apps.
    """

    client: HiscoresClient

    def get(
        self,
        username: str,
        *,
        fetch: bool = True,
        parse: bool = True,
        **modes: Any,
    ) -> Hiscores:
        """
        Create a Hiscores object and optionally fetch/parse it.

        Parameters
        ----------
        username:
            RuneScape display name.
        fetch:
            If True, call hs.fetch(**modes).
        parse:
            If True, call hs.parse().
        **modes:
            Mode flags (ironman, hardcore, etc.).

        Returns
        -------
        Hiscores
            The resulting Hiscores instance.
        """
        hs = Hiscores(username=username, client=self.client)
        if fetch:
            hs.fetch(**modes)
        if parse:
            hs.parse()
        return hs
