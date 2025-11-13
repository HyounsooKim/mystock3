"""Unit tests for stock cache service."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest

from src.models.stock import StockQuote
from src.services.stock_cache_service import StockCacheService, get_cache


@pytest.fixture
def cache():
    """Create fresh cache instance for each test."""
    return StockCacheService()


@pytest.fixture
def sample_quote():
    """Create sample stock quote."""
    return StockQuote(
        symbol="AAPL",
        company_name="Apple Inc.",
        current_price=Decimal("178.32"),
        change=Decimal("2.15"),
        change_percent=Decimal("1.22"),
        open=Decimal("176.50"),
        high=Decimal("179.00"),
        low=Decimal("176.20"),
        volume=58392010,
        last_updated=datetime.now(timezone.utc),
        currency="USD"
    )


class TestStockCacheService:
    """Test suite for StockCacheService."""
    
    def test_cache_miss(self, cache):
        """Test cache miss for non-existent symbol."""
        result = cache.get("AAPL")
        assert result is None
    
    def test_cache_hit(self, cache, sample_quote):
        """Test cache hit for stored symbol."""
        cache.set("AAPL", sample_quote)
        
        result = cache.get("AAPL")
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.current_price == Decimal("178.32")
    
    def test_cache_case_insensitive(self, cache, sample_quote):
        """Test cache is case-insensitive."""
        cache.set("aapl", sample_quote)
        
        # Should find using uppercase
        result = cache.get("AAPL")
        assert result is not None
        assert result.symbol == "AAPL"
    
    def test_cache_expiration_after_ttl(self, cache, sample_quote):
        """Test cache entry expires after TTL (1 minute)."""
        # Set cache entry
        cache.set("AAPL", sample_quote)
        
        # Mock time to be 61 seconds later (past TTL)
        future_time = datetime.now(timezone.utc) + timedelta(seconds=61)
        
        with patch('src.services.stock_cache_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            # Should return None (expired)
            result = cache.get("AAPL")
            assert result is None
            
            # Entry should be removed from cache
            assert "AAPL" not in cache._cache
    
    def test_cache_valid_within_ttl(self, cache, sample_quote):
        """Test cache entry valid within TTL."""
        cache.set("AAPL", sample_quote)
        
        # Mock time to be 30 seconds later (within TTL)
        future_time = datetime.now(timezone.utc) + timedelta(seconds=30)
        
        with patch('src.services.stock_cache_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            # Should return cached quote
            result = cache.get("AAPL")
            assert result is not None
            assert result.symbol == "AAPL"
    
    def test_invalidate_existing(self, cache, sample_quote):
        """Test invalidating existing cache entry."""
        cache.set("AAPL", sample_quote)
        
        removed = cache.invalidate("AAPL")
        assert removed is True
        
        # Should be removed
        result = cache.get("AAPL")
        assert result is None
    
    def test_invalidate_nonexistent(self, cache):
        """Test invalidating non-existent cache entry."""
        removed = cache.invalidate("AAPL")
        assert removed is False
    
    def test_clear_cache(self, cache, sample_quote):
        """Test clearing all cache entries."""
        cache.set("AAPL", sample_quote)
        cache.set("TSLA", sample_quote)
        cache.set("MSFT", sample_quote)
        
        cache.clear()
        
        # All entries should be removed
        assert cache.get("AAPL") is None
        assert cache.get("TSLA") is None
        assert cache.get("MSFT") is None
    
    def test_get_stats_empty(self, cache):
        """Test stats for empty cache."""
        stats = cache.get_stats()
        
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["ttl_seconds"] == 60
    
    def test_get_stats_with_entries(self, cache, sample_quote):
        """Test stats with active and expired entries."""
        # Add entries at different times
        cache.set("AAPL", sample_quote)
        cache.set("TSLA", sample_quote)
        
        # Mock time to be 70 seconds later (AAPL expired)
        future_time = datetime.now(timezone.utc) + timedelta(seconds=70)
        
        with patch('src.services.stock_cache_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            stats = cache.get_stats()
            
            assert stats["total_entries"] == 2
            assert stats["expired_entries"] == 2  # Both expired
    
    def test_get_cache_singleton(self):
        """Test get_cache returns singleton instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        
        assert cache1 is cache2
    
    def test_multiple_updates(self, cache):
        """Test updating cache with new quote."""
        quote1 = StockQuote(
            symbol="AAPL",
            company_name="Apple Inc.",
            current_price=Decimal("178.32"),
            change=Decimal("2.15"),
            change_percent=Decimal("1.22"),
            open=Decimal("176.50"),
            high=Decimal("179.00"),
            low=Decimal("176.20"),
            volume=58392010,
            last_updated=datetime.now(timezone.utc),
            currency="USD"
        )
        
        quote2 = StockQuote(
            symbol="AAPL",
            company_name="Apple Inc.",
            current_price=Decimal("180.50"),  # Updated price
            change=Decimal("4.33"),
            change_percent=Decimal("2.46"),
            open=Decimal("176.50"),
            high=Decimal("181.00"),
            low=Decimal("176.20"),
            volume=60000000,
            last_updated=datetime.now(timezone.utc),
            currency="USD"
        )
        
        # Set initial quote
        cache.set("AAPL", quote1)
        result1 = cache.get("AAPL")
        assert result1.current_price == Decimal("178.32")
        
        # Update with new quote
        cache.set("AAPL", quote2)
        result2 = cache.get("AAPL")
        assert result2.current_price == Decimal("180.50")
        assert result2.volume == 60000000
