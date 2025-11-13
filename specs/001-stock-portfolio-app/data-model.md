# Data Model: MyStock 주식 포트폴리오 앱

**Feature**: MyStock Stock Portfolio App  
**Date**: 2025-11-05  
**Purpose**: Entity schemas, relationships, and Cosmos DB design

## Overview

The MyStock application uses Azure Cosmos DB NoSQL for data persistence. The data model consists of four primary entities: User, Watchlist Item, Portfolio Entry, and Stock Quote (cached). All collections use `user_id` as the partition key to co-locate user data and optimize query performance.

---

## Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
│  (PK: id/email) │
└────────┬────────┘
         │ 1
         │
         │ N
    ┌────┴────────────────────┐
    │                         │
┌───▼──────────────┐   ┌──────▼──────────────┐
│ Watchlist Item   │   │  Portfolio Entry    │
│ (PK: user_id)    │   │  (PK: user_id)      │
└──────────────────┘   └─────────────────────┘
         │                         │
         │                         │
         └─────────┬───────────────┘
                   │
            ┌──────▼────────┐
            │  Stock Quote  │
            │ (Cached, TTL) │
            └───────────────┘
```

**Relationships**:
- User **1:N** Watchlist Items
- User **1:N** Portfolio Entries  
- Stock Quote is referenced but not stored permanently (cache only)

---

## 1. User Entity

### Purpose
Stores user account information, authentication credentials, and user preferences.

### Cosmos DB Collection
**Container Name**: `users`  
**Partition Key**: `/id` (user's email)

### Schema

```json
{
    "id": "user@example.com",
    "type": "user",
    "schema_version": "1.0",
    "email": "user@example.com",
    "password_hash": "$2b$12$...",
    "created_at": "2025-11-05T10:00:00Z",
    "updated_at": "2025-11-05T10:00:00Z",
    "preferences": {
        "dark_mode": true,
        "language": "ko"
    },
    "_ts": 1730804400
}
```

### Fields

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string | ✅ | User email (primary key, partition key) | Email format, unique |
| `type` | string | ✅ | Discriminator field | Fixed value: "user" |
| `schema_version` | string | ✅ | Schema version for migrations | Semantic versioning (e.g., "1.0") |
| `email` | string | ✅ | User's email address | Email format, lowercase, unique |
| `password_hash` | string | ✅ | bcrypt hashed password | bcrypt format, min 12 rounds |
| `created_at` | string (ISO 8601) | ✅ | Account creation timestamp | UTC timezone |
| `updated_at` | string (ISO 8601) | ✅ | Last profile update timestamp | UTC timezone |
| `preferences` | object | ❌ | User preferences | See sub-schema below |
| `preferences.dark_mode` | boolean | ❌ | Dark mode preference | Default: false |
| `preferences.language` | string | ❌ | UI language preference | ISO 639-1 code, default: "ko" |

### Validation Rules

1. **Email**: 
   - Must match regex: `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`
   - Normalized to lowercase before storage
   - Unique constraint enforced by using email as `id`

2. **Password**:
   - Minimum 6 characters (per clarification)
   - Hashed with bcrypt, work factor 12+
   - Never stored or transmitted in plaintext

3. **Timestamps**:
   - ISO 8601 format with UTC timezone
   - `created_at` set once at creation
   - `updated_at` updated on any field modification

### Indexing Policy

```json
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        {"path": "/id/?"},
        {"path": "/email/?"}
    ],
    "excludedPaths": [
        {"path": "/password_hash/?"},
        {"path": "/_etag/?"}
    ]
}
```

### Python Model (Pydantic)

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserPreferences(BaseModel):
    dark_mode: bool = False
    language: str = "ko"

class User(BaseModel):
    id: EmailStr
    type: str = Field(default="user", const=True)
    schema_version: str = "1.0"
    email: EmailStr
    password_hash: str
    created_at: datetime
    updated_at: datetime
    preferences: Optional[UserPreferences] = UserPreferences()
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user@example.com",
                "type": "user",
                "schema_version": "1.0",
                "email": "user@example.com",
                "password_hash": "$2b$12$...",
                "created_at": "2025-11-05T10:00:00Z",
                "updated_at": "2025-11-05T10:00:00Z",
                "preferences": {
                    "dark_mode": true,
                    "language": "ko"
                }
            }
        }
```

---

## 2. Watchlist Item Entity

### Purpose
Stores stocks that a user is monitoring with optional notes and custom ordering.

### Cosmos DB Collection
**Container Name**: `watchlist_items`  
**Partition Key**: `/user_id`

### Schema

```json
{
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
    "_ts": 1730806200
}
```

### Fields

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | ✅ | Unique item identifier | UUID v4 format |
| `type` | string | ✅ | Discriminator field | Fixed value: "watchlist_item" |
| `schema_version` | string | ✅ | Schema version | "1.0" |
| `user_id` | string | ✅ | Owner's email (partition key) | Email format, references User.id |
| `symbol` | string | ✅ | Stock ticker symbol | Uppercase, 1-5 chars (e.g., "AAPL") |
| `company_name` | string | ✅ | Company full name | Max 100 chars |
| `memo` | string | ❌ | User's note about the stock | Max 50 chars (per clarification) |
| `display_order` | integer | ✅ | Sort order in user's list | Positive integer, unique per user |
| `created_at` | string (ISO 8601) | ✅ | Item addition timestamp | UTC timezone |
| `updated_at` | string (ISO 8601) | ✅ | Last modification timestamp | UTC timezone |

### Validation Rules

1. **Symbol**:
   - Uppercase letters only
   - Length: 1-5 characters
   - Must exist in Alpha Vantage API (validated on add)

2. **Memo**:
   - Maximum 50 characters (per clarification)
   - Optional field, can be empty string

3. **Display Order**:
   - Positive integer starting from 1
   - Managed by drag-and-drop reordering
   - Resequenced when items are added/removed/reordered

4. **Duplicate Prevention**:
   - Cannot add same symbol twice to same user's watchlist (per clarification)
   - Validated at application layer before database insert

### Indexing Policy

```json
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        {"path": "/user_id/?"},
        {"path": "/symbol/?"},
        {"path": "/display_order/?"}
    ],
    "excludedPaths": [
        {"path": "/memo/?"}
    ]
}
```

### Python Model (Pydantic)

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import uuid

class WatchlistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(default="watchlist_item", const=True)
    schema_version: str = "1.0"
    user_id: str  # EmailStr
    symbol: str
    company_name: str = Field(max_length=100)
    memo: Optional[str] = Field(default="", max_length=50)
    display_order: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v.isupper() or not (1 <= len(v) <= 5):
            raise ValueError('Symbol must be 1-5 uppercase letters')
        return v
    
    class Config:
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
                "updated_at": "2025-11-05T11:00:00Z"
            }
        }
```

---

## 3. Portfolio Entry Entity

### Purpose
Stores stocks that a user owns, including purchase details and categorization.

### Cosmos DB Collection
**Container Name**: `portfolio_entries`  
**Partition Key**: `/user_id`

### Schema

```json
{
    "id": "660e8400-e29b-41d4-a716-446655440002",
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
    "_ts": 1730804400
}
```

### Fields

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | ✅ | Unique entry identifier | UUID v4 format |
| `type` | string | ✅ | Discriminator field | Fixed value: "portfolio_entry" |
| `schema_version` | string | ✅ | Schema version | "1.0" |
| `user_id` | string | ✅ | Owner's email (partition key) | Email format, references User.id |
| `symbol` | string | ✅ | Stock ticker symbol | Uppercase, 1-5 chars |
| `company_name` | string | ✅ | Company full name | Max 100 chars |
| `category` | string | ✅ | Investment category | Enum: "장기", "단기", "정찰병" |
| `purchase_price` | number | ✅ | Average purchase price per share | Positive decimal, 2 decimal places, USD |
| `quantity` | integer | ✅ | Number of shares owned | Positive integer |
| `created_at` | string (ISO 8601) | ✅ | Entry creation timestamp | UTC timezone |
| `updated_at` | string (ISO 8601) | ✅ | Last modification timestamp | UTC timezone |

### Calculated Fields (Not Stored)

These fields are calculated at runtime using current stock price from Alpha Vantage API:

| Field | Type | Formula | Description |
|-------|------|---------|-------------|
| `current_price` | number | From API | Latest stock price (USD) |
| `market_value` | number | `current_price × quantity` | Current total value |
| `profit_loss` | number | `(current_price - purchase_price) × quantity` | Total profit/loss |
| `profit_loss_percent` | number | `((current_price - purchase_price) / purchase_price) × 100` | Percentage gain/loss |

### Validation Rules

1. **Symbol**:
   - Same validation as Watchlist Item
   - Must exist in Alpha Vantage API

2. **Category**:
   - Must be one of: "장기" (long-term), "단기" (short-term), "정찰병" (scout/trial)
   - Cannot be changed after creation (business rule)

3. **Purchase Price**:
   - Must be positive
   - Precision: 2 decimal places
   - Currency: USD (assumption from spec)

4. **Quantity**:
   - Must be positive integer
   - No fractional shares in MVP

5. **Portfolio Limit**:
   - Maximum 10 entries per user (per clarification)
   - Enforced at application layer before insert

6. **Duplicate Prevention**:
   - Cannot add same symbol twice in same category (per clarification)
   - Same symbol allowed in different categories

### Indexing Policy

```json
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        {"path": "/user_id/?"},
        {"path": "/symbol/?"},
        {"path": "/category/?"}
    ],
    "excludedPaths": []
}
```

### Python Model (Pydantic)

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal
from decimal import Decimal
import uuid

class PortfolioEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(default="portfolio_entry", const=True)
    schema_version: str = "1.0"
    user_id: str  # EmailStr
    symbol: str
    company_name: str = Field(max_length=100)
    category: Literal["장기", "단기", "정찰병"]
    purchase_price: Decimal = Field(gt=0, decimal_places=2)
    quantity: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v.isupper() or not (1 <= len(v) <= 5):
            raise ValueError('Symbol must be 1-5 uppercase letters')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440002",
                "type": "portfolio_entry",
                "schema_version": "1.0",
                "user_id": "user@example.com",
                "symbol": "TSLA",
                "company_name": "Tesla, Inc.",
                "category": "장기",
                "purchase_price": 245.50,
                "quantity": 10,
                "created_at": "2025-10-01T09:00:00Z",
                "updated_at": "2025-11-05T10:00:00Z"
            }
        }

# Response model with calculated fields
class PortfolioEntryWithMetrics(PortfolioEntry):
    current_price: Decimal
    market_value: Decimal
    profit_loss: Decimal
    profit_loss_percent: Decimal
```

---

## 4. Stock Quote (Cached Entity)

### Purpose
Temporary cache of stock market data from Alpha Vantage API to minimize external API calls.

### Storage
**Implementation**: Azure Cache for Redis (or in-memory for MVP)  
**TTL**: 1 minute (per clarification)  
**No Cosmos DB persistence** (ephemeral only)

### Cache Key Format
```
stock:{symbol}:{YYYYMMDDHHMM}
```
Example: `stock:AAPL:202511051130`

### Schema

```json
{
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
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | ✅ | Stock ticker symbol |
| `company_name` | string | ✅ | Company full name |
| `current_price` | number | ✅ | Latest trading price |
| `change` | number | ✅ | Price change from previous close |
| `change_percent` | number | ✅ | Percentage change |
| `open` | number | ✅ | Opening price for the day |
| `high` | number | ✅ | Day's high price |
| `low` | number | ✅ | Day's low price |
| `volume` | integer | ✅ | Trading volume |
| `last_updated` | string (ISO 8601) | ✅ | API data timestamp |
| `currency` | string | ✅ | Price currency (USD) |

### Python Model (Pydantic)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

class StockQuote(BaseModel):
    symbol: str
    company_name: str
    current_price: Decimal = Field(decimal_places=2)
    change: Decimal = Field(decimal_places=2)
    change_percent: Decimal = Field(decimal_places=2)
    open: Decimal = Field(decimal_places=2)
    high: Decimal = Field(decimal_places=2)
    low: Decimal = Field(decimal_places=2)
    volume: int
    last_updated: datetime
    currency: str = "USD"
    
    class Config:
        json_schema_extra = {
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
```

---

## Query Patterns

### 1. User Queries

```python
# Get user by email
user = await users_container.read_item(
    item=email,
    partition_key=email
)

# Update user preferences
await users_container.upsert_item(body=user_dict)
```

### 2. Watchlist Queries

```python
# Get all watchlist items for a user (ordered)
query = "SELECT * FROM c WHERE c.type = 'watchlist_item' AND c.user_id = @user_id ORDER BY c.display_order ASC"
items = users_container.query_items(
    query=query,
    parameters=[{"name": "@user_id", "value": user_email}],
    partition_key=user_email
)

# Check for duplicate symbol
query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'watchlist_item' AND c.user_id = @user_id AND c.symbol = @symbol"
count = await watchlist_container.query_items(
    query=query,
    parameters=[
        {"name": "@user_id", "value": user_email},
        {"name": "@symbol", "value": symbol}
    ],
    partition_key=user_email
)
```

### 3. Portfolio Queries

```python
# Get portfolio entries by category
query = "SELECT * FROM c WHERE c.type = 'portfolio_entry' AND c.user_id = @user_id AND c.category = @category"
entries = await portfolio_container.query_items(
    query=query,
    parameters=[
        {"name": "@user_id", "value": user_email},
        {"name": "@category", "value": "장기"}
    ],
    partition_key=user_email
)

# Count total portfolio entries for a user
query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'portfolio_entry' AND c.user_id = @user_id"
count = await portfolio_container.query_items(
    query=query,
    parameters=[{"name": "@user_id", "value": user_email}],
    partition_key=user_email
)
```

---

## Schema Migration Strategy

### Version Tracking
- All documents include `schema_version` field
- Current version: "1.0"

### Migration Process
1. Create migration script in `backend/migrations/`
2. Document changes in `docs/schema-migrations.md`
3. Test migration on copy of production data
4. Run migration with rollback plan
5. Update `schema_version` in code

### Example Migration

```python
# migrations/001_add_user_preferences.py
async def migrate_users(container):
    query = "SELECT * FROM c WHERE c.type = 'user' AND c.schema_version = '1.0'"
    users = container.query_items(query=query)
    
    async for user in users:
        if 'preferences' not in user:
            user['preferences'] = {
                'dark_mode': False,
                'language': 'ko'
            }
            user['schema_version'] = '1.1'
            await container.upsert_item(body=user)
```

---

## Data Consistency & Integrity

### Constraints Enforced at Application Layer
1. **Unique email per user**: Enforced by using email as partition key
2. **Max 10 portfolio entries per user**: Checked before insert
3. **No duplicate symbols in watchlist**: Query check before insert
4. **No duplicate symbol+category in portfolio**: Query check before insert
5. **Memo max 50 characters**: Pydantic validation
6. **Password min 6 characters**: Pydantic validation

### Cascade Deletions
When a user is deleted:
- Delete all watchlist items (partition key = user_id)
- Delete all portfolio entries (partition key = user_id)
- Implemented via application logic (no database-level cascades)

---

## Cost Optimization

### Partition Strategy
- All user data uses `user_id` as partition key
- Ensures single-partition queries (no cross-partition overhead)
- Optimal for workload: users query only their own data

### Request Unit (RU) Estimates
- **User login**: ~10 RU (read user by id)
- **Get watchlist**: ~10 RU per user (single partition query)
- **Get portfolio**: ~10 RU per user per category
- **Add watchlist item**: ~15 RU (duplicate check + insert)
- **Add portfolio entry**: ~15 RU (count check + duplicate check + insert)

### Serverless Mode
- Use Cosmos DB serverless for MVP
- Pay per request (no provisioned throughput)
- Upgrade to provisioned throughput if usage exceeds break-even point

---

## TypeScript Frontend Types

```typescript
// types/index.ts
export interface User {
  id: string;
  type: 'user';
  schema_version: string;
  email: string;
  created_at: string;
  updated_at: string;
  preferences: {
    dark_mode: boolean;
    language: string;
  };
}

export interface WatchlistItem {
  id: string;
  type: 'watchlist_item';
  schema_version: string;
  user_id: string;
  symbol: string;
  company_name: string;
  memo: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioEntry {
  id: string;
  type: 'portfolio_entry';
  schema_version: string;
  user_id: string;
  symbol: string;
  company_name: string;
  category: '장기' | '단기' | '정찰병';
  purchase_price: number;
  quantity: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioEntryWithMetrics extends PortfolioEntry {
  current_price: number;
  market_value: number;
  profit_loss: number;
  profit_loss_percent: number;
}

export interface StockQuote {
  symbol: string;
  company_name: string;
  current_price: number;
  change: number;
  change_percent: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  last_updated: string;
  currency: string;
}
```

---

## Summary

The data model consists of three persisted entities in Cosmos DB (User, Watchlist Item, Portfolio Entry) plus one cached entity (Stock Quote). All collections use optimized partition keys for single-partition queries. The schema supports all functional requirements from the specification, including 50-character memo limits, portfolio limits, duplicate prevention, and dark mode preferences.

**Next Steps**:
1. Generate OpenAPI contracts based on these data models
2. Create quickstart guide for local development setup
3. Implement Pydantic models in backend code
4. Generate TypeScript types for frontend
