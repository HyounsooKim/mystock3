"""Stock data caching service with 1-minute TTL."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.models.stock import StockQuote

logger = logging.getLogger(__name__)


class StockCacheService:
    """In-memory cache for stock quotes with 1-minute TTL.
    
    This service implements a simple in-memory cache to minimize
    Alpha Vantage API calls as required by FR-028.
    
    For production, consider using Redis or Azure Cache for Redis.
    """
    
    CACHE_TTL_SECONDS = 60  # 1 minute as per FR-028
    
    def __init__(self):
        """Initialize empty cache."""
        self._cache: dict[str, tuple[StockQuote, datetime]] = {}
    
    def get(self, symbol: str) -> Optional[StockQuote]:
        """Get cached stock quote if available and not expired.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Cached StockQuote or None if not found or expired
        """
        symbol_upper = symbol.upper()
        
        if symbol_upper not in self._cache:
            logger.debug(
                "Cache miss - symbol not found",
                extra={"extra_fields": {"symbol": symbol_upper}}
            )
            return None
        
        quote, cached_at = self._cache[symbol_upper]
        now = datetime.now(timezone.utc)
        age_seconds = (now - cached_at).total_seconds()
        
        if age_seconds > self.CACHE_TTL_SECONDS:
            logger.info(
                "Cache expired",
                extra={"extra_fields": {
                    "symbol": symbol_upper,
                    "age_seconds": age_seconds,
                    "ttl": self.CACHE_TTL_SECONDS
                }}
            )
            # Remove expired entry
            del self._cache[symbol_upper]
            return None
        
        logger.info(
            "Cache hit",
            extra={"extra_fields": {
                "symbol": symbol_upper,
                "age_seconds": age_seconds,
                "remaining_seconds": self.CACHE_TTL_SECONDS - age_seconds
            }}
        )
        
        return quote
    
    def set(self, symbol: str, quote: StockQuote) -> None:
        """Store stock quote in cache with current timestamp.
        
        Args:
            symbol: Stock ticker symbol
            quote: StockQuote object to cache
        """
        symbol_upper = symbol.upper()
        now = datetime.now(timezone.utc)
        
        self._cache[symbol_upper] = (quote, now)
        
        logger.info(
            "Cached stock quote",
            extra={"extra_fields": {
                "symbol": symbol_upper,
                "cached_at": now.isoformat(),
                "ttl": self.CACHE_TTL_SECONDS
            }}
        )
    
    def invalidate(self, symbol: str) -> bool:
        """Remove stock quote from cache.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            True if entry was removed, False if not found
        """
        symbol_upper = symbol.upper()
        
        if symbol_upper in self._cache:
            del self._cache[symbol_upper]
            logger.info(
                "Cache invalidated",
                extra={"extra_fields": {"symbol": symbol_upper}}
            )
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear all cached entries."""
        count = len(self._cache)
        self._cache.clear()
        
        logger.info(
            "Cache cleared",
            extra={"extra_fields": {"entries_removed": count}}
        )
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        now = datetime.now(timezone.utc)
        active_count = 0
        expired_count = 0
        
        for symbol, (quote, cached_at) in self._cache.items():
            age_seconds = (now - cached_at).total_seconds()
            if age_seconds <= self.CACHE_TTL_SECONDS:
                active_count += 1
            else:
                expired_count += 1
        
        return {
            "total_entries": len(self._cache),
            "active_entries": active_count,
            "expired_entries": expired_count,
            "ttl_seconds": self.CACHE_TTL_SECONDS
        }


# Global singleton instance
_cache_instance: Optional[StockCacheService] = None


def get_cache() -> StockCacheService:
    """Get global cache instance (singleton pattern).
    
    Returns:
        Global StockCacheService instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = StockCacheService()
    return _cache_instance
