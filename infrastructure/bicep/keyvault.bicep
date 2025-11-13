// Key Vault for application secrets

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Resource name suffix')
param resourceSuffix string

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'mys${substring(environment, 0, 3)}kv${take(resourceSuffix, 10)}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
  tags: {
    Environment: environment
    Application: 'MyStock'
  }
}

// Outputs
output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultDnsSuffix string = az.environment().suffixes.keyvaultDns
