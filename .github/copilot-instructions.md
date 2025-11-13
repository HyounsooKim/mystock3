# mystock3 Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-05

## Developer Profile

**Frontend Expertise**: The developer has extensive experience in stock trading systems and has built HTS (Home Trading System) applications. They are highly proficient in:
- Real-time stock data visualization and chart components (candlestick, volume, technical indicators)
- High-frequency data updates and WebSocket integration for live market data
- Trading UI/UX patterns (order books, watchlists, portfolio management, P&L displays)
- Performance optimization for real-time market data rendering
- Financial data formatting and calculation (prices, volumes, percentages, P&L)
- Stock market domain knowledge and trading workflows

When providing frontend assistance, leverage this HTS development background and assume familiarity with stock trading concepts, financial data structures, and real-time visualization requirements.

## Active Technologies

- Python 3.11 (backend), Vue 3 with Composition API (frontend) + FastAPI (backend API framework), Pydantic (validation), Pinia (state management), Tabler (UI components), ECharts (data visualization), Alpha Vantage API (stock data) (001-stock-portfolio-app)

## Project Structure

```text
backend/
  .venv/          # Python 3.11.9 virtual environment
  src/
    api/          # FastAPI routes and dependencies
    database/     # Cosmos DB client
    models/       # Pydantic models
    repositories/ # Data access layer
    services/     # Business logic
    utils/        # Utilities (JWT, logging, security)
  tests/          # Pytest tests
  requirements.txt
  requirements-dev.txt
  pytest.ini
frontend/
tests/
```

## Backend Setup

**Location**: `mystock3/backend/`

**Python Version**: 
- System `python`: Python 3.10
- System `python3`: Python 3.11 (Required)
- Virtual environment: Python 3.11.9

**⚠️ Important**: Always use `python3` command, not `python`

### Virtual Environment

```powershell
# Navigate to backend directory
cd mystock3/backend

# Create venv (if not exists) - MUST use python3
python3 -m venv .venv

# Activate venv (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Backend Server

```powershell
# Step 1: Navigate to backend directory
cd mystock3/backend

# Step 2: Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Step 3: Start uvicorn server
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

**Environment Variables**: Copy `.env.example` to `.env` and configure:
- `MYSTOCK3_COSMOS_ENDPOINT`: Azure Cosmos DB endpoint
- `MYSTOCK3_COSMOS_KEY`: Cosmos DB access key
- `MYSTOCK3_SECRET_KEY`: JWT secret key (min 32 chars)
- `MYSTOCK3_ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key

### Backend Architecture

- **Framework**: FastAPI with async/await
- **Database**: Azure Cosmos DB NoSQL
- **Authentication**: JWT tokens (7-day expiration) with bcrypt password hashing
- **Logging**: Structured JSON logging for Azure Log Analytics
- **Testing**: pytest with 70% coverage requirement

### Key Backend Files

- `src/api/main.py`: FastAPI application factory
- `src/api/routes/auth.py`: Authentication endpoints
- `src/models/user.py`: User and auth models
- `src/repositories/user_repository.py`: User CRUD operations
- `src/services/auth_service.py`: Authentication business logic
- `src/utils/jwt.py`: JWT token management
- `src/utils/security.py`: Password hashing (bcrypt)
- `src/database/cosmos_client.py`: Cosmos DB client singleton



## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11 (backend), Vue 3 with Composition API (frontend): Follow standard conventions

## Recent Changes

- 001-stock-portfolio-app: Added Python 3.11 (backend), Vue 3 with Composition API (frontend) + FastAPI (backend API framework), Pydantic (validation), Pinia (state management), Tabler (UI components), ECharts (data visualization), Alpha Vantage API (stock data)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
