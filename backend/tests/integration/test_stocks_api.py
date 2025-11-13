"""Integration tests for stock API endpoints."""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock
from fastapi import status

from src.models.stock import StockQuote, StockSearchResult


@pytest.fixture
def mock_alpha_vantage_client(client):
    """Mock Alpha Vantage client for testing using dependency override."""
    from src.api.main import app
    from src.api.routers.stocks import get_alpha_vantage_client
    
    mock_client = AsyncMock()
    
    async def override_get_client():
        yield mock_client
    
    app.dependency_overrides[get_alpha_vantage_client] = override_get_client
    yield mock_client
    app.dependency_overrides.clear()


class TestStockSearchEndpoint:
    """Test suite for stock search endpoint."""
    
    @pytest.mark.asyncio
    async def test_search_stocks_success(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test successful stock search."""
        # Mock search results
        mock_results = [
            StockSearchResult(
                symbol="AAPL",
                name="Apple Inc.",
                type="Equity",
                region="United States",
                currency="USD"
            ),
            StockSearchResult(
                symbol="APLE",
                name="Apple Hospitality REIT Inc.",
                type="REIT",
                region="United States",
                currency="USD"
            )
        ]
        mock_alpha_vantage_client.search_symbol.return_value = mock_results
        
        # Make request
        response = auth_client.get(
            "/api/v1/stocks/search",
            params={"keywords": "apple"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "apple"
        assert len(data["results"]) == 2
        assert data["results"][0]["symbol"] == "AAPL"
        assert data["results"][0]["name"] == "Apple Inc."
    
    @pytest.mark.asyncio
    async def test_search_stocks_empty_results(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test stock search with no matches."""
        mock_alpha_vantage_client.search_symbol.return_value = []
        
        response = auth_client.get(
            "/api/v1/stocks/search",
            params={"keywords": "nonexistent"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "nonexistent"
        assert len(data["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_search_stocks_rate_limit(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test stock search when rate limit hit."""
        mock_alpha_vantage_client.search_symbol.side_effect = RuntimeError("API rate limit exceeded")
        
        response = auth_client.get(
            "/api/v1/stocks/search",
            params={"keywords": "apple"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert "rate limit" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_search_stocks_external_api_error(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test stock search when external API fails."""
        mock_alpha_vantage_client.search_symbol.side_effect = RuntimeError("Connection failed")
        
        response = auth_client.get(
            "/api/v1/stocks/search",
            params={"keywords": "apple"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "temporarily unavailable" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_search_stocks_unauthorized(self, client):
        """Test stock search without authentication."""
        response = client.get(
            "/api/v1/stocks/search",
            params={"keywords": "apple"}
        )
        
        # HTTPBearer returns 403 when credentials are missing
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStockQuoteEndpoint:
    """Test suite for stock quote endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_quote_success(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test successful quote retrieval."""
        # Mock quote
        mock_quote = StockQuote(
            symbol="AAPL",
            company_name="Apple Inc.",
            current_price=Decimal("178.32"),
            change=Decimal("2.15"),
            change_percent=Decimal("1.22"),
            open=Decimal("176.50"),
            high=Decimal("179.00"),
            low=Decimal("176.20"),
            volume=58392010,
            last_updated="2025-11-05T11:30:00Z",
            currency="USD"
        )
        mock_alpha_vantage_client.get_quote.return_value = mock_quote
        
        # Make request
        response = auth_client.get(
            "/api/v1/stocks/AAPL/quote",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert float(data["current_price"]) == 178.32
        assert float(data["change"]) == 2.15
        assert data["currency"] == "USD"
    
    @pytest.mark.asyncio
    async def test_get_quote_cached(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test quote retrieval uses cache."""
        from src.services.stock_cache_service import get_cache
        
        mock_quote = StockQuote(
            symbol="TSLA",
            company_name="Tesla Inc.",
            current_price=Decimal("245.50"),
            change=Decimal("-3.25"),
            change_percent=Decimal("-1.31"),
            open=Decimal("248.75"),
            high=Decimal("250.00"),
            low=Decimal("244.00"),
            volume=42000000,
            last_updated="2025-11-05T11:30:00Z",
            currency="USD"
        )
        
        # Pre-populate cache
        cache = get_cache()
        cache.set("TSLA", mock_quote)
        
        # Make request (should use cache, not call API)
        response = auth_client.get(
            "/api/v1/stocks/TSLA/quote",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert float(data["current_price"]) == 245.50
        
        # Verify API was NOT called (cache hit)
        mock_alpha_vantage_client.get_quote.assert_not_called()
        
        # Cleanup
        cache.clear()
    
    @pytest.mark.asyncio
    async def test_get_quote_not_found(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test quote retrieval for symbol that doesn't exist."""
        # Use valid format but non-existent symbol
        mock_alpha_vantage_client.get_quote.side_effect = ValueError("Stock symbol not found")
        
        response = auth_client.get(
            "/api/v1/stocks/ZZZZZ/quote",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "종목을 찾을 수 없음"
    
    @pytest.mark.asyncio
    async def test_get_quote_rate_limit(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test quote retrieval when rate limit hit."""
        mock_alpha_vantage_client.get_quote.side_effect = RuntimeError("API rate limit exceeded")
        
        response = auth_client.get(
            "/api/v1/stocks/AAPL/quote",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert "rate limit" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_quote_external_api_error(self, auth_client, test_user_token, mock_alpha_vantage_client):
        """Test quote retrieval when external API fails."""
        mock_alpha_vantage_client.get_quote.side_effect = RuntimeError("Connection timeout")
        
        response = auth_client.get(
            "/api/v1/stocks/AAPL/quote",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "temporarily unavailable" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_quote_unauthorized(self, client):
        """Test quote retrieval without authentication."""
        response = client.get("/api/v1/stocks/AAPL/quote")
        
        # HTTPBearer returns 403 when credentials are missing
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStockHistoryEndpoint:
    """Test suite for stock history endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_history_not_implemented(self, auth_client, test_user_token):
        """Test stock history endpoint (not yet implemented)."""
        response = auth_client.get(
            "/api/v1/stocks/AAPL/history",
            params={"period": "1M"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
        data = response.json()
        assert "not yet implemented" in data["detail"].lower()
