"""
Constants and classification helpers used across the library.

These sets exist to classify "activities" returned by index_lite.json into
stable buckets without hardcoding every boss name.
"""

DEFAULT_HISCORES_BASE_URL = "https://secure.runescape.com/m=hiscore_oldschool"
DEFAULT_ITEMS_BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"
DEFAULT_TIMEOUT = 10

# Stable non-boss activities in the hiscores JSON.
# These are not meant to be fallback order lists—only classification hints.
NON_BOSS_ACTIVITY_KEYS = {
    "grid_points",
    "league_points",
    "deadman_points",
    "seasonal_points",
    "tournament_points",
    "collection_log",
    "collections_logged",
    "colosseum_glory",
}

# PvP-related activities in the hiscores JSON.
PVP_ACTIVITY_KEYS = {
    "bounty_hunter_hunter",
    "bounty_hunter_rogue",
    "bounty_hunter_legacy_hunter",
    "bounty_hunter_legacy_rogue",
    "last_man_standing",
    "lms_rank",
    "pvp_arena_rank",
    "pvp_arena",
    "soul_wars_zeal",
    "rifts_closed",
}
