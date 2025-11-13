"""
Portfolio Entry Repository

Handles CRUD operations for portfolio entries in Cosmos DB.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from azure.cosmos import exceptions

from ..database.cosmos_client import get_container
from ..models.portfolio import PortfolioEntry, PortfolioEntryCreate, PortfolioEntryUpdate, PortfolioCategory
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PortfolioRepository:
    """Repository for portfolio entry CRUD operations."""

    def __init__(self):
        """Initialize with Cosmos DB container."""
        self.container = get_container("portfolio_entries")

    async def create(self, user_id: str, entry_data: PortfolioEntryCreate) -> PortfolioEntry:
        """
        Create a new portfolio entry

        Args:
            user_id: Owner's email (partition key)
            entry_data: Portfolio entry details

        Returns:
            Created portfolio entry

        Raises:
            Exception: If creation fails
        """
        entry_dict = {
            "id": str(uuid4()),
            "entry_id": str(uuid4()),
            "type": "portfolio_entry",
            "schema_version": "1.0",
            "user_id": user_id,
            "symbol": entry_data.symbol,
            "company_name": entry_data.company_name,
            "category": entry_data.category,
            "purchase_price": entry_data.purchase_price,
            "quantity": entry_data.quantity,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            created_item = self.container.create_item(body=entry_dict)
            logger.info(f"Created portfolio entry: {created_item['entry_id']} for user: {user_id}")
            return PortfolioEntry(**created_item)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create portfolio entry for user {user_id}: {e.message}")
            raise

    async def get_by_id(self, entry_id: str, user_id: str) -> Optional[PortfolioEntry]:
        """
        Get portfolio entry by ID

        Args:
            entry_id: Portfolio entry identifier
            user_id: Owner's email (partition key)

        Returns:
            Portfolio entry or None if not found
        """
        query = "SELECT * FROM c WHERE c.entry_id = @entry_id AND c.user_id = @user_id AND c.type = 'portfolio_entry'"
        parameters = [
            {"name": "@entry_id", "value": entry_id},
            {"name": "@user_id", "value": user_id},
        ]

        try:
            items = list(
                self.container.query_items(
                    query=query, parameters=parameters, partition_key=user_id, enable_cross_partition_query=False
                )
            )
            if items:
                return PortfolioEntry(**items[0])
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get portfolio entry {entry_id}: {e.message}")
            raise

    async def get_all_by_user(self, user_id: str, category: Optional[str] = None) -> List[PortfolioEntry]:
        """
        Get all portfolio entries for a user, optionally filtered by category

        Args:
            user_id: Owner's email (partition key)
            category: Optional category filter (장기, 단기, 정찰병)

        Returns:
            List of portfolio entries
        """
        if category:
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.category = @category AND c.type = 'portfolio_entry'"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@category", "value": category},
            ]
        else:
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.type = 'portfolio_entry'"
            parameters = [{"name": "@user_id", "value": user_id}]

        try:
            items = list(
                self.container.query_items(
                    query=query, parameters=parameters, partition_key=user_id, enable_cross_partition_query=False
                )
            )
            logger.info(f"Retrieved {len(items)} portfolio entries for user: {user_id}")
            return [PortfolioEntry(**item) for item in items]
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get portfolio entries for user {user_id}: {e.message}")
            raise

    async def get_by_symbol_and_category(self, user_id: str, symbol: str, category: str) -> Optional[PortfolioEntry]:
        """
        Get portfolio entry by symbol and category (for duplicate checking)

        Args:
            user_id: Owner's email
            symbol: Stock ticker symbol
            category: Investment category

        Returns:
            Portfolio entry or None if not found
        """
        query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.symbol = @symbol AND c.category = @category AND c.type = 'portfolio_entry'"
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@symbol", "value": symbol},
            {"name": "@category", "value": category},
        ]

        try:
            items = list(
                self.container.query_items(
                    query=query, parameters=parameters, partition_key=user_id, enable_cross_partition_query=False
                )
            )
            if items:
                return PortfolioEntry(**items[0])
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to check duplicate portfolio entry: {e.message}")
            raise

    async def count_by_user(self, user_id: str) -> int:
        """
        Count total portfolio entries for a user (for 10-item limit check)

        Args:
            user_id: Owner's email

        Returns:
            Number of portfolio entries
        """
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.user_id = @user_id AND c.type = 'portfolio_entry'"
        parameters = [{"name": "@user_id", "value": user_id}]

        try:
            items = list(
                self.container.query_items(
                    query=query, parameters=parameters, partition_key=user_id, enable_cross_partition_query=False
                )
            )
            count = items[0] if items else 0
            logger.info(f"User {user_id} has {count} portfolio entries")
            return count
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to count portfolio entries for user {user_id}: {e.message}")
            raise

    async def update(self, entry_id: str, user_id: str, update_data: PortfolioEntryUpdate) -> Optional[PortfolioEntry]:
        """
        Update portfolio entry

        Args:
            entry_id: Portfolio entry identifier
            user_id: Owner's email (partition key)
            update_data: Fields to update

        Returns:
            Updated portfolio entry or None if not found
        """
        # Query to get the full document including Cosmos DB 'id' field
        query = "SELECT * FROM c WHERE c.entry_id = @entry_id AND c.user_id = @user_id AND c.type = 'portfolio_entry'"
        parameters = [
            {"name": "@entry_id", "value": entry_id},
            {"name": "@user_id", "value": user_id},
        ]

        try:
            items = list(
                self.container.query_items(
                    query=query, parameters=parameters, partition_key=user_id, enable_cross_partition_query=False
                )
            )
            
            if not items:
                logger.warning(f"Portfolio entry {entry_id} not found for user {user_id}")
                return None
            
            # Get the raw document with 'id' field
            update_dict = items[0]
            
            # Verify 'id' field exists
            if "id" not in update_dict:
                logger.error(f"Document missing 'id' field. Document keys: {list(update_dict.keys())}")
                raise ValueError("Document missing required 'id' field")
            
            # Update only the fields that are provided
            if update_data.purchase_price is not None:
                update_dict["purchase_price"] = update_data.purchase_price
            if update_data.quantity is not None:
                update_dict["quantity"] = update_data.quantity
            
            update_dict["updated_at"] = datetime.utcnow().isoformat()

            # Replace the entire item using the document 'id'
            updated_item = self.container.replace_item(item=update_dict["id"], body=update_dict)
            logger.info(f"Updated portfolio entry: {entry_id}")
            return PortfolioEntry(**updated_item)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update portfolio entry {entry_id}: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating portfolio entry {entry_id}: {str(e)}", exc_info=True)
            raise

    async def delete(self, entry_id: str, user_id: str) -> bool:
        """
        Delete portfolio entry

        Args:
            entry_id: Portfolio entry identifier
            user_id: Owner's email (partition key)

        Returns:
            True if deleted, False if not found
        """
        # Get existing entry to find the document id
        existing_entry = await self.get_by_id(entry_id, user_id)
        if not existing_entry:
            return False

        try:
            # Get the document id from the entry
            query = "SELECT c.id FROM c WHERE c.entry_id = @entry_id AND c.user_id = @user_id"
            parameters = [
                {"name": "@entry_id", "value": entry_id},
                {"name": "@user_id", "value": user_id},
            ]
            items = list(
                self.container.query_items(
                    query=query, parameters=parameters, partition_key=user_id, enable_cross_partition_query=False
                )
            )
            
            if items:
                doc_id = items[0]["id"]
                self.container.delete_item(item=doc_id, partition_key=user_id)
                logger.info(f"Deleted portfolio entry: {entry_id}")
                return True
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to delete portfolio entry {entry_id}: {e.message}")
            raise
