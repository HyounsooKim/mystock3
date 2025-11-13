"""Stock market data API endpoints."""
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.api.dependencies.auth import get_current_user
from src.config import get_settings
from src.external.alpha_vantage_client import AlphaVantageClient
from src.models.stock import (
    StockHistoryResponse,
    StockQuote,
    StockSearchResponse,
    StockSearchResult,
)
from src.models.user import UserResponse
from src.services.stock_cache_service import get_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stocks", tags=["stocks"])


async def get_alpha_vantage_client() -> AlphaVantageClient:
    """Dependency to get Alpha Vantage API client.
    
    Returns:
        Configured AlphaVantageClient instance
    """
    settings = get_settings()
    async with AlphaVantageClient(api_key=settings.alpha_vantage_api_key) as client:
        yield client


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    keywords: Annotated[str, Query(min_length=1, max_length=100, description="Search query")],
    current_user: Annotated[dict, Depends(get_current_user)],
    client: Annotated[AlphaVantageClient, Depends(get_alpha_vantage_client)],
) -> StockSearchResponse:
    """Search for stock symbols by keywords.
    
    Requires authentication. Returns list of matching stock symbols
    from Alpha Vantage API.
    
    Args:
        keywords: Search query string
        current_user: Authenticated user
        client: Alpha Vantage API client
    
    Returns:
        List of matching stocks with symbol, name, type, region, currency
    
    Raises:
        HTTPException 429: API rate limit exceeded
        HTTPException 503: External stock API temporarily unavailable
    """
    try:
        logger.info(
            "Stock search request",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "keywords": keywords
            }}
        )
        
        results = await client.search_symbol(keywords)
        
        logger.info(
            "Stock search completed",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "keywords": keywords,
                "results_count": len(results)
            }}
        )
        
        return StockSearchResponse(query=keywords, results=results)
        
    except RuntimeError as e:
        error_msg = str(e)
        
        if "rate limit" in error_msg.lower():
            logger.warning(
                "Rate limit exceeded during stock search",
                extra={"extra_fields": {"user_id": current_user["user_id"], "keywords": keywords}}
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API rate limit exceeded, please retry later"
            )
        
        logger.error(
            "Search external API error",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "keywords": keywords,
                "error": error_msg
            }}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stock data service temporarily unavailable"
        )


@router.get("/{symbol}/quote", response_model=StockQuote)
async def get_stock_quote(
    symbol: Annotated[str, Path(min_length=1, max_length=5, pattern="^[A-Z]{1,5}$")],
    current_user: Annotated[dict, Depends(get_current_user)],
    client: Annotated[AlphaVantageClient, Depends(get_alpha_vantage_client)],
) -> StockQuote:
    """Get current stock quote with 1-minute caching.
    
    Retrieves real-time stock price data. Data is cached for 1 minute
    to minimize external API calls (FR-028).
    
    Args:
        symbol: Stock ticker symbol (1-5 uppercase letters)
        current_user: Authenticated user
        client: Alpha Vantage API client
    
    Returns:
        Stock quote with current price, change, volume, etc.
    
    Raises:
        HTTPException 404: Stock symbol not found
        HTTPException 429: API rate limit exceeded
        HTTPException 503: External stock API temporarily unavailable
    """
    symbol_upper = symbol.upper()
    cache = get_cache()
    
    # Check cache first
    cached_quote = cache.get(symbol_upper)
    if cached_quote is not None:
        logger.info(
            "Returning cached stock quote",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "symbol": symbol_upper
            }}
        )
        return cached_quote
    
    # Cache miss - fetch from API
    try:
        logger.info(
            "Stock quote request",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "symbol": symbol_upper
            }}
        )
        
        quote = await client.get_quote(symbol_upper)
        
        # Store in cache
        cache.set(symbol_upper, quote)
        
        logger.info(
            "Stock quote retrieved and cached",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "symbol": symbol_upper,
                "price": str(quote.current_price)
            }}
        )
        
        return quote
        
    except ValueError as e:
        logger.warning(
            "Stock symbol not found",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "symbol": symbol_upper,
                "error": str(e)
            }}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="종목을 찾을 수 없음"
        )
        
    except RuntimeError as e:
        error_msg = str(e)
        
        if "rate limit" in error_msg.lower():
            logger.warning(
                "Rate limit exceeded during quote fetch",
                extra={"extra_fields": {"user_id": current_user["user_id"], "symbol": symbol_upper}}
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API rate limit exceeded, please retry later"
            )
        
        logger.error(
            "Quote fetch external API error",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "symbol": symbol_upper,
                "error": error_msg
            }}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stock data service temporarily unavailable"
        )


@router.get("/{symbol}/history", response_model=StockHistoryResponse)
async def get_stock_history(
    symbol: Annotated[str, Path(min_length=1, max_length=5, pattern="^[A-Z]{1,5}$")],
    current_user: Annotated[dict, Depends(get_current_user)],
    client: Annotated[AlphaVantageClient, Depends(get_alpha_vantage_client)],
    period: Annotated[
        Literal["1D", "5D", "1M", "3M", "6M", "1Y", "5Y"],
        Query(description="Time period for historical data")
    ] = "1M",
) -> StockHistoryResponse:
    """Get historical stock price data for charting.
    
    Returns time series data for candlestick charts.
    Not yet implemented - returns stub for T082.
    
    Args:
        symbol: Stock ticker symbol
        period: Time period (1D, 5D, 1M, 3M, 6M, 1Y, 5Y)
        current_user: Authenticated user
        client: Alpha Vantage API client
    
    Returns:
        Historical price data
    
    Raises:
        HTTPException 501: Not yet implemented
    """
    logger.warning(
        "Stock history endpoint not yet implemented",
        extra={"extra_fields": {
            "user_id": current_user["user_id"],
            "symbol": symbol.upper(),
            "period": period
        }}
    )
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Historical data not yet implemented"
    )
