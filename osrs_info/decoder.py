"""
High-level entrypoints for osrs_info.

decoder is the main object users interact with. It wires together
sub-clients for hiscores and item prices.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .client import HiscoresClient
from .hiscores_api import HiscoresAPI
from .items import ItemsClient


@dataclass(slots=True)
class Decoder:
    """
    Main library entrypoint.
    
    Attributes
    ----------
    hiscores_client:
        Low-level HTTP client for the official OSRS hiscores endpoint.
    items_client:
        Client for OSRS Wiki item mapping and prices.

    Notes
    -----
    After initialization, a high-level HiscoresAPI wrapper is available
    as `.hiscores`, and the items client is available as `.items`.
    """

    hiscores_client: HiscoresClient = field(default_factory=HiscoresClient)
    items_client: ItemsClient = field(default_factory=ItemsClient)

    hiscores: HiscoresAPI = field(init=False)

    def __post_init__(self) -> None:
        """Initialize convenience APIs that depend on sub-clients."""
        self.hiscores = HiscoresAPI(self.hiscores_client)

    @property
    def items(self) -> ItemsClient:
        """
        Access the OSRS Wiki item/price API.

        Returns
        -------
        ItemsClient
            The configured items client instance.
        """
        return self.items_client
