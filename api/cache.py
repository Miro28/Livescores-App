"""Simple in-memory TTL cache shared across the app."""
import time


class Cache:
    def __init__(self):
        self._store = {}

    def get(self, key):
        item = self._store.get(key)
        if not item:
            return None
        value, expiry = item
        if time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key, value, ttl):
        self._store[key] = (value, time.time() + ttl)

    def invalidate(self, key):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


cache = Cache()
