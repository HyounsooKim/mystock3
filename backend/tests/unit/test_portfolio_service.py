"""Unit tests for portfolio service business logic."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from src.models.portfolio import PortfolioEntry, PortfolioEntryCreate, PortfolioEntryUpdate
from src.services.portfolio_service import PortfolioService


class TestPortfolioService:
    """Test suite for portfolio service."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock portfolio repository."""
        repository = Mock()
        repository.get_by_symbol_and_category = AsyncMock()
        repository.count_by_user = AsyncMock()
        repository.create = AsyncMock()
        repository.get_all_by_user = AsyncMock()
        repository.get_by_id = AsyncMock()
        repository.update = AsyncMock()
        repository.delete = AsyncMock()
        return repository

    @pytest.fixture
    def mock_stock_client(self):
        """Create mock Alpha Vantage client."""
        client = Mock()
        client.get_stock_quote = AsyncMock()
        return client

    @pytest.fixture
    def service(self, mock_repository, mock_stock_client):
        """Create portfolio service with mocked dependencies."""
        service = PortfolioService()
        service.repository = mock_repository
        service.stock_client = mock_stock_client
        return service

    @pytest.fixture
    def sample_entry(self):
        """Create a sample portfolio entry."""
        return PortfolioEntry(
            entry_id="test-entry-id",
            user_id="test@example.com",
            symbol="AAPL",
            company_name="Apple Inc.",
            category="장기",
            purchase_price=150.00,
            quantity=10,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    # T158: Profit/Loss Calculation Tests
    @pytest.mark.asyncio
    async def test_calculate_profit_loss_with_gain(self, service, sample_entry, mock_stock_client):
        """Test P/L calculation with positive gain (FR-019)."""
        # Setup: Current price higher than purchase price
        mock_stock_client.get_stock_quote.return_value = {"price": 175.50}

        # Execute
        result = await service.calculate_profit_loss(sample_entry)

        # Verify
        assert result["current_price"] == 175.50
        assert result["market_value"] == 1755.00  # 175.50 * 10
        assert result["profit_loss"] == 255.00  # (175.50 - 150.00) * 10
        assert result["profit_loss_percent"] == 17.0  # ((175.50 - 150.00) / 150.00) * 100
        mock_stock_client.get_stock_quote.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_calculate_profit_loss_with_loss(self, service, sample_entry, mock_stock_client):
        """Test P/L calculation with negative loss (FR-019)."""
        # Setup: Current price lower than purchase price
        mock_stock_client.get_stock_quote.return_value = {"price": 135.75}

        # Execute
        result = await service.calculate_profit_loss(sample_entry)

        # Verify
        assert result["current_price"] == 135.75
        assert result["market_value"] == 1357.50  # 135.75 * 10
        assert result["profit_loss"] == -142.50  # (135.75 - 150.00) * 10
        assert result["profit_loss_percent"] == -9.5  # ((135.75 - 150.00) / 150.00) * 100

    @pytest.mark.asyncio
    async def test_calculate_profit_loss_with_provided_price(self, service, sample_entry, mock_stock_client):
        """Test P/L calculation with pre-provided current price."""
        # Setup: Provide current price directly
        current_price = 160.00

        # Execute
        result = await service.calculate_profit_loss(sample_entry, current_price=current_price)

        # Verify
        assert result["current_price"] == 160.00
        assert result["market_value"] == 1600.00
        assert result["profit_loss"] == 100.00
        assert result["profit_loss_percent"] == 6.67  # Rounded to 2 decimals
        mock_stock_client.get_stock_quote.assert_not_called()  # Should not fetch

    @pytest.mark.asyncio
    async def test_calculate_profit_loss_api_failure(self, service, sample_entry, mock_stock_client):
        """Test P/L calculation when Alpha Vantage API fails."""
        # Setup: API call raises exception
        mock_stock_client.get_stock_quote.side_effect = Exception("API rate limit exceeded")

        # Execute
        result = await service.calculate_profit_loss(sample_entry)

        # Verify: All values should be None
        assert result["current_price"] is None
        assert result["market_value"] is None
        assert result["profit_loss"] is None
        assert result["profit_loss_percent"] is None

    @pytest.mark.asyncio
    async def test_calculate_profit_loss_zero_percent(self, service, sample_entry, mock_stock_client):
        """Test P/L calculation with no change (0% profit/loss)."""
        # Setup: Current price equals purchase price
        mock_stock_client.get_stock_quote.return_value = {"price": 150.00}

        # Execute
        result = await service.calculate_profit_loss(sample_entry)

        # Verify
        assert result["current_price"] == 150.00
        assert result["market_value"] == 1500.00
        assert result["profit_loss"] == 0.0
        assert result["profit_loss_percent"] == 0.0

    # T159: 10-Item Limit Check Tests
    @pytest.mark.asyncio
    async def test_check_portfolio_limit_not_reached(self, service, mock_repository):
        """Test portfolio limit check when under limit (FR-020)."""
        # Setup: User has 5 entries
        mock_repository.count_by_user.return_value = 5

        # Execute
        is_limit_reached = await service.check_portfolio_limit("test@example.com")

        # Verify
        assert is_limit_reached is False
        mock_repository.count_by_user.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_check_portfolio_limit_exactly_at_limit(self, service, mock_repository):
        """Test portfolio limit check when exactly at 10 entries (FR-020)."""
        # Setup: User has exactly MAX_PORTFOLIO_ENTRIES (10)
        mock_repository.count_by_user.return_value = 10

        # Execute
        is_limit_reached = await service.check_portfolio_limit("test@example.com")

        # Verify
        assert is_limit_reached is True

    @pytest.mark.asyncio
    async def test_check_portfolio_limit_exceeded(self, service, mock_repository):
        """Test portfolio limit check when over limit."""
        # Setup: User has more than MAX_PORTFOLIO_ENTRIES
        mock_repository.count_by_user.return_value = 12

        # Execute
        is_limit_reached = await service.check_portfolio_limit("test@example.com")

        # Verify
        assert is_limit_reached is True

    @pytest.mark.asyncio
    async def test_create_entry_blocked_by_limit(self, service, mock_repository):
        """Test creating entry fails when portfolio limit reached (FR-020)."""
        # Setup: User at limit
        mock_repository.count_by_user.return_value = 10
        mock_repository.get_by_symbol_and_category.return_value = None

        # Execute & Verify
        entry_data = PortfolioEntryCreate(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            category="장기",
            purchase_price=300.00,
            quantity=5,
        )

        with pytest.raises(ValueError) as exc_info:
            await service.create_portfolio_entry("test@example.com", entry_data)

        assert "최대 10개 종목까지 등록 가능" in str(exc_info.value)
        mock_repository.create.assert_not_called()

    # T160: Duplicate Detection Tests
    @pytest.mark.asyncio
    async def test_check_duplicate_exists(self, service, mock_repository, sample_entry):
        """Test duplicate detection when stock exists in category (FR-017-1)."""
        # Setup: Stock already exists in category
        mock_repository.get_by_symbol_and_category.return_value = sample_entry

        # Execute
        is_duplicate = await service.check_duplicate_in_category("test@example.com", "AAPL", "장기")

        # Verify
        assert is_duplicate is True
        mock_repository.get_by_symbol_and_category.assert_called_once_with(
            "test@example.com", "AAPL", "장기"
        )

    @pytest.mark.asyncio
    async def test_check_duplicate_not_exists(self, service, mock_repository):
        """Test duplicate detection when stock does not exist in category."""
        # Setup: No existing entry
        mock_repository.get_by_symbol_and_category.return_value = None

        # Execute
        is_duplicate = await service.check_duplicate_in_category("test@example.com", "GOOGL", "단기")

        # Verify
        assert is_duplicate is False

    @pytest.mark.asyncio
    async def test_check_duplicate_different_category(self, service, mock_repository):
        """Test duplicate detection allows same stock in different category (FR-017-1)."""
        # Setup: Stock exists in "장기" but not in "단기"
        mock_repository.get_by_symbol_and_category.return_value = None

        # Execute: Check for "단기" category
        is_duplicate = await service.check_duplicate_in_category("test@example.com", "AAPL", "단기")

        # Verify: Should not be considered duplicate
        assert is_duplicate is False
        mock_repository.get_by_symbol_and_category.assert_called_once_with(
            "test@example.com", "AAPL", "단기"
        )

    @pytest.mark.asyncio
    async def test_create_entry_blocked_by_duplicate(self, service, mock_repository, sample_entry):
        """Test creating entry fails when duplicate in same category (FR-017-1)."""
        # Setup: Duplicate exists
        mock_repository.get_by_symbol_and_category.return_value = sample_entry
        mock_repository.count_by_user.return_value = 5  # Under limit

        # Execute & Verify
        entry_data = PortfolioEntryCreate(
            symbol="AAPL",
            company_name="Apple Inc.",
            category="장기",
            purchase_price=155.00,
            quantity=8,
        )

        with pytest.raises(ValueError) as exc_info:
            await service.create_portfolio_entry("test@example.com", entry_data)

        assert "이미 해당 카테고리에 등록된 종목입니다" in str(exc_info.value)
        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_entry_success(self, service, mock_repository, sample_entry):
        """Test successfully creating portfolio entry."""
        # Setup: No duplicate, under limit
        mock_repository.get_by_symbol_and_category.return_value = None
        mock_repository.count_by_user.return_value = 5
        mock_repository.create.return_value = sample_entry

        # Execute
        entry_data = PortfolioEntryCreate(
            symbol="AAPL",
            company_name="Apple Inc.",
            category="장기",
            purchase_price=150.00,
            quantity=10,
        )
        result = await service.create_portfolio_entry("test@example.com", entry_data)

        # Verify
        assert result.symbol == "AAPL"
        assert result.category == "장기"
        mock_repository.get_by_symbol_and_category.assert_called_once()
        mock_repository.count_by_user.assert_called_once()
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_portfolio_with_calculations(
        self, service, mock_repository, mock_stock_client, sample_entry
    ):
        """Test retrieving portfolio with P/L calculations."""
        # Setup
        mock_repository.get_all_by_user.return_value = [sample_entry]
        mock_stock_client.get_stock_quote.return_value = {"price": 160.00}

        # Execute
        results = await service.get_portfolio_with_calculations("test@example.com")

        # Verify
        assert len(results) == 1
        assert results[0].symbol == "AAPL"
        assert results[0].current_price == 160.00
        assert results[0].market_value == 1600.00
        assert results[0].profit_loss == 100.00
        mock_repository.get_all_by_user.assert_called_once_with("test@example.com", None)

    @pytest.mark.asyncio
    async def test_get_portfolio_with_category_filter(
        self, service, mock_repository, mock_stock_client, sample_entry
    ):
        """Test retrieving portfolio filtered by category."""
        # Setup
        mock_repository.get_all_by_user.return_value = [sample_entry]
        mock_stock_client.get_stock_quote.return_value = {"price": 160.00}

        # Execute
        results = await service.get_portfolio_with_calculations("test@example.com", category="장기")

        # Verify
        assert len(results) == 1
        assert results[0].category == "장기"
        mock_repository.get_all_by_user.assert_called_once_with("test@example.com", "장기")

    @pytest.mark.asyncio
    async def test_update_portfolio_entry(self, service, mock_repository, sample_entry):
        """Test updating portfolio entry."""
        # Setup
        updated_entry = PortfolioEntry(
            **{**sample_entry.dict(), "purchase_price": 155.00, "quantity": 12}
        )
        mock_repository.update.return_value = updated_entry

        # Execute
        update_data = PortfolioEntryUpdate(purchase_price=155.00, quantity=12)
        result = await service.update_portfolio_entry("test-entry-id", "test@example.com", update_data)

        # Verify
        assert result.purchase_price == 155.00
        assert result.quantity == 12
        mock_repository.update.assert_called_once_with("test-entry-id", "test@example.com", update_data)

    @pytest.mark.asyncio
    async def test_delete_portfolio_entry(self, service, mock_repository):
        """Test deleting portfolio entry."""
        # Setup
        mock_repository.delete.return_value = True

        # Execute
        result = await service.delete_portfolio_entry("test-entry-id", "test@example.com")

        # Verify
        assert result is True
        mock_repository.delete.assert_called_once_with("test-entry-id", "test@example.com")
