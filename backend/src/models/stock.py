"""Stock models for MyStock application."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StockQuote(BaseModel):
    """Stock quote model for real-time price data.
    
    This model represents cached stock data from Alpha Vantage API
    with 1-minute TTL to minimize external API calls.
    """
    
    symbol: str
    company_name: str
    current_price: Decimal = Field(decimal_places=4)
    change: Decimal = Field(decimal_places=4)
    change_percent: Decimal = Field(decimal_places=4)
    open: Decimal = Field(decimal_places=4)
    high: Decimal = Field(decimal_places=4)
    low: Decimal = Field(decimal_places=4)
    volume: int = Field(ge=0)
    last_updated: datetime
    currency: str = "USD"
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        if not v.isupper() or not (1 <= len(v) <= 5):
            raise ValueError('Symbol must be 1-5 uppercase letters')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "current_price": 178.32,
                "change": 2.15,
                "change_percent": 1.22,
                "open": 176.50,
                "high": 179.00,
                "low": 176.20,
                "volume": 58392010,
                "last_updated": "2025-11-05T11:30:00Z",
                "currency": "USD"
            }
        }
    }


class StockHistoryPoint(BaseModel):
    """Single data point in stock price history."""
    
    date: datetime
    open: Decimal = Field(decimal_places=2)
    high: Decimal = Field(decimal_places=2)
    low: Decimal = Field(decimal_places=2)
    close: Decimal = Field(decimal_places=2)
    volume: int = Field(ge=0)


class StockHistoryResponse(BaseModel):
    """Response model for historical stock data."""
    
    symbol: str
    period: Literal["1D", "5D", "1M", "3M", "6M", "1Y", "5Y"]
    data: list[StockHistoryPoint]
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        if not v.isupper() or not (1 <= len(v) <= 5):
            raise ValueError('Symbol must be 1-5 uppercase letters')
        return v


class StockSearchResult(BaseModel):
    """Stock search result item."""
    
    symbol: str
    name: str
    type: str
    region: str
    currency: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "type": "Common Stock",
                "region": "United States",
                "currency": "USD"
            }
        }
    }


class StockSearchResponse(BaseModel):
    """Response model for stock search endpoint."""
    
    results: list[StockSearchResult]
    query: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "apple",
                "results": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "type": "Common Stock",
                        "region": "United States",
                        "currency": "USD"
                    }
                ]
            }
        }
    }
