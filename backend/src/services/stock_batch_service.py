"""
Batch Stock Query Service

Optimizes multiple stock data fetches by:
1. Deduplicating symbols
2. Using cache for recently fetched data
3. Batching API calls with concurrent execution
4. Minimizing Alpha Vantage API calls (T171)
"""

import asyncio
from typing import Dict, List, Optional, Set
from decimal import Decimal

from ..external.alpha_vantage_client import AlphaVantageClient
from ..models.stock import StockQuote
from .stock_cache_service import get_cache
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StockBatchService:
    """Service for efficient batch stock data queries"""

    def __init__(self, alpha_vantage_client: Optional[AlphaVantageClient] = None):
        """Initialize batch service with Alpha Vantage client"""
        self.client = alpha_vantage_client
        self.cache = get_cache()

    async def get_quotes_batch(self, symbols: List[str]) -> Dict[str, Optional[StockQuote]]:
        """
        Fetch multiple stock quotes efficiently using cache and batch processing

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary mapping symbol to StockQuote (or None if fetch failed)

        Performance optimizations:
        - Deduplicates symbols
        - Checks cache first (1-minute TTL)
        - Batches uncached symbols
        - Concurrent API calls for uncached symbols
        - Handles failures gracefully (returns None for failed symbols)
        """
        if not symbols:
            return {}

        # Deduplicate and normalize symbols
        unique_symbols = list(set(sym.upper() for sym in symbols if sym))
        
        logger.info(
            f"Batch quote request: {len(symbols)} total, {len(unique_symbols)} unique symbols",
            extra={"extra_fields": {
                "total_symbols": len(symbols),
                "unique_symbols": len(unique_symbols),
                "symbols": unique_symbols
            }}
        )

        result: Dict[str, Optional[StockQuote]] = {}
        uncached_symbols: List[str] = []

        # Step 1: Check cache for each symbol
        for symbol in unique_symbols:
            cached_quote = self.cache.get(symbol)
            if cached_quote:
                result[symbol] = cached_quote
                logger.debug(f"Cache hit for {symbol}")
            else:
                uncached_symbols.append(symbol)

        cache_hit_rate = (len(result) / len(unique_symbols) * 100) if unique_symbols else 0
        logger.info(
            f"Cache check complete: {len(result)} hits, {len(uncached_symbols)} misses",
            extra={"extra_fields": {
                "cache_hits": len(result),
                "cache_misses": len(uncached_symbols),
                "hit_rate_percent": round(cache_hit_rate, 2)
            }}
        )

        # Step 2: Fetch uncached symbols concurrently
        if uncached_symbols:
            if not self.client:
                logger.error("Alpha Vantage client not initialized")
                # Fill uncached symbols with None
                for symbol in uncached_symbols:
                    result[symbol] = None
                return result

            # Create concurrent tasks for all uncached symbols
            fetch_tasks = [
                self._fetch_and_cache_quote(symbol)
                for symbol in uncached_symbols
            ]

            # Execute all tasks concurrently
            fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            # Process results
            for symbol, fetch_result in zip(uncached_symbols, fetch_results):
                if isinstance(fetch_result, Exception):
                    logger.warning(
                        f"Failed to fetch quote for {symbol}: {fetch_result}",
                        extra={"extra_fields": {
                            "symbol": symbol,
                            "error": str(fetch_result),
                            "error_type": type(fetch_result).__name__
                        }}
                    )
                    result[symbol] = None
                else:
                    result[symbol] = fetch_result

            success_count = sum(1 for v in fetch_results if not isinstance(v, Exception))
            logger.info(
                f"Batch fetch complete: {success_count}/{len(uncached_symbols)} successful",
                extra={"extra_fields": {
                    "total_fetched": len(uncached_symbols),
                    "successful": success_count,
                    "failed": len(uncached_symbols) - success_count
                }}
            )

        return result

    async def _fetch_and_cache_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Fetch single stock quote and cache result

        Args:
            symbol: Stock ticker symbol

        Returns:
            StockQuote or None if fetch failed
        """
        try:
            quote = await self.client.get_quote(symbol)
            
            # Cache successful result
            self.cache.set(symbol, quote)
            
            logger.debug(
                f"Fetched and cached quote for {symbol}",
                extra={"extra_fields": {
                    "symbol": symbol,
                    "price": float(quote.current_price)
                }}
            )
            
            return quote
            
        except Exception as e:
            logger.warning(
                f"Failed to fetch quote for {symbol}: {e}",
                extra={"extra_fields": {
                    "symbol": symbol,
                    "error": str(e),
                    "error_type": type(e).__name__
                }}
            )
            return None

    async def get_prices_batch(self, symbols: List[str]) -> Dict[str, Optional[Decimal]]:
        """
        Convenience method to get just current prices for multiple symbols

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary mapping symbol to current price (or None if unavailable)
        """
        quotes = await self.get_quotes_batch(symbols)
        
        return {
            symbol: quote.current_price if quote else None
            for symbol, quote in quotes.items()
        }

    async def warm_cache(self, symbols: List[str]) -> int:
        """
        Pre-fetch and cache stock quotes for given symbols

        Useful for warming cache before batch operations.

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Number of successfully cached quotes
        """
        logger.info(
            f"Warming cache for {len(symbols)} symbols",
            extra={"extra_fields": {"symbols": symbols}}
        )

        quotes = await self.get_quotes_batch(symbols)
        
        success_count = sum(1 for quote in quotes.values() if quote is not None)
        
        logger.info(
            f"Cache warming complete: {success_count}/{len(symbols)} successful",
            extra={"extra_fields": {
                "total_symbols": len(symbols),
                "cached": success_count,
                "failed": len(symbols) - success_count
            }}
        )

        return success_count


# Singleton instance
_batch_service_instance: Optional[StockBatchService] = None


def get_batch_service(
    alpha_vantage_client: Optional[AlphaVantageClient] = None
) -> StockBatchService:
    """
    Get global batch service instance (singleton pattern)

    Args:
        alpha_vantage_client: Optional AlphaVantageClient (only for initialization)

    Returns:
        Global StockBatchService instance
    """
    global _batch_service_instance
    if _batch_service_instance is None:
        _batch_service_instance = StockBatchService(alpha_vantage_client)
    return _batch_service_instance
