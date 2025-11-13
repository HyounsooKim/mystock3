# MyStock Backend API

FastAPI-based backend for MyStock stock portfolio management application.

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Python**: 3.11+
- **Database**: Azure Cosmos DB NoSQL
- **Authentication**: JWT with bcrypt password hashing
- **API Documentation**: OpenAPI/Swagger
- **Testing**: pytest with 70% coverage requirement

## Project Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── dependencies/      # Auth dependencies
│   │   ├── routes/            # API endpoints
│   │   ├── exception_handlers.py
│   │   └── main.py           # FastAPI app factory
│   ├── database/
│   │   ├── cosmos_client.py  # Cosmos DB client
│   │   └── init_db.py        # DB initialization
│   ├── models/               # Pydantic models
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── errors.py
│   ├── repositories/         # Data access layer
│   │   └── user_repository.py
│   ├── services/            # Business logic
│   │   └── auth_service.py
│   └── utils/               # Utilities
│       ├── jwt.py           # JWT token management
│       ├── security.py      # Password hashing
│       ├── logging.py       # Structured logging
│       └── config.py        # Configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py          # Pytest fixtures
├── .env.example
├── pytest.ini
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Getting Started

### Prerequisites

- Python 3.11+ (use `python3` command, not `python`)
- Azure Cosmos DB account
- Alpha Vantage API key

### Installation

```powershell
# Navigate to backend directory
cd mystock3/backend

# Create virtual environment with Python 3.11
python3 -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Application
MYSTOCK3_APP_ENV=development
MYSTOCK3_APP_NAME=MyStock

# Azure Cosmos DB
MYSTOCK3_COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
MYSTOCK3_COSMOS_KEY=your_cosmos_db_key
MYSTOCK3_DATABASE_NAME=mystock

# Security
MYSTOCK3_SECRET_KEY=your_jwt_secret_key_min_32_chars
MYSTOCK3_ALGORITHM=HS256
MYSTOCK3_ACCESS_TOKEN_EXPIRE_DAYS=7

# External APIs
MYSTOCK3_ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# CORS
MYSTOCK3_BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Running the Server

```powershell
# Make sure you're in backend directory with venv activated
cd mystock3/backend
.\.venv\Scripts\Activate.ps1

# Run development server
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Server will be available at:
- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Development

### Code Quality

```powershell
# Format code with Black
black src tests

# Lint with Ruff
ruff check src tests

# Type check with mypy
mypy src

# Run all checks
black src tests && ruff check src tests && mypy src
```

### Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

### Database Initialization

```powershell
# Initialize Cosmos DB containers
python -m src.database.init_db
```

## API Endpoints

### Authentication (`/api/v1/auth`)

- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user info

### Users (`/api/v1/users`)

- `GET /users/me` - Get current user profile
- `PATCH /users/me` - Update user preferences

### Stocks (`/api/v1/stocks`)

- `GET /stocks/search?q={query}` - Search stocks
- `GET /stocks/{symbol}/quote` - Get stock quote
- `GET /stocks/{symbol}/history` - Get historical data

### Watchlist (`/api/v1/watchlist`)

- `GET /watchlist` - Get user's watchlist
- `POST /watchlist` - Add stock to watchlist
- `PATCH /watchlist/{item_id}` - Update watchlist item
- `DELETE /watchlist/{item_id}` - Remove from watchlist
- `POST /watchlist/reorder` - Reorder watchlist

### Portfolio (`/api/v1/portfolio`)

- `GET /portfolio` - Get user's portfolio
- `POST /portfolio` - Add stock to portfolio
- `GET /portfolio/{entry_id}` - Get portfolio entry
- `PATCH /portfolio/{entry_id}` - Update portfolio entry
- `DELETE /portfolio/{entry_id}` - Remove from portfolio

## Architecture

### Authentication Flow

1. User signs up with email/password
2. Password hashed with bcrypt (work factor 12)
3. JWT token issued (7-day expiration)
4. Token stored in client localStorage
5. Token sent in Authorization header for protected routes

### Database Schema

#### Users Container
- Partition key: `user_id`
- Fields: `user_id`, `email`, `hashed_password`, `created_at`, `updated_at`, `is_active`

#### Watchlist Items Container
- Partition key: `user_id`
- Fields: `item_id`, `user_id`, `symbol`, `memo`, `order`, `created_at`, `updated_at`

#### Portfolio Entries Container
- Partition key: `user_id`
- Fields: `entry_id`, `user_id`, `symbol`, `category`, `purchase_price`, `quantity`, `purchase_date`, `created_at`, `updated_at`

### Error Handling

- All errors return consistent JSON structure
- HTTP status codes follow REST conventions
- Detailed error messages in development
- Generic messages in production
- Structured logging for all errors

### Logging

- JSON structured logging for Azure Log Analytics
- Request/response logging
- Error stack traces
- Performance metrics
- Custom fields for filtering

## Troubleshooting

### Common Issues

**ImportError: No module named 'src'**
- Solution: Ensure you're running from backend directory and PYTHONPATH is set correctly

**ModuleNotFoundError: No module named 'azure'**
- Solution: Install azure-cosmos package: `pip install azure-cosmos`

**Server won't start**
- Check virtual environment is activated
- Verify all dependencies installed
- Check .env file exists with correct values
- Ensure port 8000 is not in use

**Tests failing**
- Check test environment variables set
- Verify test database configured
- Run `pytest -v` for detailed output

## Contributing

1. Create feature branch from `main`
2. Follow code style (black, ruff, mypy)
3. Add tests for new features
4. Ensure 70% coverage maintained
5. Update API documentation
6. Create pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Azure Cosmos DB Python SDK](https://docs.microsoft.com/en-us/azure/cosmos-db/sql/sql-api-sdk-python)
- [pytest Documentation](https://docs.pytest.org/)
# Deployment timestamp: 2025-11-14 00:34:10
# Deployment retry: 2025-11-14 00:47:13
