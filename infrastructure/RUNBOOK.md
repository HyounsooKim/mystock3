# MyStock3 Deployment Runbook

## Overview

This runbook provides step-by-step procedures for deploying MyStock3 application to Azure environments (staging and production).

**Last Updated**: 2025-11-13  
**Version**: 1.0.0  
**Maintained by**: DevOps Team

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Deployment Process](#deployment-process)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Azure CLI**: Version 2.50.0 or higher
- **PowerShell**: Version 7.0 or higher
- **Node.js**: Version 18.x or higher (for frontend build)
- **Python**: Version 3.11 (for backend)
- **Git**: For source code management

### Required Access

- Azure subscription with Contributor role
- Azure Resource Group access
- Azure Key Vault access (for secrets)
- GitHub repository access (for CI/CD)

### Environment Variables

Create a `.env` file or configure these in Azure Key Vault:

```bash
# Cosmos DB
MYSTOCK3_COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
MYSTOCK3_COSMOS_KEY=<primary-key>

# JWT
MYSTOCK3_SECRET_KEY=<min-32-char-secret>

# Alpha Vantage
MYSTOCK3_ALPHA_VANTAGE_API_KEY=<api-key>

# Application Insights (optional)
APPLICATIONINSIGHTS_CONNECTION_STRING=<connection-string>

# Azure Key Vault (optional)
AZURE_KEY_VAULT_URL=https://<vault-name>.vault.azure.net/
```

---

## Environment Configuration

### Staging Environment

- **Resource Group**: `rg-mystock3-staging`
- **Region**: East US
- **App Service Plan**: S1 (Standard)
- **Cosmos DB**: Serverless mode
- **Frontend URL**: `https://staging.mystock3.example.com`
- **Backend URL**: `https://api-staging.mystock3.example.com`

### Production Environment

- **Resource Group**: `rg-mystock3-prod`
- **Region**: East US (primary), West US (failover)
- **App Service Plan**: P1V2 (Premium)
- **Cosmos DB**: Provisioned throughput (10,000 RU/s autoscale)
- **Frontend URL**: `https://mystock3.example.com`
- **Backend URL**: `https://api.mystock3.example.com`

---

## Deployment Process

### Step 1: Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Code coverage ≥70%
- [ ] Security scan completed (no high/critical vulnerabilities)
- [ ] Database migration scripts reviewed (if any)
- [ ] Secrets rotated (if needed)
- [ ] Stakeholders notified of deployment window
- [ ] Rollback plan prepared

### Step 2: Infrastructure Deployment (Bicep)

```powershell
# Navigate to infrastructure directory
cd infrastructure/bicep

# Validate Bicep templates (T192)
az bicep build --file main.bicep
az deployment group validate `
  --resource-group rg-mystock3-staging `
  --template-file main.bicep `
  --parameters @parameters.staging.json

# Deploy infrastructure
az deployment group create `
  --resource-group rg-mystock3-staging `
  --template-file main.bicep `
  --parameters @parameters.staging.json `
  --name "mystock3-infra-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Verify deployment
az deployment group show `
  --resource-group rg-mystock3-staging `
  --name <deployment-name> `
  --query "properties.provisioningState"
```

### Step 3: Database Setup

```powershell
# Apply Cosmos DB indexing policies
cd backend/src/database

# Review INDEXING_STRATEGY.md
# Apply via Azure Portal or SDK (see backend/INDEXING_STRATEGY.md)

# Verify indexes
az cosmosdb sql container show `
  --account-name <cosmos-account> `
  --database-name mystock3 `
  --name portfolio_entries `
  --resource-group rg-mystock3-staging `
  --query "resource.indexingPolicy"
```

### Step 4: Backend Deployment

```powershell
# Build backend
cd backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ --cov=src --cov-report=html

# Deploy to Azure App Service
az webapp up `
  --resource-group rg-mystock3-staging `
  --name mystock3-backend-staging `
  --runtime "PYTHON:3.11" `
  --sku S1 `
  --location eastus

# Configure app settings
az webapp config appsettings set `
  --resource-group rg-mystock3-staging `
  --name mystock3-backend-staging `
  --settings @appsettings.staging.json
```

### Step 5: Frontend Deployment

```powershell
# Build frontend
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Deploy to Azure Static Web Apps or CDN
az staticwebapp create `
  --name mystock3-frontend-staging `
  --resource-group rg-mystock3-staging `
  --source ./dist `
  --location eastus `
  --branch staging `
  --app-location "/"

# Or deploy to App Service
az webapp up `
  --resource-group rg-mystock3-staging `
  --name mystock3-frontend-staging `
  --html `
  --location eastus
```

### Step 6: Configure Secrets (Azure Key Vault)

```powershell
# Store secrets in Key Vault (T188)
az keyvault secret set `
  --vault-name mystock3-kv-staging `
  --name "cosmos-db-key" `
  --value "<cosmos-key>"

az keyvault secret set `
  --vault-name mystock3-kv-staging `
  --name "jwt-secret-key" `
  --value "<jwt-secret>"

az keyvault secret set `
  --vault-name mystock3-kv-staging `
  --name "alpha-vantage-api-key" `
  --value "<api-key>"

# Grant App Service access to Key Vault
az webapp identity assign `
  --resource-group rg-mystock3-staging `
  --name mystock3-backend-staging

$principalId = az webapp identity show `
  --resource-group rg-mystock3-staging `
  --name mystock3-backend-staging `
  --query principalId -o tsv

az keyvault set-policy `
  --name mystock3-kv-staging `
  --object-id $principalId `
  --secret-permissions get list
```

---

## Post-Deployment Verification

### Automated Checks

```powershell
# Health check
$response = Invoke-WebRequest -Uri "https://api-staging.mystock3.example.com/health"
Write-Host "Health Status: $($response.Content)"

# Backend version check
$response = Invoke-WebRequest -Uri "https://api-staging.mystock3.example.com/api/v1/docs"
Write-Host "API Docs accessible: $($response.StatusCode -eq 200)"
```

### Manual Verification Checklist

- [ ] **Backend Health**: `/health` endpoint returns `{"status": "healthy"}`
- [ ] **Authentication**: Login/signup working
- [ ] **Watchlist**: CRUD operations functional
- [ ] **Portfolio**: CRUD operations functional
- [ ] **Stock Data**: Alpha Vantage API integration working
- [ ] **Dark Mode**: Theme persistence working
- [ ] **Performance**: API p95 latency <200ms
- [ ] **Error Handling**: 404, 500 errors display properly
- [ ] **Monitoring**: Application Insights receiving telemetry
- [ ] **Rate Limiting**: 429 responses for excessive requests

### Performance Testing (T194)

```powershell
# Load test with 100 concurrent users
cd tests/load

# Using Apache Bench
ab -n 10000 -c 100 -H "Authorization: Bearer <token>" `
  https://api-staging.mystock3.example.com/api/v1/watchlist

# Expected Results:
# - Requests per second: >100
# - p95 latency: <200ms
# - p99 latency: <500ms
# - Error rate: <1%
```

### E2E Testing (T193)

```powershell
# Run Playwright E2E tests
cd frontend
npm run test:e2e

# Expected: All tests passing
# - User signup/login flow
# - Watchlist CRUD operations
# - Portfolio CRUD operations
# - Stock search and data display
# - Theme switching
```

---

## Rollback Procedures

### Quick Rollback (App Service)

```powershell
# List deployment slots
az webapp deployment slot list `
  --resource-group rg-mystock3-staging `
  --name mystock3-backend-staging

# Swap back to previous slot
az webapp deployment slot swap `
  --resource-group rg-mystock3-staging `
  --name mystock3-backend-staging `
  --slot production `
  --target-slot previous
```

### Full Rollback (Infrastructure)

```powershell
# Redeploy previous Bicep template version
git checkout <previous-commit>

az deployment group create `
  --resource-group rg-mystock3-staging `
  --template-file infrastructure/bicep/main.bicep `
  --parameters @parameters.staging.json `
  --name "mystock3-rollback-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
```

### Database Rollback

```powershell
# Restore Cosmos DB from backup
az cosmosdb restore `
  --resource-group rg-mystock3-staging `
  --account-name <cosmos-account> `
  --target-database-account-name <target-account> `
  --restore-timestamp "2025-11-13T10:00:00Z"
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Fails to Start

**Symptoms**: App Service shows "Application Error" or restarts loop

**Solution**:
```powershell
# Check logs
az webapp log tail --resource-group rg-mystock3-staging --name mystock3-backend-staging

# Verify environment variables
az webapp config appsettings list --resource-group rg-mystock3-staging --name mystock3-backend-staging

# Check Python version
az webapp config show --resource-group rg-mystock3-staging --name mystock3-backend-staging --query "linuxFxVersion"
```

#### 2. Cosmos DB Connection Failures

**Symptoms**: 500 errors, "Failed to connect to Cosmos DB"

**Solution**:
```powershell
# Verify firewall rules
az cosmosdb show --resource-group rg-mystock3-staging --name <cosmos-account> --query "ipRules"

# Check connection string
az cosmosdb keys list --resource-group rg-mystock3-staging --name <cosmos-account> --type connection-strings
```

#### 3. Alpha Vantage Rate Limiting

**Symptoms**: "API rate limit exceeded" errors

**Solution**:
- Verify API key is valid
- Check cache hit rate in Application Insights
- Increase cache TTL (currently 1 minute)
- Consider upgrading Alpha Vantage plan

#### 4. Frontend 404 Errors

**Symptoms**: Routes not working after deployment

**Solution**:
```powershell
# Configure URL rewrite for SPA
# Add web.config (IIS) or .htaccess (Apache)
# Or use Azure Static Web Apps routing
```

### Contact Information

- **DevOps Team**: devops@mystock3.example.com
- **On-Call Engineer**: See PagerDuty schedule
- **Emergency Hotline**: +1-555-MYSTOCK

---

## Appendix

### Useful Commands

```powershell
# View App Service logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Restart App Service
az webapp restart --name <app-name> --resource-group <rg-name>

# Scale App Service
az appservice plan update --name <plan-name> --resource-group <rg-name> --sku P2V2

# View Cosmos DB metrics
az monitor metrics list --resource <cosmos-resource-id> --metric "TotalRequests"

# Export Application Insights logs
az monitor app-insights query --app <app-id> --analytics-query "requests | where timestamp > ago(1h)"
```

### Related Documentation

- [Architecture Diagram](../README.md)
- [API Documentation](../specs/001-stock-portfolio-app/contracts/openapi.yaml)
- [Incident Response Guide](./INCIDENTS.md)
- [Database Indexing Strategy](../backend/INDEXING_STRATEGY.md)

---

**End of Runbook**
