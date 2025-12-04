"""Simple in-memory cache for search results."""
from typing import Optional, List
from datetime import datetime, timedelta
from src.models import Track
from src.utils.logger import logger


class SimpleCache:
    """Simple in-memory cache for search results."""

    def __init__(self):
        """Initialize cache."""
        self._cache = {}

    def set(self, key: str, value: List[Track], ttl: int = 600):
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: List of tracks to cache
            ttl: Time to live in seconds (default: 10 minutes)
        """
        expire_at = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = {
            'data': value,
            'expire_at': expire_at
        }
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")

    def get(self, key: str) -> Optional[List[Track]]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached tracks or None if expired/not found
        """
        if key not in self._cache:
            logger.debug(f"Cache MISS: {key}")
            return None

        item = self._cache[key]

        # Check expiration
        if datetime.now() > item['expire_at']:
            logger.debug(f"Cache EXPIRED: {key}")
            del self._cache[key]
            return None

        logger.debug(f"Cache HIT: {key}")
        return item['data']

    def clear(self):
        """Clear entire cache."""
        self._cache.clear()
        logger.debug("Cache cleared")

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            'items': len(self._cache),
            'keys': list(self._cache.keys())
        }


# Singleton instance
cache = SimpleCache()
