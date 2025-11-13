"""Unit tests for Alpha Vantage API client."""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from src.external.alpha_vantage_client import AlphaVantageClient
from src.models.stock import StockQuote, StockSearchResult


@pytest.fixture
def mock_session():
    """Create mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    return session


@pytest.fixture
def client(mock_session):
    """Create AlphaVantageClient with mock session."""
    return AlphaVantageClient(api_key="test_api_key", session=mock_session)


class TestAlphaVantageClient:
    """Test suite for AlphaVantageClient."""
    
    @pytest.mark.asyncio
    async def test_get_quote_success(self, client, mock_session):
        """Test successful quote retrieval."""
        # Mock API response
        mock_response = {
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "176.50",
                "03. high": "179.00",
                "04. low": "176.20",
                "05. price": "178.32",
                "06. volume": "58392010",
                "07. latest trading day": "2025-11-05",
                "08. previous close": "176.17",
                "09. change": "2.15",
                "10. change percent": "1.22%"
            }
        }
        
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()
        
        mock_session.get.return_value = mock_resp
        
        # Call get_quote
        quote = await client.get_quote("AAPL")
        
        # Assertions
        assert isinstance(quote, StockQuote)
        assert quote.symbol == "AAPL"
        assert quote.current_price == Decimal("178.32")
        assert quote.change == Decimal("2.15")
        assert quote.change_percent == Decimal("1.22")
        assert quote.open == Decimal("176.50")
        assert quote.high == Decimal("179.00")
        assert quote.low == Decimal("176.20")
        assert quote.volume == 58392010
        assert quote.currency == "USD"
    
    @pytest.mark.asyncio
    async def test_get_quote_symbol_not_found(self, client, mock_session):
        """Test quote retrieval for invalid symbol."""
        mock_response = {
            "Error Message": "Invalid API call. Please retry or visit the documentation for TIME_SERIES_INTRADAY."
        }
        
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()
        
        mock_session.get.return_value = mock_resp
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Stock symbol not found"):
            await client.get_quote("INVALID")
    
    @pytest.mark.asyncio
    async def test_get_quote_rate_limit(self, client, mock_session):
        """Test quote retrieval when rate limit hit."""
        mock_response = {
            "Note": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
        }
        
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()
        
        mock_session.get.return_value = mock_resp
        
        # Expect RuntimeError
        with pytest.raises(RuntimeError, match="API rate limit exceeded"):
            await client.get_quote("AAPL")
    
    @pytest.mark.asyncio
    async def test_search_symbol_success(self, client, mock_session):
        """Test successful symbol search."""
        mock_response = {
            "bestMatches": [
                {
                    "1. symbol": "AAPL",
                    "2. name": "Apple Inc.",
                    "3. type": "Equity",
                    "4. region": "United States",
                    "5. marketOpen": "09:30",
                    "6. marketClose": "16:00",
                    "7. timezone": "UTC-04",
                    "8. currency": "USD",
                    "9. matchScore": "1.0000"
                }
            ]
        }
        
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()
        
        mock_session.get.return_value = mock_resp
        
        # Call search_symbol
        results = await client.search_symbol("apple")
        
        # Assertions
        assert len(results) == 1
        assert isinstance(results[0], StockSearchResult)
        assert results[0].symbol == "AAPL"
        assert results[0].name == "Apple Inc."
        assert results[0].type == "Equity"
        assert results[0].region == "United States"
        assert results[0].currency == "USD"
    
    @pytest.mark.asyncio
    async def test_search_symbol_empty_results(self, client, mock_session):
        """Test symbol search with no matches."""
        mock_response = {"bestMatches": []}
        
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()
        
        mock_session.get.return_value = mock_resp
        
        # Call search_symbol
        results = await client.search_symbol("nonexistent")
        
        # Assertions
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_on_429(self, client, mock_session):
        """Test exponential backoff retry logic on 429 status."""
        # First two attempts return 429, third succeeds
        mock_resp_429 = AsyncMock()
        mock_resp_429.status = 429
        mock_resp_429.__aenter__ = AsyncMock(return_value=mock_resp_429)
        mock_resp_429.__aexit__ = AsyncMock()
        
        mock_resp_success = AsyncMock()
        mock_resp_success.status = 200
        mock_resp_success.json = AsyncMock(return_value={
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "176.50",
                "03. high": "179.00",
                "04. low": "176.20",
                "05. price": "178.32",
                "06. volume": "58392010",
                "09. change": "2.15",
                "10. change percent": "1.22%"
            }
        })
        mock_resp_success.raise_for_status = MagicMock()
        mock_resp_success.__aenter__ = AsyncMock(return_value=mock_resp_success)
        mock_resp_success.__aexit__ = AsyncMock()
        
        # Mock session.get to return 429 twice, then success
        mock_session.get.side_effect = [mock_resp_429, mock_resp_429, mock_resp_success]
        
        # Patch asyncio.sleep to avoid actual delays
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            quote = await client.get_quote("AAPL")
            
            # Verify retries happened
            assert mock_session.get.call_count == 3
            
            # Verify exponential backoff delays
            assert mock_sleep.call_count == 2
            # First retry: 1.0 * (2.0 ^ 0) = 1.0 seconds
            assert mock_sleep.call_args_list[0][0][0] == 1.0
            # Second retry: 1.0 * (2.0 ^ 1) = 2.0 seconds
            assert mock_sleep.call_args_list[1][0][0] == 2.0
            
            # Verify successful result
            assert quote.symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client, mock_session):
        """Test max retries exceeded raises error."""
        mock_resp_429 = AsyncMock()
        mock_resp_429.status = 429
        mock_resp_429.__aenter__ = AsyncMock(return_value=mock_resp_429)
        mock_resp_429.__aexit__ = AsyncMock()
        
        # All attempts return 429
        mock_session.get.return_value = mock_resp_429
        
        # Patch asyncio.sleep
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="(API rate limit exceeded after 3 retries|Max retries exceeded)"):
                await client.get_quote("AAPL")
            
            # Verify all 3 retries were attempted
            assert mock_session.get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        async with AlphaVantageClient(api_key="test_key") as client:
            assert client._session is not None
            assert client._own_session is True
        
        # Session should be closed after exiting context
        # (we can't check this directly, but coverage will show it was called)
