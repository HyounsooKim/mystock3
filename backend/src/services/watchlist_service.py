"""Watchlist service for business logic.

This module provides business logic for watchlist operations including duplicate detection.
"""

from typing import List, Optional

from src.models.watchlist import (
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemWithQuote,
)
from src.repositories.watchlist_repository import WatchlistRepository
from src.utils.input_sanitizer import InputSanitizer


class DuplicateStockError(Exception):
    """Raised when attempting to add a duplicate stock to watchlist."""

    pass


class WatchlistService:
    """Service for watchlist business logic."""

    def __init__(self, repository: Optional[WatchlistRepository] = None):
        """Initialize service with repository.

        Args:
            repository: Watchlist repository (or creates default)
        """
        self.repository = repository or WatchlistRepository()

    async def get_watchlist(self, user_id: str) -> List[WatchlistItem]:
        """Get user's complete watchlist.

        Args:
            user_id: User's email address

        Returns:
            List of watchlist items ordered by display_order
        """
        return await self.repository.get_by_user(user_id)

    async def get_watchlist_with_quotes(
        self, user_id: str, stock_service
    ) -> List[WatchlistItemWithQuote]:
        """Get watchlist enriched with current stock quotes.

        Args:
            user_id: User's email address
            stock_service: Stock service for fetching quotes

        Returns:
            List of watchlist items with current price data
        """
        items = await self.repository.get_by_user(user_id)
        enriched_items = []

        for item in items:
            try:
                quote = await stock_service.get_quote(item.symbol)
                enriched = WatchlistItemWithQuote(
                    **item.model_dump(),
                    current_price=float(quote.current_price),
                    change=float(quote.change),
                    change_percent=float(quote.change_percent),
                )
                enriched_items.append(enriched)
            except Exception:
                # If quote fetch fails, include item without price data
                enriched_items.append(WatchlistItemWithQuote(**item.model_dump()))

        return enriched_items

    async def add_to_watchlist(
        self, user_id: str, item: WatchlistItemCreate
    ) -> WatchlistItem:
        """Add a stock to user's watchlist.

        Args:
            user_id: User's email address
            item: Watchlist item data

        Returns:
            Created watchlist item

        Raises:
            DuplicateStockError: If symbol already exists in watchlist
        """
        # Sanitize inputs (T187)
        sanitized_symbol = InputSanitizer.sanitize_symbol(item.symbol)
        sanitized_memo = InputSanitizer.sanitize_memo(item.memo) if item.memo else None
        
        # Update item with sanitized values
        item.symbol = sanitized_symbol
        item.memo = sanitized_memo
        
        # Check for duplicate
        if await self.repository.exists(user_id, item.symbol):
            raise DuplicateStockError(f"Symbol {item.symbol} already in watchlist")

        # Create item
        return await self.repository.create(user_id, item)

    async def update_item(
        self, user_id: str, item_id: str, update: WatchlistItemUpdate
    ) -> Optional[WatchlistItem]:
        """Update a watchlist item.

        Args:
            user_id: User's email address
            item_id: Watchlist item ID
            update: Fields to update

        Returns:
            Updated item, or None if not found
        """
        # Sanitize memo if provided (T187)
        if update.memo is not None:
            update.memo = InputSanitizer.sanitize_memo(update.memo)
        
        return await self.repository.update(
            user_id, item_id, update.memo, update.display_order
        )

    async def delete_item(self, user_id: str, item_id: str) -> bool:
        """Delete a watchlist item.

        Args:
            user_id: User's email address
            item_id: Watchlist item ID

        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(user_id, item_id)

    async def reorder_items(
        self, user_id: str, item_ids: List[str]
    ) -> List[WatchlistItem]:
        """Reorder watchlist items.

        Args:
            user_id: User's email address
            item_ids: Ordered list of item IDs

        Returns:
            List of updated items
        """
        return await self.repository.reorder(user_id, item_ids)
