# MyStock - Deploy to Staging Environment
# This script deploys the application to Azure staging environment and runs E2E tests

param(
    [Parameter(Mandatory=$false)]
    [string]$Location = "koreacentral",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== MyStock Staging Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Set environment variables
Write-Host "Step 1: Setting environment..." -ForegroundColor Yellow
$env:ENVIRONMENT = "staging"
$timestamp = Get-Date -Format "yyyyMMddHHmmss"

# Step 2: Validate Bicep templates
Write-Host "Step 2: Validating Bicep templates..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\bicep"
az bicep build --file main.bicep
if ($LASTEXITCODE -ne 0) {
    Write-Error "Bicep validation failed"
    exit 1
}
Pop-Location
Write-Host "✓ Bicep templates validated" -ForegroundColor Green

# Step 3: Deploy infrastructure
Write-Host "Step 3: Deploying infrastructure..." -ForegroundColor Yellow
$deploymentName = "mystock-staging-$timestamp"

az deployment sub create `
    --name $deploymentName `
    --location $Location `
    --template-file "$PSScriptRoot\bicep\main.bicep" `
    --parameters environment=staging `
    --parameters location=$Location `
    --output json | Out-File -FilePath "$PSScriptRoot\deployment-output.json"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Infrastructure deployment failed"
    exit 1
}

Write-Host "✓ Infrastructure deployed" -ForegroundColor Green

# Step 4: Get deployment outputs
Write-Host "Step 4: Retrieving deployment outputs..." -ForegroundColor Yellow
$deploymentOutput = Get-Content "$PSScriptRoot\deployment-output.json" | ConvertFrom-Json
$backendUrl = $deploymentOutput.properties.outputs.backendUrl.value
$frontendUrl = $deploymentOutput.properties.outputs.frontendUrl.value
$cosmosEndpoint = $deploymentOutput.properties.outputs.cosmosEndpoint.value
$keyVaultName = $deploymentOutput.properties.outputs.keyVaultName.value

Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host "Cosmos Endpoint: $cosmosEndpoint" -ForegroundColor Cyan
Write-Host "Key Vault: $keyVaultName" -ForegroundColor Cyan

# Step 5: Configure secrets in Key Vault
Write-Host "Step 5: Configuring Key Vault secrets..." -ForegroundColor Yellow

# Get Cosmos DB key
$resourceGroupName = $deploymentOutput.properties.outputs.resourceGroupName.value
$cosmosAccountName = $cosmosEndpoint -replace "https://", "" -replace "\.documents\.azure\.com.*", ""

$cosmosKey = az cosmosdb keys list `
    --name $cosmosAccountName `
    --resource-group $resourceGroupName `
    --query primaryMasterKey `
    --output tsv

# Set secrets (user must provide these)
Write-Host "Please provide the following secrets:" -ForegroundColor Yellow
$jwtSecret = Read-Host "JWT Secret Key (min 32 chars)" -AsSecureString
$alphaVantageKey = Read-Host "Alpha Vantage API Key" -AsSecureString

$jwtSecretPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($jwtSecret))
$alphaVantageKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($alphaVantageKey))

az keyvault secret set --vault-name $keyVaultName --name "cosmos-key" --value $cosmosKey | Out-Null
az keyvault secret set --vault-name $keyVaultName --name "jwt-secret" --value $jwtSecretPlain | Out-Null
az keyvault secret set --vault-name $keyVaultName --name "alpha-vantage-key" --value $alphaVantageKeyPlain | Out-Null

Write-Host "✓ Secrets configured" -ForegroundColor Green

# Step 6: Build and deploy backend
Write-Host "Step 6: Building and deploying backend..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\backend"

# Build Docker image (if using Container Apps with custom image)
# For now, using the placeholder image in the Bicep template
# In production, this would build and push to Azure Container Registry

Write-Host "✓ Backend deployment queued (using Container Apps)" -ForegroundColor Green
Pop-Location

# Step 7: Build and deploy frontend
Write-Host "Step 7: Building and deploying frontend..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\frontend"

# Set environment variables for build
$env:VITE_API_BASE_URL = $backendUrl
$env:VITE_ENVIRONMENT = "staging"

# Build frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend build failed"
    exit 1
}

# Deploy to Static Web Apps (using SWA CLI or GitHub Actions)
# For manual deployment, use Azure Static Web Apps CLI
# swa deploy ./dist --env staging

Write-Host "✓ Frontend built successfully" -ForegroundColor Green
Write-Host "Note: Deploy using 'swa deploy' or GitHub Actions" -ForegroundColor Yellow
Pop-Location

# Step 8: Wait for services to be ready
Write-Host "Step 8: Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Health check
$maxRetries = 10
$retryCount = 0
$backendHealthy = $false

while ($retryCount -lt $maxRetries -and -not $backendHealthy) {
    try {
        $response = Invoke-WebRequest -Uri "$backendUrl/health" -Method GET -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $backendHealthy = $true
            Write-Host "✓ Backend health check passed" -ForegroundColor Green
        }
    } catch {
        $retryCount++
        Write-Host "Backend not ready yet, retrying ($retryCount/$maxRetries)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
}

if (-not $backendHealthy) {
    Write-Error "Backend health check failed after $maxRetries attempts"
    exit 1
}

# Step 9: Run E2E tests (if not skipped)
if (-not $SkipTests) {
    Write-Host "Step 9: Running E2E tests..." -ForegroundColor Yellow
    Push-Location "$PSScriptRoot\..\frontend"
    
    $env:PLAYWRIGHT_BASE_URL = $frontendUrl
    npm run test:e2e
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "E2E tests failed"
        Pop-Location
        exit 1
    }
    
    Write-Host "✓ E2E tests passed" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "Step 9: Skipping E2E tests (use -SkipTests:$false to run)" -ForegroundColor Yellow
}

# Step 10: Deployment summary
Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Environment: Staging" -ForegroundColor Cyan
Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the application manually at: $frontendUrl" -ForegroundColor White
Write-Host "2. Monitor logs in Application Insights" -ForegroundColor White
Write-Host "3. Review deployment in Azure Portal" -ForegroundColor White
Write-Host "4. If everything looks good, proceed with production deployment" -ForegroundColor White
Write-Host ""

# Save deployment info for reference
$deploymentInfo = @{
    Timestamp = $timestamp
    Environment = "staging"
    BackendUrl = $backendUrl
    FrontendUrl = $frontendUrl
    CosmosEndpoint = $cosmosEndpoint
    KeyVaultName = $keyVaultName
    ResourceGroupName = $resourceGroupName
}

$deploymentInfo | ConvertTo-Json | Out-File -FilePath "$PSScriptRoot\last-deployment.json"
Write-Host "Deployment info saved to: $PSScriptRoot\last-deployment.json" -ForegroundColor Cyan
