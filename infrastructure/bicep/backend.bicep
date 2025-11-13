// Backend API - Azure Container Apps

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Resource name suffix')
param resourceSuffix string

@description('Cosmos DB endpoint')
param cosmosEndpoint string

@description('Key Vault name')
param keyVaultName string

@description('Key Vault DNS suffix')
param keyVaultDnsSuffix string

@description('Log Analytics workspace ID')
param logAnalyticsWorkspaceId string

@description('Application Insights connection string')
@secure()
param appInsightsConnectionString string

// Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'mys${substring(environment, 0, 3)}env${take(resourceSuffix, 8)}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2022-10-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2022-10-01').primarySharedKey
      }
    }
  }
  tags: {
    Environment: environment
    Application: 'MyStock'
  }
}

// Backend Container App
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'mys${substring(environment, 0, 3)}api${take(resourceSuffix, 8)}'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
        corsPolicy: {
          allowedOrigins: environment == 'prod' ? [
            'https://mystock-${environment}-web-${resourceSuffix}.azurestaticapps.net'
          ] : ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: true
        }
      }
      secrets: [
        {
          name: 'app-insights-connection-string'
          value: appInsightsConnectionString
        }
      ]
      registries: []
    }
    template: {
      containers: [
        {
          name: 'api'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - will be updated by CI/CD
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'MYSTOCK3_COSMOS_ENDPOINT'
              value: cosmosEndpoint
            }
            {
              name: 'MYSTOCK3_KEYVAULT_URI'
              value: 'https://${keyVaultName}${keyVaultDnsSuffix}/'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'app-insights-connection-string'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
  tags: {
    Environment: environment
    Application: 'MyStock'
  }
}

// Key Vault Access for Backend Managed Identity
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Role Assignment - Key Vault Secrets User
resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, backendApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: backendApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output backendPrincipalId string = backendApp.identity.principalId
