"""Watchlist data models.

This module defines Pydantic models for watchlist items.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class WatchlistItemBase(BaseModel):
    """Base watchlist item schema shared across operations."""

    symbol: str = Field(..., min_length=1, max_length=5, description="Stock ticker symbol")
    company_name: str = Field(..., max_length=100, description="Company full name")
    memo: Optional[str] = Field(
        default="", max_length=50, description="User's note (max 50 chars)"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        if not v.isupper():
            raise ValueError("Symbol must be uppercase letters")
        if not (1 <= len(v) <= 5):
            raise ValueError("Symbol must be 1-5 characters")
        return v


class WatchlistItemCreate(BaseModel):
    """Schema for creating a new watchlist item."""
    
    symbol: str = Field(..., min_length=1, max_length=5, description="Stock ticker symbol")
    company_name: str = Field(..., max_length=100, description="Company full name")
    memo: Optional[str] = Field(
        default="", max_length=50, description="User's note (max 50 chars)"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        if not v.isupper():
            raise ValueError("Symbol must be uppercase letters")
        if not (1 <= len(v) <= 5):
            raise ValueError("Symbol must be 1-5 characters")
        return v


class WatchlistItemUpdate(BaseModel):
    """Schema for updating an existing watchlist item."""

    memo: Optional[str] = Field(None, max_length=50, description="Updated memo")
    display_order: Optional[int] = Field(None, ge=1, description="Updated display order")


class WatchlistItemReorder(BaseModel):
    """Schema for reordering watchlist items."""

    item_ids: list[str] = Field(..., description="Ordered list of item IDs")


class WatchlistItem(BaseModel):
    """Complete watchlist item with database fields."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique item ID")
    type: str = Field(default="watchlist_item", description="Document type discriminator")
    schema_version: str = Field(default="1.0", description="Schema version")
    user_id: str = Field(..., description="Owner's email")
    symbol: str = Field(..., min_length=1, max_length=5, description="Stock ticker symbol")
    company_name: str = Field(..., max_length=100, description="Company full name")
    memo: Optional[str] = Field(
        default="", max_length=50, description="User's note (max 50 chars)"
    )
    display_order: int = Field(ge=1, description="Sort order in user's list")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "type": "watchlist_item",
                "schema_version": "1.0",
                "user_id": "user@example.com",
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "memo": "매수 타이밍 지켜보는 중",
                "display_order": 1,
                "created_at": "2025-11-05T10:30:00Z",
                "updated_at": "2025-11-05T11:00:00Z",
            }
        }


class WatchlistItemWithQuote(WatchlistItem):
    """Watchlist item enriched with current stock quote data."""

    current_price: Optional[float] = Field(None, description="Latest stock price")
    change: Optional[float] = Field(None, description="Price change from previous close")
    change_percent: Optional[float] = Field(None, description="Percentage change")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "type": "watchlist_item",
                "schema_version": "1.0",
                "user_id": "user@example.com",
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "memo": "매수 타이밍 지켜보는 중",
                "display_order": 1,
                "created_at": "2025-11-05T10:30:00Z",
                "updated_at": "2025-11-05T11:00:00Z",
                "current_price": 178.32,
                "change": 2.15,
                "change_percent": 1.22,
            }
        }
