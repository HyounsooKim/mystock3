// MyStock - Main Infrastructure Template
// Provisions all Azure resources for the application

targetScope = 'subscription'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for resources')
param location string = 'koreacentral'

@description('Unique suffix for resource names')
param resourceSuffix string = uniqueString(subscription().subscriptionId, environment)

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'mystock-${environment}-rg'
  location: location
  tags: {
    Environment: environment
    Application: 'MyStock'
    ManagedBy: 'Bicep'
  }
}

// Monitoring (Log Analytics + Application Insights)
module monitoring './monitoring.bicep' = {
  name: 'monitoring-deployment'
  scope: rg
  params: {
    environment: environment
    location: location
    resourceSuffix: resourceSuffix
  }
}

// Key Vault for secrets
module keyVault './keyvault.bicep' = {
  name: 'keyvault-deployment'
  scope: rg
  params: {
    environment: environment
    location: location
    resourceSuffix: resourceSuffix
  }
}

// Cosmos DB
module database './database.bicep' = {
  name: 'database-deployment'
  scope: rg
  params: {
    environment: environment
    location: location
    resourceSuffix: resourceSuffix
  }
}

// Backend (Container Apps)
module backend './backend.bicep' = {
  name: 'backend-deployment'
  scope: rg
  params: {
    environment: environment
    location: location
    resourceSuffix: resourceSuffix
    cosmosEndpoint: database.outputs.cosmosEndpoint
    keyVaultName: keyVault.outputs.keyVaultName
    keyVaultDnsSuffix: keyVault.outputs.keyVaultDnsSuffix
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
  }
}

// Frontend (Static Web Apps)
module frontend './frontend.bicep' = {
  name: 'frontend-deployment'
  scope: rg
  params: {
    environment: environment
    resourceSuffix: resourceSuffix
    backendUrl: backend.outputs.backendUrl
  }
}

// Outputs
output resourceGroupName string = rg.name
output backendUrl string = backend.outputs.backendUrl
output frontendUrl string = frontend.outputs.frontendUrl
output cosmosEndpoint string = database.outputs.cosmosEndpoint
output keyVaultName string = keyVault.outputs.keyVaultName
