"""
Pytest configuration and fixtures for MyStock backend tests.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["MYSTOCK3_APP_ENV"] = "test"
os.environ["MYSTOCK3_COSMOS_ENDPOINT"] = "https://test.documents.azure.com:443/"
os.environ["MYSTOCK3_COSMOS_KEY"] = "test_key"
os.environ["MYSTOCK3_DATABASE_NAME"] = "test_mystock"
os.environ["MYSTOCK3_SECRET_KEY"] = "test_secret_key_for_jwt_signing_minimum_32_chars"
os.environ["MYSTOCK3_ALPHA_VANTAGE_API_KEY"] = "test_alpha_vantage_key"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_cosmos_client():
    """Mock Cosmos DB client."""
    mock_client = MagicMock()
    mock_database = MagicMock()
    mock_container = MagicMock()
    
    mock_client.get_database_client.return_value = mock_database
    mock_database.get_container_client.return_value = mock_container
    
    return mock_client


@pytest.fixture
def mock_cosmos_container():
    """Mock Cosmos DB container."""
    mock_container = MagicMock()
    
    # Mock common container methods
    mock_container.create_item = MagicMock()
    mock_container.read_item = MagicMock()
    mock_container.query_items = MagicMock()
    mock_container.replace_item = MagicMock()
    mock_container.delete_item = MagicMock()
    
    return mock_container


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    from src.api.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_test_client() -> Generator[TestClient, None, None]:
    """Create a synchronous test client."""
    from src.api.main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client (alias for sync_test_client)."""
    from src.api.main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_client(client, valid_jwt_token) -> Generator[TestClient, None, None]:
    """Create a test client with authentication headers."""
    # Add default authorization header
    client.headers.update({"Authorization": f"Bearer {valid_jwt_token}"})
    yield client


@pytest.fixture
def test_user_token(valid_jwt_token):
    """Provide test user JWT token."""
    return valid_jwt_token


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
        "user_id": "user_test123",
    }


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 150.25,
        "change": 2.50,
        "change_percent": 1.69,
        "volume": 50000000,
    }


@pytest.fixture
def sample_watchlist_item():
    """Sample watchlist item for testing."""
    return {
        "item_id": "watchlist_test123",
        "user_id": "user_test123",
        "symbol": "AAPL",
        "memo": "Good buy opportunity",
        "order": 1,
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_portfolio_entry():
    """Sample portfolio entry for testing."""
    return {
        "entry_id": "portfolio_test123",
        "user_id": "user_test123",
        "symbol": "AAPL",
        "category": "장기",
        "purchase_price": 145.00,
        "quantity": 10,
        "purchase_date": "2025-01-01",
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_alpha_vantage_client():
    """Mock Alpha Vantage API client."""
    mock_client = AsyncMock()
    
    mock_client.search_symbol = AsyncMock(return_value=[
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "type": "Equity",
            "region": "United States",
        }
    ])
    
    mock_client.get_quote = AsyncMock(return_value={
        "symbol": "AAPL",
        "price": 150.25,
        "change": 2.50,
        "change_percent": 1.69,
        "volume": 50000000,
        "latest_trading_day": "2025-01-01",
    })
    
    mock_client.get_daily_history = AsyncMock(return_value=[
        {
            "date": "2025-01-01",
            "open": 148.00,
            "high": 151.00,
            "low": 147.50,
            "close": 150.25,
            "volume": 50000000,
        }
    ])
    
    return mock_client


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing."""
    from src.utils.jwt import create_access_token
    
    token_data = {
        "email": "test@example.com",
        "user_id": "user_test123",
    }
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Create authorization headers with valid JWT."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture(autouse=True)
async def reset_database():
    """Reset database state between tests."""
    # This is a placeholder for actual database cleanup
    # In a real scenario, you would:
    # 1. Clear test containers
    # 2. Reset sequences/IDs
    # 3. Restore initial state
    yield
    # Cleanup after test
    pass


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return MagicMock()


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Tests that take a long time")


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add unit marker to tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Add integration marker to tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        # Add e2e marker to tests in e2e/ directory
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
