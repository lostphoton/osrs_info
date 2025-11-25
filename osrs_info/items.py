"""
OSRS item mapping and price client.

Uses the OSRS Wiki prices API:
- /mapping provides item metadata (cached after first call)
- /latest provides realtime high/low price snapshots

This client supports:
- exact lookup (by id or exact name)
- substring search
- fuzzy search via RapidFuzz (optional dependency)

Tradeable-only policy
---------------------
This library is price-focused, so we only surface items that have
actual GE price data. We treat `/latest` as the source of truth:
if an item id is not present in `/latest["data"]`, it is excluded
from search results and from lookup().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests

from .constants import DEFAULT_ITEMS_BASE_URL, DEFAULT_TIMEOUT
from .exceptions import FetchError


@dataclass(slots=True)
class ItemsClient:
    """
    Client for OSRS item mapping and prices via the Wiki prices API.

    Parameters
    ----------
    base_url:
        Root URL for the Wiki prices API.
    timeout:
        Requests timeout in seconds.
    user_agent:
        User-Agent header sent to the Wiki API.

    Notes
    -----
    - Mapping results are cached after the first request.
      Use `mapping(refresh=True)` to force a reload.
    - Tradeable filtering is done by checking membership in `/latest`.
    - Fuzzy search requires the `rapidfuzz` package:
          pip install rapidfuzz
    """

    base_url: str = DEFAULT_ITEMS_BASE_URL
    timeout: int = DEFAULT_TIMEOUT
    user_agent: str = "osrs_info"

    _mapping_cache: list[dict[str, Any]] | None = field(
        default=None, init=False, repr=False
    )
    _names_cache: list[str] | None = field(default=None, init=False, repr=False)

    # Cache of `/latest["data"]` dict (keys are item ids as strings).
    _latest_cache: dict[str, Any] | None = field(
        default=None, init=False, repr=False
    )

    # Optional alias map for OSRS slang/short-hands.
    aliases: dict[str, str] = field(default_factory=dict)

    # ---------------------------
    # Internal HTTP
    # ---------------------------
    def _get(self, path: str) -> Any:
        """Internal GET helper."""
        url = f"{self.base_url}{path}"
        try:
            r = requests.get(
                url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise FetchError(f"Failed to fetch '{url}': {e}") from e

    # ---------------------------
    # Mapping / latest indexing
    # ---------------------------
    def mapping(self, refresh: bool = False) -> list[dict[str, Any]]:
        """
        Return the full item mapping list (unfiltered).

        Parameters
        ----------
        refresh:
            If True, re-download mapping even if cached.
        """
        if self._mapping_cache is None or refresh:
            self._mapping_cache = self._get("/mapping")
            self._names_cache = [str(it.get("name", "")) for it in self._mapping_cache]
        return list(self._mapping_cache)

    def latest_index(self, refresh: bool = False) -> dict[str, Any]:
        """
        Return cached `/latest["data"]`.

        Parameters
        ----------
        refresh:
            If True, re-download latest even if cached.

        Returns
        -------
        dict[str, Any]
            Mapping of item_id (as string) -> {"high":..., "low":...}
        """
        if self._latest_cache is None or refresh:
            data = self._get("/latest")
            self._latest_cache = data.get("data", {}) or {}
        return dict(self._latest_cache)

    def tradeable_mapping(self, refresh: bool = False) -> list[dict[str, Any]]:
        """
        Return only items that have GE price data.

        Parameters
        ----------
        refresh:
            If True, refresh mapping and latest caches first.
        """
        items = self.mapping(refresh=refresh)
        latest = self.latest_index(refresh=refresh)
        latest_ids = set(latest.keys())

        tradeable = [it for it in items if str(it.get("id")) in latest_ids]
        return tradeable

    def _names_tradeable(self, refresh: bool = False) -> list[str]:
        """Internal: names aligned to tradeable_mapping()."""
        items = self.tradeable_mapping(refresh=refresh)
        return [str(it.get("name", "")) for it in items]

    def _apply_alias(self, query: str) -> str:
        """Internal: apply alias normalization if an alias exists."""
        q = query.strip().lower()
        return self.aliases.get(q, query)

    # ---------------------------
    # Lookup / search
    # ---------------------------
    def lookup(self, item: int | str) -> dict[str, Any]:
        """
        Lookup a single tradeable item by id (int) or exact name (str).

        Raises
        ------
        KeyError
            If item is unknown OR is not tradeable (no GE price).
        """
        items = self.tradeable_mapping()

        if isinstance(item, int):
            item_id_str = str(item)
            if item_id_str not in self.latest_index():
                raise KeyError(f"Item id {item} is not tradeable or has no GE price.")
            for it in items:
                if it.get("id") == item:
                    return it
            raise KeyError(f"Unknown item id {item}")

        query = self._apply_alias(item).strip().lower()
        for it in items:
            if str(it.get("name", "")).lower() == query:
                return it
        raise KeyError(f"Unknown or untradeable item name '{item}'")

    def search(
        self,
        query: str,
        limit: int | None = None,
        *,
        fuzzy: bool = False,
        score_cutoff: int = 60,
    ) -> list[dict[str, Any]]:
        """
        Search tradeable items by name.

        Behavior
        --------
        1) Fast substring search over tradeable items.
        2) If `fuzzy=True` and substring search returns no hits,
           fall back to RapidFuzz fuzzy matching (still tradeable-only).
        """
        query = self._apply_alias(query)
        q = query.strip().lower()

        items = self.tradeable_mapping()

        hits = [it for it in items if q in str(it.get("name", "")).lower()]
        hits.sort(key=lambda it: str(it.get("name", "")).lower())

        if hits or not fuzzy:
            return hits[:limit] if limit else hits

        return self.fuzzy_search(
            query, limit=limit or 10, score_cutoff=score_cutoff
        )

    def fuzzy_search(
        self,
        query: str,
        *,
        limit: int = 10,
        score_cutoff: int = 60,
        scorer: str = "WRatio",
    ) -> list[dict[str, Any]]:
        """
        Fuzzy search tradeable items using RapidFuzz.

        Raises
        ------
        ImportError
            If rapidfuzz is not installed.
        """
        query = self._apply_alias(query)

        try:
            from rapidfuzz import process, fuzz  # type: ignore
        except Exception as e:
            raise ImportError(
                "Fuzzy search requires `rapidfuzz`. Install with: pip install rapidfuzz"
            ) from e

        items = self.tradeable_mapping()
        names = [str(it.get("name", "")) for it in items]

        scorer_fn = getattr(fuzz, scorer, fuzz.WRatio)

        matches = process.extract(
            query,
            names,
            scorer=scorer_fn,
            limit=limit,
            score_cutoff=score_cutoff,
        )
        return [items[idx] for _, _, idx in matches]

    # ---------------------------
    # Pricing
    # ---------------------------
    def latest(self, item_id: int) -> dict[str, Any]:
        """
        Return latest high/low for a single tradeable item id.
        """
        latest = self.latest_index()
        data = latest.get(str(item_id))
        if data is None:
            raise KeyError(f"No latest price for id {item_id} (not tradeable?)")
        return data

    def price(self, item_id: int) -> dict[str, Any]:
        """
        Convenience bundle: mapping metadata + latest price.
        """
        meta = self.lookup(item_id)   # enforces tradeable-only
        price = self.latest(item_id)
        return {"meta": meta, "price": price}
