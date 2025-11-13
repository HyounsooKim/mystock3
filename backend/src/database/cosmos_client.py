"""
Cosmos DB client wrapper with connection pooling.
Provides singleton client instance for database operations.
"""

from typing import Optional
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.exceptions import CosmosHttpResponseError
from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Global client instance
_cosmos_client: Optional[CosmosClient] = None
_database: Optional[DatabaseProxy] = None


def get_cosmos_client() -> CosmosClient:
    """
    Get or create Cosmos DB client instance (singleton pattern).
    
    Returns:
        CosmosClient instance
    """
    global _cosmos_client
    
    if _cosmos_client is None:
        logger.info(
            "Initializing Cosmos DB client",
            extra={"extra_fields": {"endpoint": settings.cosmos_endpoint}}
        )
        _cosmos_client = CosmosClient(
            url=settings.cosmos_endpoint,
            credential=settings.cosmos_key
        )
    
    return _cosmos_client


def get_database() -> DatabaseProxy:
    """
    Get or create database instance.
    
    Returns:
        DatabaseProxy instance
    """
    global _database
    
    if _database is None:
        client = get_cosmos_client()
        _database = client.get_database_client(settings.cosmos_database_name)
        logger.info(
            "Connected to Cosmos DB database",
            extra={"extra_fields": {"database": settings.cosmos_database_name}}
        )
    
    return _database


def get_container(container_name: str) -> ContainerProxy:
    """
    Get a container client.
    
    Args:
        container_name: Name of the container
    
    Returns:
        ContainerProxy instance
    """
    database = get_database()
    return database.get_container_client(container_name)


async def close_cosmos_client() -> None:
    """Close Cosmos DB client connection."""
    global _cosmos_client, _database
    
    if _cosmos_client is not None:
        logger.info("Closing Cosmos DB client")
        _cosmos_client = None
        _database = None
