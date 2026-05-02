"""API package — handles network calls, caching, and async dispatch."""

from .cache import cache
from .client import (
    fetch_live_matches,
    fetch_matches_by_date,
    fetch_statistics,
    fetch_lineups,
    run_async,
)

__all__ = [
    "cache",
    "fetch_live_matches",
    "fetch_matches_by_date",
    "fetch_statistics",
    "fetch_lineups",
    "run_async",
]
