"""
Database initialization script.
Creates Cosmos DB containers with proper partition keys and indexing policies.
"""

from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError
from ..utils.logging import get_logger
from ..database.cosmos_client import get_cosmos_client
from ..config import settings

logger = get_logger(__name__)


def create_users_container(database):
    """Create users container with email as partition key."""
    container_name = "users"
    partition_key = PartitionKey(path="/id")
    
    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/id/?"},
            {"path": "/email/?"}
        ],
        "excludedPaths": [
            {"path": "/password_hash/?"},
            {"path": "/_etag/?"}
        ]
    }
    
    try:
        container = database.create_container(
            id=container_name,
            partition_key=partition_key,
            indexing_policy=indexing_policy
        )
        logger.info(f"Created container: {container_name}")
        return container
    except CosmosResourceExistsError:
        logger.info(f"Container already exists: {container_name}")
        return database.get_container_client(container_name)


def create_watchlist_items_container(database):
    """Create watchlist_items container with user_id as partition key."""
    container_name = "watchlist_items"
    partition_key = PartitionKey(path="/user_id")
    
    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/user_id/?"},
            {"path": "/symbol/?"},
            {"path": "/display_order/?"}
        ],
        "excludedPaths": [
            {"path": "/memo/?"}
        ]
    }
    
    try:
        container = database.create_container(
            id=container_name,
            partition_key=partition_key,
            indexing_policy=indexing_policy
        )
        logger.info(f"Created container: {container_name}")
        return container
    except CosmosResourceExistsError:
        logger.info(f"Container already exists: {container_name}")
        return database.get_container_client(container_name)


def create_portfolio_entries_container(database):
    """Create portfolio_entries container with user_id as partition key."""
    container_name = "portfolio_entries"
    partition_key = PartitionKey(path="/user_id")
    
    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/user_id/?"},
            {"path": "/symbol/?"},
            {"path": "/category/?"}
        ],
        "excludedPaths": []
    }
    
    try:
        container = database.create_container(
            id=container_name,
            partition_key=partition_key,
            indexing_policy=indexing_policy
        )
        logger.info(f"Created container: {container_name}")
        return container
    except CosmosResourceExistsError:
        logger.info(f"Container already exists: {container_name}")
        return database.get_container_client(container_name)


def initialize_database():
    """Initialize Cosmos DB database and create all containers."""
    logger.info("Starting database initialization")
    
    client = get_cosmos_client()
    
    # Create database if it doesn't exist
    try:
        database = client.create_database(id=settings.cosmos_database_name)
        logger.info(f"Created database: {settings.cosmos_database_name}")
    except CosmosResourceExistsError:
        logger.info(f"Database already exists: {settings.cosmos_database_name}")
        database = client.get_database_client(settings.cosmos_database_name)
    
    # Create containers
    create_users_container(database)
    create_watchlist_items_container(database)
    create_portfolio_entries_container(database)
    
    logger.info("Database initialization completed successfully")


if __name__ == "__main__":
    initialize_database()
