"""Watchlist API endpoints.

This module provides REST API endpoints for managing user watchlists.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.auth import get_current_user
from src.models.errors import ErrorResponse
from src.models.watchlist import (
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistItemReorder,
    WatchlistItemUpdate,
    WatchlistItemWithQuote,
)
from src.services.watchlist_service import DuplicateStockError, WatchlistService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def get_watchlist_service() -> WatchlistService:
    """Dependency to get watchlist service instance."""
    return WatchlistService()


@router.get(
    "",
    response_model=List[WatchlistItemWithQuote],
    summary="Get user's watchlist",
    description="Retrieve all watchlist items with current stock quotes",
    responses={
        200: {"description": "Watchlist retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_watchlist(
    current_user: Dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """Get user's complete watchlist with live stock data.

    Args:
        current_user: Authenticated user from JWT token
        service: Watchlist service instance

    Returns:
        List of watchlist items with current prices
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting watchlist for user: {user_id}")

        # For now, return items without quotes (stock service integration pending)
        items = await service.get_watchlist(user_id)
        
        # Convert to WatchlistItemWithQuote (prices will be None for now)
        return [WatchlistItemWithQuote(**item.model_dump()) for item in items]

    except Exception as e:
        logger.error(f"Error getting watchlist for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve watchlist",
        )


@router.post(
    "",
    response_model=WatchlistItem,
    status_code=status.HTTP_201_CREATED,
    summary="Add stock to watchlist",
    description="Add a new stock to the user's watchlist",
    responses={
        201: {"description": "Stock added successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input or duplicate stock"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def add_to_watchlist(
    item: WatchlistItemCreate,
    current_user: Dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """Add a stock to user's watchlist.

    Args:
        item: Watchlist item data
        current_user: Authenticated user from JWT token
        service: Watchlist service instance

    Returns:
        Created watchlist item

    Raises:
        HTTPException: 400 if stock already exists in watchlist
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Adding {item.symbol} to watchlist for user: {user_id}")

        created = await service.add_to_watchlist(user_id, item)
        logger.info(
            f"Successfully added {item.symbol} to watchlist for user: {user_id}"
        )
        return created

    except DuplicateStockError as e:
        logger.warning(f"Duplicate stock error for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 관심종목에 추가된 종목입니다",  # Korean: "Already added to watchlist"
        )
    except Exception as e:
        logger.error(f"Error adding to watchlist for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add stock to watchlist",
        )


@router.patch(
    "/{item_id}",
    response_model=WatchlistItem,
    summary="Update watchlist item",
    description="Update memo or display order of a watchlist item",
    responses={
        200: {"description": "Item updated successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Item not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_watchlist_item(
    item_id: str,
    update: WatchlistItemUpdate,
    current_user: Dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """Update a watchlist item.

    Args:
        item_id: Watchlist item ID
        update: Fields to update
        current_user: Authenticated user from JWT token
        service: Watchlist service instance

    Returns:
        Updated watchlist item

    Raises:
        HTTPException: 404 if item not found or doesn't belong to user
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Updating watchlist item {item_id} for user: {user_id}")

        updated = await service.update_item(user_id, item_id, update)
        
        if not updated:
            logger.warning(f"Watchlist item {item_id} not found for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist item not found",
            )

        logger.info(f"Successfully updated watchlist item {item_id} for user: {user_id}")
        return updated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating watchlist item for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update watchlist item",
        )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete watchlist item",
    description="Remove a stock from the watchlist",
    responses={
        204: {"description": "Item deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Item not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_watchlist_item(
    item_id: str,
    current_user: Dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """Delete a watchlist item.

    Args:
        item_id: Watchlist item ID
        current_user: Authenticated user from JWT token
        service: Watchlist service instance

    Raises:
        HTTPException: 404 if item not found or doesn't belong to user
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Deleting watchlist item {item_id} for user: {user_id}")

        deleted = await service.delete_item(user_id, item_id)
        
        if not deleted:
            logger.warning(f"Watchlist item {item_id} not found for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist item not found",
            )

        logger.info(f"Successfully deleted watchlist item {item_id} for user: {user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting watchlist item for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete watchlist item",
        )


@router.post(
    "/reorder",
    response_model=List[WatchlistItem],
    summary="Reorder watchlist items",
    description="Update display order of multiple watchlist items",
    responses={
        200: {"description": "Items reordered successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def reorder_watchlist(
    reorder: WatchlistItemReorder,
    current_user: Dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """Reorder watchlist items via drag-and-drop.

    Args:
        reorder: Ordered list of item IDs
        current_user: Authenticated user from JWT token
        service: Watchlist service instance

    Returns:
        List of updated watchlist items
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Reordering watchlist for user: {user_id}")

        updated_items = await service.reorder_items(user_id, reorder.item_ids)
        logger.info(
            f"Successfully reordered {len(updated_items)} items for user: {user_id}"
        )
        return updated_items

    except Exception as e:
        logger.error(f"Error reordering watchlist for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder watchlist",
        )
