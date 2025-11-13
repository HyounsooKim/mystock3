# MyStock Infrastructure

Azure infrastructure provisioning and deployment guide for the MyStock application.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Environments](#environments)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Overview

MyStock infrastructure uses **Azure Bicep** for Infrastructure as Code (IaC), deploying resources to Azure with modular templates for different components:

- **Cosmos DB**: NoSQL database for user data, watchlist, and portfolio
- **Container Apps**: Backend API hosting (FastAPI)
- **Static Web Apps**: Frontend hosting (Vue 3)
- **Key Vault**: Secrets management (API keys, connection strings)
- **Log Analytics + Application Insights**: Monitoring and observability

---

## Prerequisites

### Required Tools

1. **Azure CLI** (v2.50+)
   ```powershell
   # Install
   winget install Microsoft.AzureCLI
   
   # Verify
   az --version
   ```

2. **Azure Bicep CLI**
   ```powershell
   # Install (via Azure CLI)
   az bicep install
   
   # Verify
   az bicep version
   ```

3. **PowerShell 7+**
   ```powershell
   # Verify
   $PSVersionTable.PSVersion
   ```

### Azure Requirements

1. **Active Azure Subscription**
   - Subscription ID
   - Contributor or Owner role

2. **Azure AD Permissions**
   - Create service principals (for CI/CD)
   - Assign roles to resources

3. **Resource Provider Registration**
   ```powershell
   # Register required providers
   az provider register --namespace Microsoft.DocumentDB
   az provider register --namespace Microsoft.App
   az provider register --namespace Microsoft.Web
   az provider register --namespace Microsoft.KeyVault
   az provider register --namespace Microsoft.OperationalInsights
   ```

### Secrets Required

Before deployment, gather:

1. **Alpha Vantage API Key**
   - Sign up: https://www.alphavantage.co/support/#api-key
   - Free tier: 25 requests/day

2. **JWT Secret Key**
   - Generate: `openssl rand -base64 32`
   - Minimum 32 characters

---

## Architecture

### Resource Topology

```
Azure Subscription
└── mystock-{env}-rg (Resource Group)
    ├── mystock-{env}-cosmos (Cosmos DB Account)
    │   └── mystock-db (Database)
    │       ├── users (Container)
    │       ├── watchlist (Container)
    │       └── portfolio (Container)
    ├── mystock-{env}-containerapp-env (Container Apps Environment)
    │   └── mystock-{env}-backend (Backend API)
    ├── mystock-{env}-frontend (Static Web App)
    ├── mystock-{env}-kv (Key Vault)
    ├── mystock-{env}-law (Log Analytics Workspace)
    └── mystock-{env}-ai (Application Insights)
```

### Network Flow

```
User Browser
    ↓
Static Web App (Frontend)
    ↓ HTTPS
Container App (Backend API)
    ↓
    ├→ Cosmos DB (Data)
    ├→ Key Vault (Secrets)
    └→ Alpha Vantage API (Stock Data)
```

---

## Deployment

### Step 1: Login to Azure

```powershell
# Login
az login

# Set subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Verify
az account show
```

### Step 2: Validate Bicep Templates

```powershell
cd infrastructure

# Validate main template
az bicep build --file bicep/main.bicep

# Validate all modules
az bicep build --file bicep/database.bicep
az bicep build --file bicep/backend.bicep
az bicep build --file bicep/frontend.bicep
az bicep build --file bicep/keyvault.bicep
az bicep build --file bicep/monitoring.bicep
```

### Step 3: Deploy Infrastructure

#### Development Environment

```powershell
# Navigate to infrastructure directory
cd C:\Work\Azure\test1\mystock3\infrastructure

# Deploy with PowerShell script
.\deploy-staging.ps1 `
  -SubscriptionId "YOUR_SUBSCRIPTION_ID" `
  -Environment "dev" `
  -Location "koreacentral" `
  -AlphaVantageApiKey "YOUR_API_KEY" `
  -JwtSecretKey "YOUR_JWT_SECRET"
```

#### Staging Environment

```powershell
.\deploy-staging.ps1 `
  -SubscriptionId "YOUR_SUBSCRIPTION_ID" `
  -Environment "staging" `
  -Location "koreacentral" `
  -AlphaVantageApiKey "YOUR_API_KEY" `
  -JwtSecretKey "YOUR_JWT_SECRET"
```

#### Production Environment

```powershell
.\deploy-production.ps1 `
  -SubscriptionId "YOUR_SUBSCRIPTION_ID" `
  -Environment "prod" `
  -Location "koreacentral" `
  -AlphaVantageApiKey "YOUR_API_KEY" `
  -JwtSecretKey "YOUR_JWT_SECRET"
```

### Step 4: Verify Deployment

```powershell
# Check resource group
az group show --name mystock-dev-rg

# List all resources
az resource list --resource-group mystock-dev-rg --output table

# Get backend URL
az containerapp show `
  --name mystock-dev-backend `
  --resource-group mystock-dev-rg `
  --query properties.configuration.ingress.fqdn `
  --output tsv

# Get frontend URL
az staticwebapp show `
  --name mystock-dev-frontend `
  --resource-group mystock-dev-rg `
  --query defaultHostname `
  --output tsv
```

---

## Environments

### Development (`dev`)

**Purpose**: Local development and testing

**Characteristics**:
- Minimal SKU (cost-optimized)
- Public access enabled
- Debug logging enabled
- No SLA guarantees

**Configuration**:
```bicep
environment: 'dev'
location: 'koreacentral'
cosmosDbThroughput: 400 (manual)
containerAppReplicas: 1
```

### Staging (`staging`)

**Purpose**: Pre-production validation

**Characteristics**:
- Production-like configuration
- Isolated from production data
- Performance testing enabled
- SLA monitoring active

**Configuration**:
```bicep
environment: 'staging'
location: 'koreacentral'
cosmosDbThroughput: 1000 (autoscale)
containerAppReplicas: 2
```

### Production (`prod`)

**Purpose**: Live user traffic

**Characteristics**:
- High availability
- Autoscaling enabled
- Enhanced monitoring
- Backup policies active
- Private endpoints (optional)

**Configuration**:
```bicep
environment: 'prod'
location: 'koreacentral'
cosmosDbThroughput: 4000 (autoscale)
containerAppReplicas: 3
```

---

## Monitoring

### Application Insights

**Access**:
```powershell
# Get instrumentation key
az monitor app-insights component show `
  --app mystock-dev-ai `
  --resource-group mystock-dev-rg `
  --query instrumentationKey `
  --output tsv
```

**Key Metrics**:
- API request rate
- Response time (p50, p95, p99)
- Error rate
- Dependency latency (Cosmos DB, Alpha Vantage)

### Log Analytics

**Access**: Azure Portal → Log Analytics Workspace → Logs

**Sample Queries**:

```kql
// API errors in last 24 hours
AppTraces
| where TimeGenerated > ago(24h)
| where SeverityLevel >= 3
| summarize count() by Message, SeverityLevel
| order by count_ desc

// Slow API requests (>200ms)
AppRequests
| where TimeGenerated > ago(1h)
| where DurationMs > 200
| summarize p95=percentile(DurationMs, 95), p99=percentile(DurationMs, 99) by Name
| order by p95 desc

// Cosmos DB request units consumed
AppDependencies
| where TimeGenerated > ago(1h)
| where Type == "Azure DocumentDB"
| summarize TotalRU=sum(todouble(Properties["Request Charge"])) by bin(TimeGenerated, 5m)
| render timechart
```

### Alerts

Configured alerts:
- API error rate > 5%
- API p95 latency > 500ms
- Cosmos DB RU/s > 80% of provisioned
- Container App CPU > 80%
- Container App memory > 80%

---

## Troubleshooting

### Common Issues

#### 1. Bicep Deployment Fails

**Symptom**: `az deployment sub create` returns error

**Causes**:
- Invalid parameter values
- Resource provider not registered
- Insufficient permissions
- Resource name conflicts

**Resolution**:
```powershell
# Check deployment errors
az deployment sub show `
  --name mystock-dev-deployment `
  --query properties.error

# Validate template
az deployment sub validate `
  --location koreacentral `
  --template-file bicep/main.bicep `
  --parameters environment=dev
```

#### 2. Backend Container App Not Starting

**Symptom**: Container app shows "Provisioning failed"

**Causes**:
- Environment variables missing
- Container image pull failure
- Port configuration mismatch

**Resolution**:
```powershell
# Check container logs
az containerapp logs show `
  --name mystock-dev-backend `
  --resource-group mystock-dev-rg `
  --follow

# Check environment variables
az containerapp show `
  --name mystock-dev-backend `
  --resource-group mystock-dev-rg `
  --query properties.configuration.secrets
```

#### 3. Cosmos DB Connection Fails

**Symptom**: Backend returns 500 errors with "Unable to connect to Cosmos DB"

**Causes**:
- Firewall rules blocking Container App IP
- Invalid connection string in Key Vault
- Cosmos DB account not provisioned

**Resolution**:
```powershell
# Check Cosmos DB firewall
az cosmosdb show `
  --name mystock-dev-cosmos `
  --resource-group mystock-dev-rg `
  --query ipRules

# Test connection from Container App
az containerapp exec `
  --name mystock-dev-backend `
  --resource-group mystock-dev-rg `
  --command "python -c 'from azure.cosmos import CosmosClient; print(CosmosClient.from_connection_string(os.environ[\"COSMOS_CONNECTION_STRING\"]))'"
```

#### 4. Frontend Cannot Reach Backend

**Symptom**: Frontend shows "Network Error" or CORS errors

**Causes**:
- CORS not configured in backend
- Backend URL not set in frontend environment
- Backend not publicly accessible

**Resolution**:
```powershell
# Check CORS settings
az containerapp show `
  --name mystock-dev-backend `
  --resource-group mystock-dev-rg `
  --query properties.configuration.ingress.corsPolicy

# Update CORS (if needed)
az containerapp ingress cors update `
  --name mystock-dev-backend `
  --resource-group mystock-dev-rg `
  --allowed-origins "*" `
  --allowed-methods "GET,POST,PUT,DELETE,PATCH,OPTIONS"

# Check backend health
curl https://mystock-dev-backend.FQDN/api/v1/health
```

### Runbooks

For detailed incident response procedures, see:
- [RUNBOOK.md](./RUNBOOK.md) - Operational procedures
- [INCIDENTS.md](./INCIDENTS.md) - Incident response guide

---

## References

### Documentation

- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/)
- [Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Key Vault](https://learn.microsoft.com/azure/key-vault/)

### Project Files

- [plan.md](../specs/001-stock-portfolio-app/plan.md) - Architecture and tech stack
- [spec.md](../specs/001-stock-portfolio-app/spec.md) - Feature specification
- [tasks.md](../specs/001-stock-portfolio-app/tasks.md) - Implementation tasks
- [OpenAPI Spec](../specs/001-stock-portfolio-app/contracts/openapi.yaml) - API contracts

### Deployment Scripts

- `deploy-staging.ps1` - Deploy to dev/staging environment
- `deploy-production.ps1` - Deploy to production environment
- `load-test.ps1` - Run load tests against deployed environment
- `verify-coverage.ps1` - Verify code coverage meets 70% threshold

---

## Cost Estimation

### Development Environment

| Resource | SKU | Monthly Cost (KRW) |
|----------|-----|-------------------|
| Cosmos DB | 400 RU/s manual | ~5,000 |
| Container Apps | 0.5 vCPU, 1GB RAM | ~15,000 |
| Static Web Apps | Free tier | 0 |
| Key Vault | Standard | ~500 |
| Log Analytics | Pay-as-you-go | ~3,000 |
| **Total** | | **~23,500** |

### Production Environment

| Resource | SKU | Monthly Cost (KRW) |
|----------|-----|-------------------|
| Cosmos DB | 4000 RU/s autoscale | ~50,000 |
| Container Apps | 1 vCPU, 2GB RAM x3 | ~90,000 |
| Static Web Apps | Standard tier | ~12,000 |
| Key Vault | Standard | ~500 |
| Log Analytics | Pay-as-you-go | ~15,000 |
| Application Insights | Pay-as-you-go | ~10,000 |
| **Total** | | **~177,500** |

*Estimates based on Korea Central region pricing as of November 2025. Actual costs may vary based on usage.*

---

## Cleanup

### Delete Specific Environment

```powershell
# Delete resource group (deletes all resources)
az group delete --name mystock-dev-rg --yes --no-wait

# Verify deletion
az group exists --name mystock-dev-rg
```

### Delete All Environments

```powershell
# Delete all MyStock resource groups
az group list --query "[?contains(name, 'mystock')].name" -o tsv | ForEach-Object {
  az group delete --name $_ --yes --no-wait
}
```

---

**Last Updated**: 2025-11-13  
**Version**: 1.0.0  
**Maintained By**: MyStock DevOps Team
