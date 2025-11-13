"""
Portfolio Service

Business logic for portfolio management including limit checks and P/L calculations.
"""

from typing import Dict, List, Optional

from ..models.portfolio import PortfolioEntry, PortfolioEntryCreate, PortfolioEntryResponse, PortfolioEntryUpdate
from ..repositories.portfolio_repository import PortfolioRepository
from ..external.alpha_vantage_client import AlphaVantageClient
from .stock_batch_service import StockBatchService
from ..utils.logging import get_logger
from ..utils.input_sanitizer import InputSanitizer
from ..config import get_settings

logger = get_logger(__name__)


class PortfolioService:
    """Service for portfolio business logic"""

    MAX_PORTFOLIO_ENTRIES = 10

    def __init__(self):
        """Initialize service with repository and stock client"""
        self.repository = PortfolioRepository()
        settings = get_settings()
        self.stock_client = AlphaVantageClient(api_key=settings.alpha_vantage_api_key)
        self.batch_service = StockBatchService(self.stock_client)

    async def check_duplicate_in_category(self, user_id: str, symbol: str, category: str) -> bool:
        """
        Check if stock already exists in the specified category

        Args:
            user_id: Owner's email
            symbol: Stock ticker symbol
            category: Investment category

        Returns:
            True if duplicate exists, False otherwise
        """
        existing_entry = await self.repository.get_by_symbol_and_category(user_id, symbol, category)
        return existing_entry is not None

    async def check_portfolio_limit(self, user_id: str) -> bool:
        """
        Check if user has reached the 10-item portfolio limit

        Args:
            user_id: Owner's email

        Returns:
            True if limit reached, False otherwise
        """
        count = await self.repository.count_by_user(user_id)
        return count >= self.MAX_PORTFOLIO_ENTRIES

    async def calculate_profit_loss(
        self, entry: PortfolioEntry, current_price: Optional[float] = None
    ) -> Dict[str, Optional[float]]:
        """
        Calculate profit/loss metrics for a portfolio entry

        Args:
            entry: Portfolio entry
            current_price: Optional current stock price (fetched if not provided)

        Returns:
            Dictionary with current_price, market_value, profit_loss, profit_loss_percent
        """
        # Fetch current price if not provided
        if current_price is None:
            try:
                stock_quote = await self.stock_client.get_quote(entry.symbol)
                current_price = float(stock_quote.current_price)
            except Exception as e:
                logger.error(f"Failed to fetch current price for {entry.symbol}: {e}")
                return {
                    "current_price": None,
                    "market_value": None,
                    "profit_loss": None,
                    "profit_loss_percent": None,
                }

        if current_price is None:
            return {
                "current_price": None,
                "market_value": None,
                "profit_loss": None,
                "profit_loss_percent": None,
            }

        # Calculate metrics
        market_value = current_price * entry.quantity
        profit_loss = (current_price - entry.purchase_price) * entry.quantity
        profit_loss_percent = ((current_price - entry.purchase_price) / entry.purchase_price) * 100

        return {
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_percent": round(profit_loss_percent, 2),
        }

    async def create_portfolio_entry(self, user_id: str, entry_data: PortfolioEntryCreate) -> PortfolioEntry:
        """
        Create a new portfolio entry with validation

        Args:
            user_id: Owner's email
            entry_data: Portfolio entry details

        Returns:
            Created portfolio entry

        Raises:
            ValueError: If duplicate in category or limit reached
        """
        # Sanitize inputs (T187)
        sanitized_symbol = InputSanitizer.sanitize_symbol(entry_data.symbol)
        sanitized_category = InputSanitizer.sanitize_category(entry_data.category)
        
        # Update entry data with sanitized values
        entry_data.symbol = sanitized_symbol
        entry_data.category = sanitized_category if sanitized_category else entry_data.category
        
        # Check for duplicate in category
        if await self.check_duplicate_in_category(user_id, entry_data.symbol, entry_data.category):
            raise ValueError(f"이미 해당 카테고리에 등록된 종목입니다")

        # Check portfolio limit
        if await self.check_portfolio_limit(user_id):
            raise ValueError(f"최대 {self.MAX_PORTFOLIO_ENTRIES}개 종목까지 등록 가능")

        # Create entry
        return await self.repository.create(user_id, entry_data)

    async def get_portfolio_with_calculations(
        self, user_id: str, category: Optional[str] = None
    ) -> List[PortfolioEntryResponse]:
        """
        Get portfolio entries with calculated P/L metrics

        Args:
            user_id: Owner's email
            category: Optional category filter

        Returns:
            List of portfolio entries with P/L calculations

        Performance: Uses batch service to fetch all stock prices in parallel (T171)
        """
        entries = await self.repository.get_all_by_user(user_id, category)

        if not entries:
            return []

        # Extract unique symbols for batch fetch
        symbols = [entry.symbol for entry in entries]
        
        # Batch fetch all stock prices (uses cache + concurrent API calls)
        prices = await self.batch_service.get_prices_batch(symbols)

        # Calculate P/L for each entry using fetched prices
        responses = []
        for entry in entries:
            current_price = prices.get(entry.symbol)
            
            # Calculate P/L metrics
            if current_price is not None:
                market_value = float(current_price) * entry.quantity
                profit_loss = (float(current_price) - float(entry.purchase_price)) * entry.quantity
                profit_loss_percent = ((float(current_price) - float(entry.purchase_price)) / float(entry.purchase_price)) * 100

                response = PortfolioEntryResponse(
                    entry_id=entry.entry_id,
                    user_id=entry.user_id,
                    symbol=entry.symbol,
                    company_name=entry.company_name,
                    category=entry.category,
                    purchase_price=entry.purchase_price,
                    quantity=entry.quantity,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                    current_price=round(current_price, 2),
                    market_value=round(market_value, 2),
                    profit_loss=round(profit_loss, 2),
                    profit_loss_percent=round(profit_loss_percent, 2),
                )
            else:
                # Price fetch failed - return entry with null calculations
                response = PortfolioEntryResponse(
                    entry_id=entry.entry_id,
                    user_id=entry.user_id,
                    symbol=entry.symbol,
                    company_name=entry.company_name,
                    category=entry.category,
                    purchase_price=entry.purchase_price,
                    quantity=entry.quantity,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                    current_price=None,
                    market_value=None,
                    profit_loss=None,
                    profit_loss_percent=None,
                )

            responses.append(response)

        return responses

    async def get_entry_with_calculations(self, entry_id: str, user_id: str) -> Optional[PortfolioEntryResponse]:
        """
        Get single portfolio entry with calculated P/L metrics

        Args:
            entry_id: Portfolio entry identifier
            user_id: Owner's email

        Returns:
            Portfolio entry with P/L calculations or None if not found
        """
        entry = await self.repository.get_by_id(entry_id, user_id)
        if not entry:
            return None

        calculations = await self.calculate_profit_loss(entry)
        return PortfolioEntryResponse(
            entry_id=entry.entry_id,
            user_id=entry.user_id,
            symbol=entry.symbol,
            company_name=entry.company_name,
            category=entry.category,
            purchase_price=entry.purchase_price,
            quantity=entry.quantity,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            current_price=calculations["current_price"],
            market_value=calculations["market_value"],
            profit_loss=calculations["profit_loss"],
            profit_loss_percent=calculations["profit_loss_percent"],
        )

    async def update_portfolio_entry(
        self, entry_id: str, user_id: str, update_data: PortfolioEntryUpdate
    ) -> Optional[PortfolioEntry]:
        """
        Update portfolio entry

        Args:
            entry_id: Portfolio entry identifier
            user_id: Owner's email
            update_data: Fields to update

        Returns:
            Updated portfolio entry or None if not found
        """
        return await self.repository.update(entry_id, user_id, update_data)

    async def delete_portfolio_entry(self, entry_id: str, user_id: str) -> bool:
        """
        Delete portfolio entry

        Args:
            entry_id: Portfolio entry identifier
            user_id: Owner's email

        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(entry_id, user_id)
