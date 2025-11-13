"""Watchlist repository for database operations.

This module provides CRUD operations for watchlist items with user-scoped queries.
"""

from datetime import datetime
from typing import List, Optional

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from src.database.cosmos_client import get_container
from src.models.watchlist import WatchlistItem, WatchlistItemCreate


class WatchlistRepository:
    """Repository for watchlist item database operations."""

    def __init__(self):
        """Initialize repository with Cosmos DB container."""
        self.container = get_container("watchlist_items")

    async def get_by_user(self, user_id: str) -> List[WatchlistItem]:
        """Get all watchlist items for a user, ordered by display_order.

        Args:
            user_id: User's email address

        Returns:
            List of watchlist items ordered by display_order
        """
        query = """
            SELECT * FROM c 
            WHERE c.type = 'watchlist_item' AND c.user_id = @user_id 
            ORDER BY c.display_order ASC
        """
        parameters = [{"name": "@user_id", "value": user_id}]

        items = self.container.query_items(
            query=query, parameters=parameters, partition_key=user_id
        )

        return [WatchlistItem(**item) for item in items]

    async def get_by_id(self, user_id: str, item_id: str) -> Optional[WatchlistItem]:
        """Get a specific watchlist item.

        Args:
            user_id: User's email address
            item_id: Watchlist item ID

        Returns:
            WatchlistItem if found, None otherwise
        """
        try:
            item = self.container.read_item(item=item_id, partition_key=user_id)
            return WatchlistItem(**item)
        except CosmosResourceNotFoundError:
            return None

    async def exists(self, user_id: str, symbol: str) -> bool:
        """Check if a symbol already exists in user's watchlist.

        Args:
            user_id: User's email address
            symbol: Stock ticker symbol

        Returns:
            True if symbol exists, False otherwise
        """
        query = """
            SELECT VALUE COUNT(1) FROM c 
            WHERE c.type = 'watchlist_item' 
            AND c.user_id = @user_id 
            AND c.symbol = @symbol
        """
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@symbol", "value": symbol.upper()},
        ]

        result = list(
            self.container.query_items(
                query=query, parameters=parameters, partition_key=user_id
            )
        )

        return result[0] > 0 if result else False

    async def get_max_display_order(self, user_id: str) -> int:
        """Get the maximum display_order value for a user's watchlist.

        Args:
            user_id: User's email address

        Returns:
            Maximum display_order value, or 0 if watchlist is empty
        """
        query = """
            SELECT VALUE MAX(c.display_order) FROM c 
            WHERE c.type = 'watchlist_item' AND c.user_id = @user_id
        """
        parameters = [{"name": "@user_id", "value": user_id}]

        result = list(
            self.container.query_items(
                query=query, parameters=parameters, partition_key=user_id
            )
        )

        return result[0] if result and result[0] is not None else 0

    async def create(self, user_id: str, item: WatchlistItemCreate) -> WatchlistItem:
        """Create a new watchlist item.

        Args:
            user_id: User's email address
            item: Watchlist item data

        Returns:
            Created watchlist item
        """
        try:
            # Get next display_order (automatically assign)
            max_order = await self.get_max_display_order(user_id)
            display_order = max_order + 1

            # Create watchlist item
            watchlist_item = WatchlistItem(
                user_id=user_id,
                symbol=item.symbol.upper(),
                company_name=item.company_name,
                memo=item.memo or "",
                display_order=display_order,
            )

            # Convert to dict and store
            item_dict = watchlist_item.model_dump(mode="json")
            
            # Debug logging
            import json
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.info(f"Creating watchlist item: {json.dumps(item_dict, default=str)}")
            
            # Create item - partition key is already in the document body as 'user_id'
            created = self.container.create_item(body=item_dict)
            
            logger.info(f"Cosmos DB response: {json.dumps(created, default=str)}")

            return WatchlistItem(**created)
        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error creating watchlist item: {str(e)}", exc_info=True)
            raise

    async def update(
        self, user_id: str, item_id: str, memo: Optional[str], display_order: Optional[int]
    ) -> Optional[WatchlistItem]:
        """Update a watchlist item.

        Args:
            user_id: User's email address
            item_id: Watchlist item ID
            memo: Updated memo (None to keep existing)
            display_order: Updated display order (None to keep existing)

        Returns:
            Updated watchlist item, or None if not found
        """
        # Get existing item
        existing = await self.get_by_id(user_id, item_id)
        if not existing:
            return None

        # Update fields
        if memo is not None:
            existing.memo = memo
        if display_order is not None:
            existing.display_order = display_order
        existing.updated_at = datetime.utcnow()

        # Save to database (use upsert_item instead of replace_item to avoid partition_key bug)
        item_dict = existing.model_dump(mode="json")
        updated = self.container.upsert_item(body=item_dict)

        return WatchlistItem(**updated)

    async def delete(self, user_id: str, item_id: str) -> bool:
        """Delete a watchlist item.

        Args:
            user_id: User's email address
            item_id: Watchlist item ID

        Returns:
            True if deleted, False if not found
        """
        try:
            self.container.delete_item(item=item_id, partition_key=user_id)
            return True
        except CosmosResourceNotFoundError:
            return False

    async def reorder(self, user_id: str, item_ids: List[str]) -> List[WatchlistItem]:
        """Reorder watchlist items.

        Args:
            user_id: User's email address
            item_ids: Ordered list of item IDs

        Returns:
            List of updated watchlist items
        """
        items = await self.get_by_user(user_id)
        item_map = {item.id: item for item in items}

        updated_items = []
        for new_order, item_id in enumerate(item_ids, start=1):
            if item_id in item_map:
                item = item_map[item_id]  
                item.display_order = new_order
                item.updated_at = datetime.utcnow()

                item_dict = item.model_dump(mode="json")
                updated = self.container.upsert_item(body=item_dict)
                updated_items.append(WatchlistItem(**updated))

        return updated_items
