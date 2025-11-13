"""Integration tests for watchlist API endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from fastapi import status

from src.api.main import app
from src.models.watchlist import WatchlistItem


@pytest.fixture
def mock_watchlist_service():
    """Mock watchlist service for integration tests."""
    from src.api.routers.watchlist import get_watchlist_service
    
    mock_service = AsyncMock()
    
    async def override_get_service():
        return mock_service
    
    app.dependency_overrides[get_watchlist_service] = override_get_service
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


class TestWatchlistEndpoints:
    """Test suite for watchlist API endpoints."""

    @pytest.mark.asyncio
    async def test_get_watchlist_success(
        self, mock_watchlist_service, mock_auth
    ):
        """Test successfully retrieving user's watchlist (T117)."""
        # Setup
        mock_items = [
            WatchlistItem(
                id="id1",
                user_id="test@example.com",
                symbol="AAPL",
                company_name="Apple Inc.",
                memo="Test memo",
                display_order=1,
            ),
            WatchlistItem(
                id="id2",
                user_id="test@example.com",
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                memo="",
                display_order=2,
            ),
        ]
        mock_watchlist_service.get_watchlist.return_value = mock_items

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/watchlist")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["memo"] == "Test memo"
        assert data[1]["symbol"] == "GOOGL"
        mock_watchlist_service.get_watchlist.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_get_watchlist_empty(
        self, mock_watchlist_service, mock_auth
    ):
        """Test retrieving empty watchlist."""
        # Setup
        mock_watchlist_service.get_watchlist.return_value = []

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/watchlist")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_watchlist_unauthorized(self):
        """Test watchlist endpoint requires authentication."""
        # No mock_auth fixture - authentication will fail
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/watchlist")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_add_to_watchlist_success(
        self, mock_watchlist_service, mock_auth
    ):
        """Test successfully adding stock to watchlist (T118)."""
        # Setup
        from src.models.watchlist import WatchlistItemCreate
        
        created_item = WatchlistItem(
            id="new-id",
            user_id="test@example.com",
            symbol="TSLA",
            company_name="Tesla, Inc.",
            memo="매수 고려",
            display_order=1,
        )
        mock_watchlist_service.add_to_watchlist.return_value = created_item

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/watchlist",
                json={
                    "symbol": "TSLA",
                    "company_name": "Tesla, Inc.",
                    "memo": "매수 고려",
                    "display_order": 1,
                },
            )

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["company_name"] == "Tesla, Inc."
        assert data["memo"] == "매수 고려"
        mock_watchlist_service.add_to_watchlist.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_watchlist_duplicate_rejection(
        self, mock_watchlist_service, mock_auth
    ):
        """Test duplicate stock rejection with Korean warning (T119, FR-009-1)."""
        # Setup
        from src.services.watchlist_service import DuplicateStockError
        
        mock_watchlist_service.add_to_watchlist.side_effect = DuplicateStockError(
            "AAPL already in watchlist"
        )

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/watchlist",
                json={
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "display_order": 1,
                },
            )

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "이미 관심종목에 추가된 종목입니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_to_watchlist_invalid_data(
        self, mock_watchlist_service, mock_auth
    ):
        """Test validation error for invalid watchlist data."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Missing required fields
            response = await client.post(
                "/api/v1/watchlist",
                json={
                    "symbol": "AAPL",
                    # missing company_name and display_order
                },
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_watchlist_item_success(
        self, mock_watchlist_service, mock_auth
    ):
        """Test successfully updating watchlist item."""
        # Setup
        updated_item = WatchlistItem(
            id="test-id",
            user_id="test@example.com",
            symbol="AAPL",
            company_name="Apple Inc.",
            memo="Updated memo",
            display_order=1,
        )
        mock_watchlist_service.update_item.return_value = updated_item

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/watchlist/test-id",
                json={"memo": "Updated memo"},
            )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["memo"] == "Updated memo"
        mock_watchlist_service.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_watchlist_item_not_found(
        self, mock_watchlist_service, mock_auth
    ):
        """Test updating non-existent item returns 404."""
        # Setup
        mock_watchlist_service.update_item.return_value = None

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/watchlist/nonexistent-id",
                json={"memo": "New memo"},
            )

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_watchlist_item_success(
        self, mock_watchlist_service, mock_auth
    ):
        """Test successfully deleting watchlist item."""
        # Setup
        mock_watchlist_service.delete_item.return_value = True

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/v1/watchlist/test-id")

        # Verify
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_watchlist_service.delete_item.assert_called_once_with(
            "test@example.com", "test-id"
        )

    @pytest.mark.asyncio
    async def test_delete_watchlist_item_not_found(
        self, mock_watchlist_service, mock_auth
    ):
        """Test deleting non-existent item returns 404."""
        # Setup
        mock_watchlist_service.delete_item.return_value = False

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/v1/watchlist/nonexistent-id")

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_reorder_watchlist_success(
        self, mock_watchlist_service, mock_auth
    ):
        """Test successfully reordering watchlist items (T120)."""
        # Setup
        reordered_items = [
            WatchlistItem(
                id="id2",
                user_id="test@example.com",
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                display_order=1,
            ),
            WatchlistItem(
                id="id1",
                user_id="test@example.com",
                symbol="AAPL",
                company_name="Apple Inc.",
                display_order=2,
            ),
        ]
        mock_watchlist_service.reorder_items.return_value = reordered_items

        # Execute
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/watchlist/reorder",
                json={"item_ids": ["id2", "id1"]},
            )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "id2"
        assert data[0]["display_order"] == 1
        assert data[1]["id"] == "id1"
        assert data[1]["display_order"] == 2
        mock_watchlist_service.reorder_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_reorder_watchlist_invalid_payload(
        self, mock_watchlist_service, mock_auth
    ):
        """Test reorder endpoint validates payload structure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Missing item_ids field
            response = await client.post(
                "/api/v1/watchlist/reorder",
                json={},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
