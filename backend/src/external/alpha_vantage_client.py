"""Alpha Vantage API client for stock market data."""
import asyncio
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import aiohttp

from src.models.stock import StockQuote, StockSearchResult
from src.utils.telemetry import get_telemetry_client

logger = logging.getLogger(__name__)


class AlphaVantageClient:
    """Client for Alpha Vantage API with rate limiting and error handling.
    
    Features:
    - Async HTTP client using aiohttp
    - Exponential backoff retry logic (T078)
    - Stock quote retrieval
    - Stock search functionality
    - Error handling for 429 rate limits
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2.0
    
    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """Initialize Alpha Vantage client.
        
        Args:
            api_key: Alpha Vantage API key
            session: Optional aiohttp session (for testing)
        """
        self.api_key = api_key
        self._session = session
        self._own_session = session is None
        self.telemetry = get_telemetry_client()
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_session and self._session:
            await self._session.close()
    
    async def get_quote(self, symbol: str) -> StockQuote:
        """Get real-time stock quote.
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
        
        Returns:
            StockQuote object with current price data
        
        Raises:
            ValueError: If symbol not found
            RuntimeError: If API rate limit exceeded or external API error
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol.upper(),
            "apikey": self.api_key
        }
        
        data = await self._make_request(params)
        
        # Check for error responses
        if "Error Message" in data:
            logger.error(
                "Stock symbol not found",
                extra={"extra_fields": {"symbol": symbol, "error": data["Error Message"]}}
            )
            raise ValueError(f"Stock symbol not found: {symbol}")
        
        if "Note" in data:
            # API rate limit message
            logger.warning(
                "Alpha Vantage rate limit hit",
                extra={"extra_fields": {"symbol": symbol, "note": data["Note"]}}
            )
            raise RuntimeError("API rate limit exceeded, please retry later")
        
        # Parse quote data
        quote_data = data.get("Global Quote", {})
        if not quote_data:
            raise ValueError(f"No quote data available for symbol: {symbol}")
        
        try:
            return StockQuote(
                symbol=quote_data["01. symbol"],
                company_name=quote_data["01. symbol"],  # Alpha Vantage doesn't return company name in GLOBAL_QUOTE
                current_price=Decimal(quote_data["05. price"]),
                change=Decimal(quote_data["09. change"]),
                change_percent=Decimal(quote_data["10. change percent"].rstrip('%')),
                open=Decimal(quote_data["02. open"]),
                high=Decimal(quote_data["03. high"]),
                low=Decimal(quote_data["04. low"]),
                volume=int(quote_data["06. volume"]),
                last_updated=datetime.now(timezone.utc),
                currency="USD"
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to parse quote data",
                extra={"extra_fields": {"symbol": symbol, "error": str(e), "data": quote_data}}
            )
            raise ValueError(f"Invalid quote data format for {symbol}") from e
    
    async def search_symbol(self, keywords: str) -> list[StockSearchResult]:
        """Search for stock symbols by keywords.
        
        Args:
            keywords: Search query string
        
        Returns:
            List of matching stock symbols
        
        Raises:
            RuntimeError: If API rate limit exceeded or external API error
        """
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": self.api_key
        }
        
        data = await self._make_request(params)
        
        # Check for error responses
        if "Note" in data:
            logger.warning(
                "Alpha Vantage rate limit hit",
                extra={"extra_fields": {"keywords": keywords, "note": data["Note"]}}
            )
            raise RuntimeError("API rate limit exceeded, please retry later")
        
        # Parse search results
        matches = data.get("bestMatches", [])
        results = []
        
        for match in matches:
            try:
                results.append(StockSearchResult(
                    symbol=match["1. symbol"],
                    name=match["2. name"],
                    type=match["3. type"],
                    region=match["4. region"],
                    currency=match["8. currency"]
                ))
            except (KeyError, ValueError) as e:
                logger.warning(
                    "Skipping invalid search result",
                    extra={"extra_fields": {"error": str(e), "match": match}}
                )
                continue
        
        logger.info(
            "Symbol search completed",
            extra={"extra_fields": {"keywords": keywords, "results_count": len(results)}}
        )
        
        return results
    
    async def _make_request(self, params: dict) -> dict:
        """Make HTTP request to Alpha Vantage API with exponential backoff retry.
        
        Implements retry logic for transient failures (429, 503) with exponential backoff.
        Formula: wait_time = INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ^ retry_attempt)
        
        Args:
            params: Query parameters for API request
        
        Returns:
            JSON response data
        
        Raises:
            RuntimeError: If request fails after all retries or external API error
        """
        # Lazy initialize session if not already created
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        
        last_exception = None
        start_time = time.time()
        function = params.get("function", "UNKNOWN")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    "Making Alpha Vantage API request",
                    extra={"extra_fields": {
                        "function": function,
                        "symbol": params.get("symbol"),
                        "attempt": attempt + 1,
                        "max_retries": self.MAX_RETRIES
                    }}
                )
                
                request_start = time.time()
                
                async with self._session.get(self.BASE_URL, params=params) as response:
                    # Check for rate limit (429) or service unavailable (503)
                    if response.status in (429, 503):
                        wait_time = self.INITIAL_BACKOFF * (self.BACKOFF_MULTIPLIER ** attempt)
                        
                        logger.warning(
                            f"Alpha Vantage API {response.status}, retrying with exponential backoff",
                            extra={"extra_fields": {
                                "status_code": response.status,
                                "attempt": attempt + 1,
                                "wait_seconds": wait_time,
                                "function": function
                            }}
                        )
                        
                        # Track rate limit event
                        self.telemetry.track_event(
                            "AlphaVantage.RateLimit",
                            {
                                "function": function,
                                "status_code": response.status,
                                "attempt": attempt + 1
                            }
                        )
                        
                        if attempt < self.MAX_RETRIES - 1:
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Last attempt failed
                            raise RuntimeError(f"API rate limit exceeded after {self.MAX_RETRIES} retries")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Calculate duration
                    duration_ms = (time.time() - request_start) * 1000
                    total_duration_ms = (time.time() - start_time) * 1000
                    
                    logger.info(
                        "Alpha Vantage API request successful",
                        extra={"extra_fields": {
                            "function": function,
                            "status_code": response.status,
                            "attempt": attempt + 1,
                            "duration_ms": duration_ms
                        }}
                    )
                    
                    # Track successful API call
                    self.telemetry.track_dependency(
                        name="AlphaVantageAPI",
                        dependency_type="HTTP",
                        data=f"{function} - {params.get('symbol', params.get('keywords', ''))}",
                        duration=total_duration_ms,
                        success=True,
                        properties={
                            "function": function,
                            "status_code": response.status,
                            "attempt": attempt + 1
                        }
                    )
                    
                    # Track call count metric
                    self.telemetry.track_metric(
                        "AlphaVantage.ApiCall.Count",
                        1.0,
                        {"function": function, "success": "true"}
                    )
                    
                    return data
                    
            except aiohttp.ClientResponseError as e:
                last_exception = e
                duration_ms = (time.time() - start_time) * 1000
                
                # Track failed API call
                self.telemetry.track_dependency(
                    name="AlphaVantageAPI",
                    dependency_type="HTTP",
                    data=f"{function} - {params.get('symbol', params.get('keywords', ''))}",
                    duration=duration_ms,
                    success=False,
                    properties={
                        "function": function,
                        "status_code": e.status,
                        "error": str(e)
                    }
                )
                
                # Retry on 429 or 503
                if e.status in (429, 503) and attempt < self.MAX_RETRIES - 1:
                    wait_time = self.INITIAL_BACKOFF * (self.BACKOFF_MULTIPLIER ** attempt)
                    
                    logger.warning(
                        f"Alpha Vantage API HTTP {e.status}, retrying",
                        extra={"extra_fields": {
                            "status_code": e.status,
                            "attempt": attempt + 1,
                            "wait_seconds": wait_time,
                            "function": function
                        }}
                    )
                    
                    await asyncio.sleep(wait_time)
                    continue
                
                # Non-retryable error
                logger.error(
                    "Alpha Vantage API HTTP error",
                    extra={"extra_fields": {
                        "status_code": e.status,
                        "message": str(e),
                        "function": function,
                        "attempt": attempt + 1
                    }}
                )
                raise RuntimeError(f"External stock API error: {e.status}") from e
                
            except aiohttp.ClientError as e:
                last_exception = e
                duration_ms = (time.time() - start_time) * 1000
                
                # Track failed API call
                self.telemetry.track_dependency(
                    name="AlphaVantageAPI",
                    dependency_type="HTTP",
                    data=f"{function} - {params.get('symbol', params.get('keywords', ''))}",
                    duration=duration_ms,
                    success=False,
                    properties={
                        "function": function,
                        "error": str(e)
                    }
                )
                
                # Retry connection errors
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.INITIAL_BACKOFF * (self.BACKOFF_MULTIPLIER ** attempt)
                    
                    logger.warning(
                        "Alpha Vantage API connection error, retrying",
                        extra={"extra_fields": {
                            "error": str(e),
                            "attempt": attempt + 1,
                            "wait_seconds": wait_time,
                            "function": function
                        }}
                    )
                    
                    await asyncio.sleep(wait_time)
                    continue
                
                logger.error(
                    "Alpha Vantage API connection error",
                    extra={"extra_fields": {
                        "error": str(e),
                        "function": function,
                        "attempt": attempt + 1
                    }}
                )
                raise RuntimeError("Stock data service temporarily unavailable") from e
        
        # Should not reach here, but handle gracefully
        raise RuntimeError("Max retries exceeded") from last_exception
