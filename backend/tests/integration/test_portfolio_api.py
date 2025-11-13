"""Integration tests for portfolio API endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from fastapi import status
from datetime import datetime

from src.api.main import app
from src.models.portfolio import PortfolioEntry, PortfolioEntryResponse


@pytest.fixture
def mock_portfolio_service():
    """Mock portfolio service for integration tests."""
    from src.api.routes.portfolio import get_portfolio_service

    mock_service = AsyncMock()

    async def override_get_service():
        return mock_service

    app.dependency_overrides[get_portfolio_service] = override_get_service
    yield mock_service
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth():
    """Mock authentication dependency."""
    from src.api.dependencies.auth import get_current_user

    async def override_get_current_user():
        return {"user_id": "test@example.com", "email": "test@example.com"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def sample_portfolio_response():
    """Create sample portfolio entry response."""
    return PortfolioEntryResponse(
        entry_id="entry-1",
        user_id="test@example.com",
        symbol="AAPL",
        company_name="Apple Inc.",
        category="장기",
        purchase_price=150.00,
        quantity=10,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        current_price=160.00,
        market_value=1600.00,
        profit_loss=100.00,
        profit_loss_percent=6.67,
    )


class TestPortfolioEndpoints:
    """Test suite for portfolio API endpoints."""

    # T161: GET /portfolio Tests
    @pytest.mark.asyncio
    async def test_get_portfolio_success(self, mock_portfolio_service, mock_auth, sample_portfolio_response):
        """Test successfully retrieving user's portfolio (T141)."""
        # Setup
        mock_portfolio_service.get_portfolio_with_calculations.return_value = [sample_portfolio_response]

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/portfolio")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["category"] == "장기"
        assert data[0]["current_price"] == 160.00
        assert data[0]["profit_loss"] == 100.00
        mock_portfolio_service.get_portfolio_with_calculations.assert_called_once_with("test@example.com", None)

    @pytest.mark.asyncio
    async def test_get_portfolio_with_category_filter(
        self, mock_portfolio_service, mock_auth, sample_portfolio_response
    ):
        """Test retrieving portfolio filtered by category."""
        # Setup
        mock_portfolio_service.get_portfolio_with_calculations.return_value = [sample_portfolio_response]

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/portfolio?category=장기")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "장기"
        mock_portfolio_service.get_portfolio_with_calculations.assert_called_once_with("test@example.com", "장기")

    @pytest.mark.asyncio
    async def test_get_portfolio_empty(self, mock_portfolio_service, mock_auth):
        """Test retrieving empty portfolio."""
        # Setup
        mock_portfolio_service.get_portfolio_with_calculations.return_value = []

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/portfolio")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_portfolio_unauthorized(self, mock_portfolio_service):
        """Test retrieving portfolio without authentication."""
        # Execute (no mock_auth fixture)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/portfolio")

        # Verify
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # T162: POST /portfolio Tests
    @pytest.mark.asyncio
    async def test_add_to_portfolio_success(self, mock_portfolio_service, mock_auth, sample_portfolio_response):
        """Test successfully adding stock to portfolio (T142)."""
        # Setup
        mock_entry = PortfolioEntry(
            entry_id="entry-1",
            user_id="test@example.com",
            symbol="AAPL",
            company_name="Apple Inc.",
            category="장기",
            purchase_price=150.00,
            quantity=10,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_portfolio_service.create_portfolio_entry.return_value = mock_entry
        mock_portfolio_service.get_entry_with_calculations.return_value = sample_portfolio_response

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/portfolio",
                json={
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "category": "장기",
                    "purchase_price": 150.00,
                    "quantity": 10,
                },
            )

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["current_price"] == 160.00
        assert data["profit_loss"] == 100.00

    @pytest.mark.asyncio
    async def test_add_to_portfolio_duplicate_error(self, mock_portfolio_service, mock_auth):
        """Test duplicate stock error when adding to portfolio (T142, FR-017-1)."""
        # Setup: Service raises ValueError for duplicate
        mock_portfolio_service.create_portfolio_entry.side_effect = ValueError(
            "이미 해당 카테고리에 등록된 종목입니다"
        )

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/portfolio",
                json={
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "category": "장기",
                    "purchase_price": 150.00,
                    "quantity": 10,
                },
            )

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "이미 해당 카테고리에 등록된 종목입니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_to_portfolio_limit_error(self, mock_portfolio_service, mock_auth):
        """Test 10-item limit error when adding to portfolio (T142, FR-020)."""
        # Setup: Service raises ValueError for limit reached
        mock_portfolio_service.create_portfolio_entry.side_effect = ValueError("최대 10개 종목까지 등록 가능")

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/portfolio",
                json={
                    "symbol": "MSFT",
                    "company_name": "Microsoft Corporation",
                    "category": "단기",
                    "purchase_price": 300.00,
                    "quantity": 5,
                },
            )

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "최대 10개 종목까지 등록 가능" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_to_portfolio_validation_error(self, mock_auth):
        """Test validation error with invalid data."""
        # Execute: Invalid purchase_price (negative)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/portfolio",
                json={
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "category": "장기",
                    "purchase_price": -150.00,  # Invalid
                    "quantity": 10,
                },
            )

        # Verify
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # T163: GET /portfolio/{entry_id} Tests
    @pytest.mark.asyncio
    async def test_get_portfolio_entry_success(self, mock_portfolio_service, mock_auth, sample_portfolio_response):
        """Test successfully retrieving single portfolio entry (T143)."""
        # Setup
        mock_portfolio_service.get_entry_with_calculations.return_value = sample_portfolio_response

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/portfolio/entry-1")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["entry_id"] == "entry-1"
        assert data["symbol"] == "AAPL"
        assert data["profit_loss"] == 100.00
        mock_portfolio_service.get_entry_with_calculations.assert_called_once_with("entry-1", "test@example.com")

    @pytest.mark.asyncio
    async def test_get_portfolio_entry_not_found(self, mock_portfolio_service, mock_auth):
        """Test retrieving non-existent portfolio entry."""
        # Setup
        mock_portfolio_service.get_entry_with_calculations.return_value = None

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/portfolio/nonexistent")

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "포트폴리오 항목을 찾을 수 없습니다" in response.json()["detail"]

    # T164: DELETE /portfolio/{entry_id} Tests
    @pytest.mark.asyncio
    async def test_delete_portfolio_entry_success(self, mock_portfolio_service, mock_auth):
        """Test successfully deleting portfolio entry (T145)."""
        # Setup
        mock_portfolio_service.delete_portfolio_entry.return_value = True

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/v1/portfolio/entry-1")

        # Verify
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_portfolio_service.delete_portfolio_entry.assert_called_once_with("entry-1", "test@example.com")

    @pytest.mark.asyncio
    async def test_delete_portfolio_entry_not_found(self, mock_portfolio_service, mock_auth):
        """Test deleting non-existent portfolio entry."""
        # Setup
        mock_portfolio_service.delete_portfolio_entry.return_value = False

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/v1/portfolio/nonexistent")

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "포트폴리오 항목을 찾을 수 없습니다" in response.json()["detail"]

    # T165: PATCH /portfolio/{entry_id} Tests
    @pytest.mark.asyncio
    async def test_update_portfolio_entry_success(self, mock_portfolio_service, mock_auth, sample_portfolio_response):
        """Test successfully updating portfolio entry (T144)."""
        # Setup
        updated_entry = PortfolioEntry(
            entry_id="entry-1",
            user_id="test@example.com",
            symbol="AAPL",
            company_name="Apple Inc.",
            category="장기",
            purchase_price=155.00,  # Updated
            quantity=12,  # Updated
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        updated_response = PortfolioEntryResponse(
            **{**sample_portfolio_response.dict(), "purchase_price": 155.00, "quantity": 12}
        )
        mock_portfolio_service.update_portfolio_entry.return_value = updated_entry
        mock_portfolio_service.get_entry_with_calculations.return_value = updated_response

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/portfolio/entry-1",
                json={"purchase_price": 155.00, "quantity": 12},
            )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["purchase_price"] == 155.00
        assert data["quantity"] == 12

    @pytest.mark.asyncio
    async def test_update_portfolio_entry_not_found(self, mock_portfolio_service, mock_auth):
        """Test updating non-existent portfolio entry."""
        # Setup
        mock_portfolio_service.update_portfolio_entry.return_value = None

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/portfolio/nonexistent",
                json={"purchase_price": 155.00},
            )

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "포트폴리오 항목을 찾을 수 없습니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_portfolio_entry_validation_error(self, mock_auth):
        """Test updating with invalid data."""
        # Execute: Invalid quantity (negative)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/portfolio/entry-1",
                json={"quantity": -5},  # Invalid
            )

        # Verify
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_portfolio_entry_partial(self, mock_portfolio_service, mock_auth, sample_portfolio_response):
        """Test updating only purchase_price (partial update)."""
        # Setup
        updated_entry = PortfolioEntry(
            entry_id="entry-1",
            user_id="test@example.com",
            symbol="AAPL",
            company_name="Apple Inc.",
            category="장기",
            purchase_price=158.00,  # Updated
            quantity=10,  # Unchanged
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        updated_response = PortfolioEntryResponse(**{**sample_portfolio_response.dict(), "purchase_price": 158.00})
        mock_portfolio_service.update_portfolio_entry.return_value = updated_entry
        mock_portfolio_service.get_entry_with_calculations.return_value = updated_response

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/portfolio/entry-1",
                json={"purchase_price": 158.00},
            )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["purchase_price"] == 158.00
        assert data["quantity"] == 10  # Unchanged
