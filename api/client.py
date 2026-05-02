"""HTTP client functions and a small threading helper.

Each fetch_* function returns (data, error) where error is None on success.
Cache keys are scoped per-request so re-clicking is instant within the TTL.
"""
import threading
import requests

from config import (
    BASE_URL,
    get_headers,
    CACHE_TTL_LIVE,
    CACHE_TTL_DATE,
    CACHE_TTL_DETAILS,
)
from .cache import cache


def _api_get(endpoint, params, cache_key=None, ttl=CACHE_TTL_DETAILS):
    if cache_key:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached, None

    try:
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=get_headers(),
            params=params,
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            if cache_key:
                cache.set(cache_key, data, ttl)
            return data, None
        return None, f"HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {e.__class__.__name__}"


def fetch_live_matches():
    return _api_get(
        "/matches/v2/list-live",
        {"Category": "soccer", "Timezone": "0"},
        cache_key="live",
        ttl=CACHE_TTL_LIVE,
    )


def fetch_matches_by_date(date_yyyymmdd):
    return _api_get(
        "/matches/v2/list-by-date",
        {"Category": "soccer", "Date": date_yyyymmdd, "Timezone": "0"},
        cache_key=f"date:{date_yyyymmdd}",
        ttl=CACHE_TTL_DATE,
    )


def fetch_statistics(eid):
    return _api_get(
        "/matches/v2/get-statistics",
        {"Eid": eid, "Category": "soccer"},
        cache_key=f"stats:{eid}",
        ttl=CACHE_TTL_DETAILS,
    )


def fetch_lineups(eid):
    return _api_get(
        "/matches/v2/get-lineups",
        {"Category": "soccer", "Eid": eid},
        cache_key=f"lineups:{eid}",
        ttl=CACHE_TTL_DETAILS,
    )


def run_async(root, worker, on_done):
    """Run worker() in a thread; deliver result to on_done() on the Tk main thread."""
    def thread_target():
        try:
            result = worker()
        except Exception as e:
            result = (None, f"Unexpected error: {e}")
        root.after(0, lambda: on_done(result))

    threading.Thread(target=thread_target, daemon=True).start()
