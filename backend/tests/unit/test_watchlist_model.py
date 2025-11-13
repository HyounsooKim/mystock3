"""Unit tests for watchlist model validation."""

import pytest
from pydantic import ValidationError

from src.models.watchlist import WatchlistItem, WatchlistItemCreate, WatchlistItemUpdate


class TestWatchlistModel:
    """Test suite for watchlist Pydantic models."""

    def test_watchlist_item_create_valid(self):
        """Test creating a valid watchlist item."""
        item = WatchlistItemCreate(
            symbol="AAPL",
            company_name="Apple Inc.",
            memo="Good buy opportunity",
            display_order=1,
        )
        assert item.symbol == "AAPL"
        assert item.company_name == "Apple Inc."
        assert item.memo == "Good buy opportunity"
        assert item.display_order == 1

    def test_watchlist_item_memo_max_50_chars(self):
        """Test memo field enforces 50 character limit (FR-010)."""
        # 50 characters - should pass
        valid_memo = "a" * 50
        item = WatchlistItemCreate(
            symbol="AAPL",
            company_name="Apple Inc.",
            memo=valid_memo,
            display_order=1,
        )
        assert len(item.memo) == 50

    def test_watchlist_item_memo_exceeds_50_chars(self):
        """Test memo validation fails when exceeding 50 characters."""
        # 51 characters - should fail
        invalid_memo = "a" * 51
        with pytest.raises(ValidationError) as exc_info:
            WatchlistItemCreate(
                symbol="AAPL",
                company_name="Apple Inc.",
                memo=invalid_memo,
                display_order=1,
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("memo",) and "50" in str(error["msg"])
            for error in errors
        )

    def test_watchlist_item_memo_optional(self):
        """Test memo field is optional and defaults to empty string."""
        item = WatchlistItemCreate(
            symbol="AAPL", company_name="Apple Inc.", display_order=1
        )
        assert item.memo == ""

    def test_watchlist_item_symbol_uppercase_validation(self):
        """Test symbol must be uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            WatchlistItemCreate(
                symbol="aapl",  # lowercase
                company_name="Apple Inc.",
                display_order=1,
            )
        
        errors = exc_info.value.errors()
        assert any("uppercase" in str(error["msg"]).lower() for error in errors)

    def test_watchlist_item_symbol_length_validation(self):
        """Test symbol must be 1-5 characters."""
        # Too long (6 chars)
        with pytest.raises(ValidationError):
            WatchlistItemCreate(
                symbol="ABCDEF",
                company_name="Test Corp",
                display_order=1,
            )
        
        # Valid lengths
        for length in [1, 2, 3, 4, 5]:
            item = WatchlistItemCreate(
                symbol="A" * length,
                company_name="Test Corp",
                display_order=1,
            )
            assert len(item.symbol) == length

    def test_watchlist_item_display_order_positive(self):
        """Test display_order must be positive integer."""
        # Valid positive integers
        for order in [1, 2, 10, 100]:
            item = WatchlistItemCreate(
                symbol="AAPL",
                company_name="Apple Inc.",
                display_order=order,
            )
            assert item.display_order == order
        
        # Invalid: zero
        with pytest.raises(ValidationError):
            WatchlistItemCreate(
                symbol="AAPL",
                company_name="Apple Inc.",
                display_order=0,
            )
        
        # Invalid: negative
        with pytest.raises(ValidationError):
            WatchlistItemCreate(
                symbol="AAPL",
                company_name="Apple Inc.",
                display_order=-1,
            )

    def test_watchlist_item_update_partial(self):
        """Test partial update schema."""
        # Can update just memo
        update = WatchlistItemUpdate(memo="New memo")
        assert update.memo == "New memo"
        assert update.display_order is None
        
        # Can update just display_order
        update = WatchlistItemUpdate(display_order=5)
        assert update.memo is None
        assert update.display_order == 5
        
        # Can update both
        update = WatchlistItemUpdate(memo="Both", display_order=10)
        assert update.memo == "Both"
        assert update.display_order == 10

    def test_watchlist_item_update_memo_max_50_chars(self):
        """Test update schema also enforces 50 char memo limit."""
        # Valid
        update = WatchlistItemUpdate(memo="a" * 50)
        assert len(update.memo) == 50
        
        # Invalid
        with pytest.raises(ValidationError):
            WatchlistItemUpdate(memo="a" * 51)

    def test_watchlist_item_company_name_max_100_chars(self):
        """Test company_name field enforces 100 character limit."""
        # 100 characters - should pass
        valid_name = "A" * 100
        item = WatchlistItemCreate(
            symbol="AAPL",
            company_name=valid_name,
            display_order=1,
        )
        assert len(item.company_name) == 100
        
        # 101 characters - should fail
        with pytest.raises(ValidationError):
            WatchlistItemCreate(
                symbol="AAPL",
                company_name="A" * 101,
                display_order=1,
            )

    def test_watchlist_item_full_model_with_database_fields(self):
        """Test complete WatchlistItem model with all database fields."""
        from datetime import datetime
        
        item = WatchlistItem(
            id="test-id-123",
            user_id="user@example.com",
            symbol="TSLA",
            company_name="Tesla, Inc.",
            memo="매수 타이밍 확인",
            display_order=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        assert item.id == "test-id-123"
        assert item.type == "watchlist_item"
        assert item.schema_version == "1.0"
        assert item.user_id == "user@example.com"
        assert item.symbol == "TSLA"
        assert item.company_name == "Tesla, Inc."
        assert item.memo == "매수 타이밍 확인"
        assert item.display_order == 2
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
