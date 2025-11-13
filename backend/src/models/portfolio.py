"""
Portfolio Entry Model

Defines the PortfolioEntry entity for tracking user's stock holdings with purchase details.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class PortfolioCategory(str, Enum):
    """Portfolio investment categories"""
    
    LONG_TERM = "장기"
    SHORT_TERM = "단기"
    SCOUT = "정찰병"


class PortfolioEntryBase(BaseModel):
    """Base portfolio entry fields"""

    symbol: str = Field(..., min_length=1, max_length=5, description="Stock ticker symbol")
    company_name: str = Field(..., max_length=100, description="Company full name")
    category: str = Field(..., description="Investment category: 장기, 단기, 정찰병")
    purchase_price: float = Field(..., gt=0, description="Average purchase price per share (USD)")
    quantity: int = Field(..., gt=0, description="Number of shares owned")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol is uppercase"""
        if not v.isupper():
            raise ValueError("Symbol must be uppercase")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is one of allowed values"""
        allowed_categories = ["장기", "단기", "정찰병"]
        if v not in allowed_categories:
            raise ValueError(f"Category must be one of: {', '.join(allowed_categories)}")
        return v

    @field_validator("purchase_price")
    @classmethod
    def validate_purchase_price(cls, v: float) -> float:
        """Validate purchase price has max 2 decimal places"""
        if round(v, 2) != v:
            raise ValueError("Purchase price must have at most 2 decimal places")
        return v


class PortfolioEntryCreate(PortfolioEntryBase):
    """Schema for creating a new portfolio entry"""

    pass


class PortfolioEntryUpdate(BaseModel):
    """Schema for updating an existing portfolio entry"""

    purchase_price: Optional[float] = Field(None, gt=0, description="Updated purchase price")
    quantity: Optional[int] = Field(None, gt=0, description="Updated quantity")

    @field_validator("purchase_price")
    @classmethod
    def validate_purchase_price(cls, v: Optional[float]) -> Optional[float]:
        """Validate purchase price has max 2 decimal places"""
        if v is not None and round(v, 2) != v:
            raise ValueError("Purchase price must have at most 2 decimal places")
        return v


class PortfolioEntry(PortfolioEntryBase):
    """Complete portfolio entry model stored in Cosmos DB"""

    entry_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique entry identifier")
    user_id: str = Field(..., description="Owner's email (partition key)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Entry creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last modification timestamp")

    # Cosmos DB internal fields
    type: str = Field(default="portfolio_entry", description="Discriminator field")
    schema_version: str = Field(default="1.0", description="Schema version")

    class Config:
        json_schema_extra = {
            "example": {
                "entry_id": "660e8400-e29b-41d4-a716-446655440002",
                "type": "portfolio_entry",
                "schema_version": "1.0",
                "user_id": "user@example.com",
                "symbol": "TSLA",
                "company_name": "Tesla, Inc.",
                "category": "장기",
                "purchase_price": 245.50,
                "quantity": 10,
                "created_at": "2025-10-01T09:00:00Z",
                "updated_at": "2025-11-05T10:00:00Z",
            }
        }


class PortfolioEntryResponse(PortfolioEntryBase):
    """Schema for portfolio entry API responses with calculated fields"""

    entry_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    # Calculated fields (not stored, computed at runtime)
    current_price: Optional[float] = Field(None, description="Latest stock price from API")
    market_value: Optional[float] = Field(None, description="Current total value (current_price × quantity)")
    profit_loss: Optional[float] = Field(None, description="Total profit/loss amount")
    profit_loss_percent: Optional[float] = Field(None, description="Percentage gain/loss")

    class Config:
        json_schema_extra = {
            "example": {
                "entry_id": "660e8400-e29b-41d4-a716-446655440002",
                "user_id": "user@example.com",
                "symbol": "TSLA",
                "company_name": "Tesla, Inc.",
                "category": "장기",
                "purchase_price": 245.50,
                "quantity": 10,
                "created_at": "2025-10-01T09:00:00Z",
                "updated_at": "2025-11-05T10:00:00Z",
                "current_price": 250.00,
                "market_value": 2500.00,
                "profit_loss": 45.00,
                "profit_loss_percent": 1.83,
            }
        }
