# MyStock Quickstart Guide

**Feature Branch:** `001-stock-portfolio-app`  
**Last Updated:** 2025-11-05

This guide will help you set up and run the MyStock application locally for development.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
  - [Clone Repository](#clone-repository)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [External API Setup](#external-api-setup)
- [Running Locally](#running-locally)
  - [Start Backend Server](#start-backend-server)
  - [Start Frontend Dev Server](#start-frontend-dev-server)
  - [Verify Installation](#verify-installation)
- [Running Tests](#running-tests)
  - [Backend Tests](#backend-tests)
  - [Frontend Tests](#frontend-tests)
  - [E2E Tests](#e2e-tests)
- [Common Development Tasks](#common-development-tasks)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Ensure you have the following installed on your development machine:

### Required Software

| Tool | Version | Purpose | Download Link |
|------|---------|---------|---------------|
| **Python** | 3.11+ | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ (LTS) | Frontend runtime | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ | Package manager | Included with Node.js |
| **Git** | Latest | Version control | [git-scm.com](https://git-scm.com/) |
| **PowerShell** | 5.1+ | Scripting (Windows) | Pre-installed on Windows |
| **Azure CLI** | Latest | Cloud deployment | [docs.microsoft.com](https://docs.microsoft.com/cli/azure/install-azure-cli) |

### Optional Tools

- **Docker Desktop** - For containerized development (optional)
- **VS Code** - Recommended IDE with Python and Vue extensions
- **Postman** - For API testing

### Azure Account Requirements

- Active Azure subscription
- Permission to create resources (Resource Groups, Container Apps, Cosmos DB)
- Alpha Vantage API key (free tier: [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key))

---

## Environment Setup

### Clone Repository

```powershell
# Clone the repository
git clone https://github.com/HyounsooKim/mystock3.git
cd mystock3

# Checkout feature branch
git checkout 001-stock-portfolio-app
```

### Backend Setup

#### 1. Create Python Virtual Environment

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Verify activation (should show (venv) prefix)
# If you get execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Install Backend Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

**`requirements.txt`** (core dependencies):
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiohttp==3.9.1
azure-cosmos==4.5.1
azure-identity==1.15.0
```

**`requirements-dev.txt`** (development dependencies):
```txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
black==23.11.0
ruff==0.1.6
mypy==1.7.1
```

#### 3. Configure Backend Environment

Create `.env` file in `backend/` directory:

```powershell
# Create .env file from template
Copy-Item .env.example .env

# Edit .env with your settings
notepad .env
```

**`backend/.env`** (example values):
```bash
# Application
APP_NAME=MyStock
APP_ENV=development
LOG_LEVEL=INFO

# API
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# Database (local development uses Azure Cosmos DB Emulator or cloud)
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOS_DATABASE_NAME=mystockdb

# External API
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
STOCK_CACHE_TTL_SECONDS=60

# Azure (for cloud deployment)
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

**Important:** 
- Change `SECRET_KEY` to a random string (use `openssl rand -hex 32`)
- Get free Alpha Vantage API key from https://www.alphavantage.co/support/#api-key
- For local dev, use [Azure Cosmos DB Emulator](https://docs.microsoft.com/azure/cosmos-db/local-emulator) or cloud instance

#### 4. Initialize Database

```powershell
# Run database initialization script
python -m app.db.init_db

# Verify containers created
python -m app.db.verify_db
```

### Frontend Setup

#### 1. Install Frontend Dependencies

```powershell
# Navigate to frontend directory (from project root)
cd ..\frontend

# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

**Key packages** (defined in `package.json`):
```json
{
  "dependencies": {
    "vue": "^3.3.10",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "@tabler/core": "^1.0.0-beta20",
    "echarts": "^5.4.3",
    "vue-echarts": "^6.6.1",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.0",
    "vite": "^5.0.4",
    "typescript": "^5.3.2",
    "@vue/eslint-config-typescript": "^12.0.0",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0",
    "@playwright/test": "^1.40.1"
  }
}
```

#### 2. Configure Frontend Environment

Create `.env` file in `frontend/` directory:

```powershell
# Create .env file
New-Item -Path .env -ItemType File

# Edit .env
notepad .env
```

**`frontend/.env`**:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=MyStock
VITE_APP_VERSION=1.0.0
```

### External API Setup

#### Alpha Vantage API Key

1. Visit https://www.alphavantage.co/support/#api-key
2. Enter your email to receive free API key
3. Add key to `backend/.env`:
   ```bash
   ALPHA_VANTAGE_API_KEY=YOUR_KEY_HERE
   ```

**Rate Limits (Free Tier):**
- 5 API calls per minute
- 100 API calls per day
- Use 1-minute cache to minimize calls

---

## Running Locally

### Start Backend Server

Open **PowerShell Terminal 1**:

```powershell
# Navigate to backend directory
cd C:\Work\Azure\test1\mystock3\backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start FastAPI server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Run with detailed logs
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify Backend:**
- API Docs: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/v1/health

### Start Frontend Dev Server

Open **PowerShell Terminal 2**:

```powershell
# Navigate to frontend directory
cd C:\Work\Azure\test1\mystock3\frontend

# Start Vite dev server
npm run dev

# Alternative: Expose to network
npm run dev -- --host
```

**Expected Output:**
```
VITE v5.0.4  ready in 523 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Verify Frontend:**
- Application: http://localhost:5173
- Should see login/signup page with dark mode toggle

### Verify Installation

#### Backend Health Check

```powershell
# Test API health endpoint
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method GET

# Expected response:
# @{status=healthy; timestamp=2025-11-05T10:00:00Z}
```

#### Frontend-Backend Connection

```powershell
# Test signup (from frontend directory)
$body = @{
    email = "test@example.com"
    password = "test123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/signup" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Expected: JWT token response
```

#### Browse Application

1. Open browser to http://localhost:5173
2. Click "Sign Up" and create test account
3. Login with created credentials
4. Add a stock to watchlist (e.g., "AAPL")
5. Verify stock data displays with current price

---

## Running Tests

### Backend Tests

```powershell
# Navigate to backend directory
cd backend
.\venv\Scripts\Activate.ps1

# Run all tests with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run tests matching pattern
pytest tests/test_api/ -k "watchlist" -v

# Run with detailed output
pytest -vv --tb=short

# Check coverage report
# Open: backend/htmlcov/index.html in browser
```

**Coverage Requirements:** Minimum 70% (constitution mandate)

**Test Structure:**
```
backend/tests/
├── conftest.py               # Shared fixtures
├── test_auth.py              # Authentication tests
├── test_api/
│   ├── test_watchlist.py     # Watchlist endpoint tests
│   ├── test_portfolio.py     # Portfolio endpoint tests
│   └── test_stocks.py        # Stock data tests
├── test_models/
│   ├── test_user.py          # User model tests
│   └── test_validations.py   # Pydantic validation tests
└── test_services/
    ├── test_alpha_vantage.py # External API tests (mocked)
    └── test_cache.py          # Cache logic tests
```

### Frontend Tests

```powershell
# Navigate to frontend directory
cd frontend

# Run unit tests (Vitest)
npm run test:unit

# Run with coverage
npm run test:unit -- --coverage

# Run in watch mode
npm run test:unit -- --watch
```

**Test Structure:**
```
frontend/tests/
├── unit/
│   ├── components/
│   │   ├── WatchlistTable.spec.ts
│   │   ├── PortfolioHeatmap.spec.ts
│   │   └── StockChart.spec.ts
│   └── stores/
│       ├── auth.store.spec.ts
│       ├── watchlist.store.spec.ts
│       └── portfolio.store.spec.ts
└── e2e/
    ├── auth.spec.ts
    ├── watchlist.spec.ts
    └── portfolio.spec.ts
```

### E2E Tests

```powershell
# Ensure backend and frontend are running

# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run in UI mode (interactive)
npm run test:e2e -- --ui

# Run specific test file
npx playwright test tests/e2e/watchlist.spec.ts

# Generate test report
npx playwright show-report
```

**E2E Test Scenarios:**
- User signup and login flow
- Add/remove stocks from watchlist
- Drag-and-drop reordering
- Portfolio CRUD operations
- Stock data refresh (cache verification)
- Dark mode toggle persistence

---

## Common Development Tasks

### Code Formatting

**Backend (Black + Ruff):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Format code with Black
black app/ tests/

# Lint with Ruff
ruff check app/ tests/

# Fix auto-fixable issues
ruff check --fix app/ tests/

# Type checking
mypy app/
```

**Frontend (ESLint + Prettier):**
```powershell
cd frontend

# Format with Prettier
npm run format

# Lint with ESLint
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix
```

### Database Management

**Reset Database:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Drop all containers
python -m app.db.drop_all

# Recreate containers
python -m app.db.init_db
```

**Seed Test Data:**
```powershell
# Create test users and data
python -m app.db.seed_data
```

### API Documentation

**Update OpenAPI Spec:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1

# FastAPI auto-generates OpenAPI spec
# View at http://localhost:8000/docs

# Export spec to file
Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" `
    | ConvertTo-Json -Depth 10 `
    | Out-File -FilePath "../specs/001-stock-portfolio-app/contracts/openapi.json"
```

### Environment Variables

**Backend:**
```powershell
# List all environment variables
cd backend
Get-Content .env

# Update specific variable
(Get-Content .env) -replace 'LOG_LEVEL=INFO', 'LOG_LEVEL=DEBUG' | Set-Content .env
```

**Frontend:**
```powershell
# Vite requires VITE_ prefix for exposed variables
cd frontend
Get-Content .env
```

### Clear Caches

**Backend Cache:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Clear stock quote cache
python -m app.services.cache --clear
```

**Frontend Cache:**
```powershell
cd frontend

# Clear Vite cache
Remove-Item -Recurse -Force node_modules/.vite

# Clear browser cache
# Use browser DevTools > Network > Disable cache
```

---

## Deployment

### Prerequisites

```powershell
# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Verify login
az account show
```

### Deploy Infrastructure

```powershell
# Navigate to infrastructure directory
cd infrastructure

# Deploy to dev environment
.\deploy.ps1 -Environment dev -Location koreacentral

# Deploy to production
.\deploy.ps1 -Environment prod -Location koreacentral -SkipTests
```

**Deployment Script** (`infrastructure/deploy.ps1`):
- Creates Resource Group
- Deploys Bicep templates (Cosmos DB, Container Apps, Static Web Apps)
- Configures Key Vault with secrets
- Sets up Log Analytics workspace
- Configures CI/CD with GitHub Actions

### Deploy Backend

```powershell
# Build Docker image
cd backend
docker build -t mystock-backend:latest .

# Push to Azure Container Registry
az acr login --name mystockacr
docker tag mystock-backend:latest mystockacr.azurecr.io/backend:latest
docker push mystockacr.azurecr.io/backend:latest

# Deploy to Container Apps
az containerapp update `
    --name mystock-backend `
    --resource-group mystock-dev-rg `
    --image mystockacr.azurecr.io/backend:latest
```

### Deploy Frontend

```powershell
# Build frontend
cd frontend
npm run build

# Deploy to Static Web Apps
az staticwebapp deploy `
    --name mystock-frontend `
    --resource-group mystock-dev-rg `
    --app-location dist/ `
    --output-location dist/
```

### Verify Deployment

```powershell
# Get backend URL
$backendUrl = az containerapp show `
    --name mystock-backend `
    --resource-group mystock-dev-rg `
    --query "properties.configuration.ingress.fqdn" `
    --output tsv

Write-Host "Backend URL: https://$backendUrl"

# Get frontend URL
$frontendUrl = az staticwebapp show `
    --name mystock-frontend `
    --resource-group mystock-dev-rg `
    --query "defaultHostname" `
    --output tsv

Write-Host "Frontend URL: https://$frontendUrl"

# Test health endpoint
Invoke-RestMethod -Uri "https://$backendUrl/api/v1/health"
```

---

## Troubleshooting

### Backend Issues

#### Port Already in Use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution:**
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object -Property OwningProcess
$processId = (Get-NetTCPConnection -LocalPort 8000).OwningProcess

# Kill process
Stop-Process -Id $processId -Force

# Restart backend
uvicorn app.main:app --reload --port 8000
```

#### Database Connection Failed

**Error:** `azure.cosmos.exceptions.CosmosHttpResponseError: Unauthorized`

**Solution:**
```powershell
# Verify Cosmos DB credentials in .env
cd backend
Get-Content .env | Select-String -Pattern "COSMOS"

# Test connection
python -c "from app.db.cosmos_client import get_cosmos_client; client = get_cosmos_client(); print('Connected:', client)"
```

#### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```powershell
# Ensure virtual environment is activated
cd backend
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues

#### Network Error (CORS)

**Error:** `Access to fetch blocked by CORS policy`

**Solution:**
```powershell
# Verify backend CORS configuration in backend/.env
# BACKEND_CORS_ORIGINS must include http://localhost:5173

# Update backend .env
cd backend
notepad .env
# Add: BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# Restart backend server
```

#### Dependency Version Conflict

**Error:** `npm ERR! ERESOLVE unable to resolve dependency tree`

**Solution:**
```powershell
cd frontend

# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
Remove-Item -Recurse -Force node_modules, package-lock.json

# Reinstall
npm install

# If still fails, use --legacy-peer-deps
npm install --legacy-peer-deps
```

#### Vite Build Failed

**Error:** `[vite] error while building`

**Solution:**
```powershell
# Check TypeScript errors
npm run type-check

# Clear Vite cache
Remove-Item -Recurse -Force node_modules/.vite

# Rebuild
npm run build
```

### Test Issues

#### Pytest Import Errors

**Error:** `ImportError: attempted relative import with no known parent package`

**Solution:**
```powershell
cd backend

# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Install package in editable mode
pip install -e .

# Run tests from backend root
pytest
```

#### Playwright Browser Not Found

**Error:** `browserType.launch: Executable doesn't exist`

**Solution:**
```powershell
cd frontend

# Install Playwright browsers
npx playwright install

# Install system dependencies (if on Linux/WSL)
npx playwright install-deps
```

### External API Issues

#### Alpha Vantage Rate Limit

**Error:** `API rate limit exceeded (5 calls/min)`

**Solution:**
- Check cache TTL in `backend/.env` (should be 60 seconds)
- Reduce frontend auto-refresh frequency
- Use batch requests for multiple symbols
- Consider upgrading to paid Alpha Vantage tier

**Verify Cache:**
```powershell
cd backend
python -m app.services.cache --stats
# Should show cache hit rate and TTL
```

### Azure Deployment Issues

#### Bicep Deployment Failed

**Error:** `DeploymentFailed: The template deployment failed`

**Solution:**
```powershell
# Get deployment error details
az deployment group show `
    --name mystock-deployment `
    --resource-group mystock-dev-rg `
    --query "properties.error"

# Validate Bicep template
cd infrastructure
az bicep build --file main.bicep
```

#### Container App Not Starting

**Error:** `Container failed to start`

**Solution:**
```powershell
# Check logs
az containerapp logs show `
    --name mystock-backend `
    --resource-group mystock-dev-rg `
    --follow

# Verify environment variables
az containerapp show `
    --name mystock-backend `
    --resource-group mystock-dev-rg `
    --query "properties.template.containers[0].env"
```

---

## Additional Resources

### Documentation

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Vue 3 Docs:** https://vuejs.org/guide/introduction.html
- **Pinia Docs:** https://pinia.vuejs.org/
- **Azure Cosmos DB:** https://docs.microsoft.com/azure/cosmos-db/
- **Azure Container Apps:** https://docs.microsoft.com/azure/container-apps/
- **Alpha Vantage API:** https://www.alphavantage.co/documentation/

### Project Resources

- **Feature Spec:** `specs/001-stock-portfolio-app/spec.md`
- **Implementation Plan:** `specs/001-stock-portfolio-app/plan.md`
- **API Contracts:** `specs/001-stock-portfolio-app/contracts/openapi.yaml`
- **Data Model:** `specs/001-stock-portfolio-app/data-model.md`
- **Research:** `specs/001-stock-portfolio-app/research.md`

### Useful Commands

```powershell
# Backend
cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload

# Frontend
cd frontend; npm run dev

# Tests
cd backend; pytest --cov=app; cd ..\frontend; npm run test:e2e

# Format
cd backend; black app/ tests/; ruff check --fix app/; cd ..\frontend; npm run format; npm run lint -- --fix

# Deploy
cd infrastructure; .\deploy.ps1 -Environment dev
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check [GitHub Issues](https://github.com/HyounsooKim/mystock3/issues)
2. Review error logs in `backend/logs/` and browser DevTools Console
3. Verify all prerequisites are installed with correct versions
4. Ensure `.env` files are properly configured
5. Try clearing caches and reinstalling dependencies

**Constitution Reference:** See `.specify/memory/constitution.md` for project principles and standards.

---

**Happy Coding! 🚀**
