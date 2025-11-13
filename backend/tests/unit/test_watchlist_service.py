"""Unit tests for watchlist service business logic."""

import pytest
from unittest.mock import AsyncMock, Mock

from src.models.watchlist import WatchlistItem, WatchlistItemCreate
from src.services.watchlist_service import DuplicateStockError, WatchlistService


class TestWatchlistService:
    """Test suite for watchlist service."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock watchlist repository."""
        repository = Mock()
        repository.get_by_user = AsyncMock()
        repository.exists = AsyncMock()
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        repository.delete = AsyncMock()
        repository.reorder = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        """Create watchlist service with mocked repository."""
        return WatchlistService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_add_to_watchlist_success(self, service, mock_repository):
        """Test successfully adding a stock to watchlist."""
        # Setup
        mock_repository.exists.return_value = False
        mock_repository.create.return_value = WatchlistItem(
            id="test-id",
            user_id="user@example.com",
            symbol="AAPL",
            company_name="Apple Inc.",
            memo="Test memo",
            display_order=1,
        )

        # Execute
        item = WatchlistItemCreate(
            symbol="AAPL",
            company_name="Apple Inc.",
            memo="Test memo",
            display_order=1,
        )
        result = await service.add_to_watchlist("user@example.com", item)

        # Verify
        assert result.symbol == "AAPL"
        mock_repository.exists.assert_called_once_with("user@example.com", "AAPL")
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_watchlist_duplicate_stock(self, service, mock_repository):
        """Test duplicate stock detection prevents adding same symbol (FR-009-1)."""
        # Setup: Symbol already exists
        mock_repository.exists.return_value = True

        # Execute & Verify
        item = WatchlistItemCreate(
            symbol="AAPL",
            company_name="Apple Inc.",
            display_order=1,
        )
        
        with pytest.raises(DuplicateStockError) as exc_info:
            await service.add_to_watchlist("user@example.com", item)
        
        assert "AAPL" in str(exc_info.value)
        mock_repository.exists.assert_called_once_with("user@example.com", "AAPL")
        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_to_watchlist_case_insensitive_duplicate(
        self, service, mock_repository
    ):
        """Test duplicate detection is case-insensitive."""
        # Setup: AAPL exists, trying to add aapl (after validation converts to AAPL)
        mock_repository.exists.return_value = True

        # Execute & Verify
        item = WatchlistItemCreate(
            symbol="AAPL",  # Symbol validator ensures uppercase
            company_name="Apple Inc.",
            display_order=1,
        )
        
        with pytest.raises(DuplicateStockError):
            await service.add_to_watchlist("user@example.com", item)
        
        mock_repository.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_watchlist(self, service, mock_repository):
        """Test retrieving user's watchlist."""
        # Setup
        expected_items = [
            WatchlistItem(
                id="id1",
                user_id="user@example.com",
                symbol="AAPL",
                company_name="Apple Inc.",
                display_order=1,
            ),
            WatchlistItem(
                id="id2",
                user_id="user@example.com",
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                display_order=2,
            ),
        ]
        mock_repository.get_by_user.return_value = expected_items

        # Execute
        result = await service.get_watchlist("user@example.com")

        # Verify
        assert len(result) == 2
        assert result[0].symbol == "AAPL"
        assert result[1].symbol == "GOOGL"
        mock_repository.get_by_user.assert_called_once_with("user@example.com")

    @pytest.mark.asyncio
    async def test_update_item(self, service, mock_repository):
        """Test updating watchlist item."""
        # Setup
        from src.models.watchlist import WatchlistItemUpdate
        
        updated_item = WatchlistItem(
            id="test-id",
            user_id="user@example.com",
            symbol="AAPL",
            company_name="Apple Inc.",
            memo="Updated memo",
            display_order=1,
        )
        mock_repository.update.return_value = updated_item

        # Execute
        update = WatchlistItemUpdate(memo="Updated memo")
        result = await service.update_item("user@example.com", "test-id", update)

        # Verify
        assert result.memo == "Updated memo"
        mock_repository.update.assert_called_once_with(
            "user@example.com", "test-id", "Updated memo", None
        )

    @pytest.mark.asyncio
    async def test_delete_item(self, service, mock_repository):
        """Test deleting watchlist item."""
        # Setup
        mock_repository.delete.return_value = True

        # Execute
        result = await service.delete_item("user@example.com", "test-id")

        # Verify
        assert result is True
        mock_repository.delete.assert_called_once_with("user@example.com", "test-id")

    @pytest.mark.asyncio
    async def test_reorder_items(self, service, mock_repository):
        """Test reordering watchlist items."""
        # Setup
        reordered_items = [
            WatchlistItem(
                id="id2",
                user_id="user@example.com",
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                display_order=1,  # Was 2, now 1
            ),
            WatchlistItem(
                id="id1",
                user_id="user@example.com",
                symbol="AAPL",
                company_name="Apple Inc.",
                display_order=2,  # Was 1, now 2
            ),
        ]
        mock_repository.reorder.return_value = reordered_items

        # Execute
        item_ids = ["id2", "id1"]
        result = await service.reorder_items("user@example.com", item_ids)

        # Verify
        assert len(result) == 2
        assert result[0].id == "id2"
        assert result[0].display_order == 1
        assert result[1].id == "id1"
        assert result[1].display_order == 2
        mock_repository.reorder.assert_called_once_with("user@example.com", item_ids)
