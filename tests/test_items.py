"""
Unit tests for ItemsClient tradeable-only behavior.

Key points:
- mapping() returns raw mapping (unfiltered)
- tradeable_mapping() filters by /latest
- lookup/search only operate on tradeable items
- latest()/price() read from /latest
"""

from osrs_info.items import ItemsClient
import osrs_info.items as items_mod


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


def _patch_items_endpoints(monkeypatch, *, mapping_payload, latest_payload):
    """
    Helper to patch requests.get for both /mapping and /latest endpoints.
    """
    def fake_get(url, headers=None, timeout=None):
        if url.endswith("/mapping"):
            return FakeResponse(mapping_payload)
        if url.endswith("/latest"):
            return FakeResponse(latest_payload)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(items_mod.requests, "get", fake_get)


def test_items_mapping_and_lookup(monkeypatch):
    client = ItemsClient()

    fake_mapping = [
        {"id": 4151, "name": "Abyssal whip", "examine": "A weapon from the abyss."},
        {"id": 11840, "name": "Dragon boots", "examine": "Boots of fire."},
        {"id": 13239, "name": "Abyssal bludgeon", "examine": "A crushing weapon."},
    ]
    fake_latest = {
        "data": {
            "4151": {"high": 1, "low": 1},
            "11840": {"high": 1, "low": 1},
            "13239": {"high": 1, "low": 1},
        }
    }

    _patch_items_endpoints(
        monkeypatch,
        mapping_payload=fake_mapping,
        latest_payload=fake_latest,
    )

    # Raw mapping still returns everything
    mapping = client.mapping(refresh=True)
    assert len(mapping) == 3

    # Tradeable mapping filters via /latest (here all 3 are tradeable)
    tradeable = client.tradeable_mapping(refresh=True)
    assert len(tradeable) == 3

    whip = client.lookup(4151)
    assert whip["name"] == "Abyssal whip"


def test_items_search_tradeable_only(monkeypatch):
    client = ItemsClient()

    fake_mapping = [
        {"id": 4151, "name": "Abyssal whip"},
        {"id": 13239, "name": "Abyssal bludgeon"},
        {"id": 11840, "name": "Dragon boots"},
        # Untradeable/price-less item that should be filtered out
        {"id": 99999, "name": "Abyssal demo item"},
    ]
    fake_latest = {
        "data": {
            "4151": {"high": 1, "low": 1},
            "13239": {"high": 1, "low": 1},
            "11840": {"high": 1, "low": 1},
            # Note: 99999 intentionally missing → not tradeable
        }
    }

    _patch_items_endpoints(
        monkeypatch,
        mapping_payload=fake_mapping,
        latest_payload=fake_latest,
    )

    hits = client.search("abyssal")
    # Sorted by name, and untradeable filtered out
    assert [h["id"] for h in hits] == [13239, 4151]


def test_items_latest_and_price(monkeypatch):
    client = ItemsClient()

    fake_mapping = [{"id": 4151, "name": "Abyssal whip"}]
    fake_latest = {"data": {"4151": {"high": 2300000, "low": 2200000}}}

    _patch_items_endpoints(
        monkeypatch,
        mapping_payload=fake_mapping,
        latest_payload=fake_latest,
    )

    latest_whip = client.latest(4151)
    assert latest_whip["high"] == 2300000

    bundle = client.price(4151)
    assert bundle["meta"]["name"] == "Abyssal whip"
    assert bundle["price"]["low"] == 2200000
