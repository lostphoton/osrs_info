"""
Custom exceptions for osrs_info.

Keeping a small exception surface makes the library predictable for users.
"""

from __future__ import annotations


class FetchError(RuntimeError):
    """
    Raised when a remote endpoint could not be fetched or parsed.

    Examples include networking issues, non-200 responses, or invalid JSON.
    """
