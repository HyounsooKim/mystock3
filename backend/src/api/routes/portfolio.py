"""
Portfolio API Router

Endpoints for portfolio management (CRUD operations with P/L calculations).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies.auth import get_current_user
from ...models.portfolio import PortfolioEntryCreate, PortfolioEntryResponse, PortfolioEntryUpdate
from ...services.portfolio_service import PortfolioService
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def get_portfolio_service() -> PortfolioService:
    """Dependency to get portfolio service instance"""
    return PortfolioService()


@router.get("", response_model=List[PortfolioEntryResponse], status_code=status.HTTP_200_OK)
async def get_portfolio(
    category: Optional[str] = Query(None, description="Filter by category: 장기, 단기, 정찰병"),
    current_user: dict = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Get user's portfolio with profit/loss calculations

    **Query Parameters:**
    - `category` (optional): Filter by investment category

    **Returns:**
    - List of portfolio entries with current price, market value, and P/L metrics
    """
    try:
        entries = await portfolio_service.get_portfolio_with_calculations(current_user["user_id"], category)
        logger.info(f"User {current_user['user_id']} retrieved {len(entries)} portfolio entries")
        return entries
    except Exception as e:
        logger.error(f"Failed to get portfolio for user {current_user['user_id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="포트폴리오 조회에 실패했습니다"
        )


@router.post("", response_model=PortfolioEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_to_portfolio(
    entry_data: PortfolioEntryCreate,
    current_user: dict = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Add stock to portfolio

    **Request Body:**
    - `symbol`: Stock ticker symbol (uppercase, 1-5 chars)
    - `company_name`: Company full name (max 100 chars)
    - `category`: Investment category (장기, 단기, 정찰병)
    - `purchase_price`: Average purchase price per share (positive, max 2 decimals)
    - `quantity`: Number of shares (positive integer)

    **Validations:**
    - Maximum 10 entries per user
    - No duplicate symbol in same category

    **Returns:**
    - Created portfolio entry with P/L calculations
    """
    try:
        # Create entry with validation
        entry = await portfolio_service.create_portfolio_entry(current_user["user_id"], entry_data)

        # Get entry with P/L calculations
        entry_with_calc = await portfolio_service.get_entry_with_calculations(entry.entry_id, current_user["user_id"])

        logger.info(f"User {current_user['user_id']} added {entry_data.symbol} to portfolio")
        return entry_with_calc

    except ValueError as e:
        # Business rule violations (duplicate, limit reached)
        logger.warning(f"Portfolio validation failed for user {current_user['user_id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add to portfolio for user {current_user['user_id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="포트폴리오 추가에 실패했습니다"
        )


@router.get("/{entry_id}", response_model=PortfolioEntryResponse, status_code=status.HTTP_200_OK)
async def get_portfolio_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Get single portfolio entry with P/L calculations

    **Path Parameters:**
    - `entry_id`: Portfolio entry identifier

    **Returns:**
    - Portfolio entry with current price, market value, and P/L metrics

    **Errors:**
    - 404: Entry not found or doesn't belong to user
    """
    try:
        entry = await portfolio_service.get_entry_with_calculations(entry_id, current_user["user_id"])

        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="포트폴리오 항목을 찾을 수 없습니다")

        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="포트폴리오 조회에 실패했습니다"
        )


@router.patch("/{entry_id}", response_model=PortfolioEntryResponse, status_code=status.HTTP_200_OK)
async def update_portfolio_entry(
    entry_id: str,
    update_data: PortfolioEntryUpdate,
    current_user: dict = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Update portfolio entry (purchase price and/or quantity)

    **Path Parameters:**
    - `entry_id`: Portfolio entry identifier

    **Request Body:**
    - `purchase_price` (optional): Updated purchase price
    - `quantity` (optional): Updated quantity

    **Returns:**
    - Updated portfolio entry with recalculated P/L metrics

    **Errors:**
    - 404: Entry not found or doesn't belong to user
    """
    try:
        # Update entry
        updated_entry = await portfolio_service.update_portfolio_entry(entry_id, current_user["user_id"], update_data)

        if not updated_entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="포트폴리오 항목을 찾을 수 없습니다")

        # Get entry with updated P/L calculations
        entry_with_calc = await portfolio_service.get_entry_with_calculations(entry_id, current_user["user_id"])

        logger.info(f"User {current_user['user_id']} updated portfolio entry {entry_id}")
        return entry_with_calc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update portfolio entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="포트폴리오 수정에 실패했습니다"
        )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Delete portfolio entry

    **Path Parameters:**
    - `entry_id`: Portfolio entry identifier

    **Returns:**
    - 204 No Content on success

    **Errors:**
    - 404: Entry not found or doesn't belong to user
    """
    try:
        deleted = await portfolio_service.delete_portfolio_entry(entry_id, current_user["user_id"])

        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="포트폴리오 항목을 찾을 수 없습니다")

        logger.info(f"User {current_user['user_id']} deleted portfolio entry {entry_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete portfolio entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="포트폴리오 삭제에 실패했습니다"
        )
