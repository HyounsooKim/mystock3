// Cosmos DB NoSQL Database

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Resource name suffix')
param resourceSuffix string

// Cosmos DB Account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: 'mystock-${environment}-cosmos-${resourceSuffix}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: environment == 'prod'
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: environment == 'prod' ? 'Continuous7Days' : 'Continuous7Days'
      }
    }
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    publicNetworkAccess: 'Enabled'
  }
  tags: {
    Environment: environment
    Application: 'MyStock'
  }
}

// Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: 'mystock'
  properties: {
    resource: {
      id: 'mystock'
    }
  }
}

// Users Container
resource usersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'users'
  properties: {
    resource: {
      id: 'users'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: ['/email']
          }
        ]
      }
    }
  }
}

// Watchlist Items Container
resource watchlistContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'watchlist_items'
  properties: {
    resource: {
      id: 'watchlist_items'
      partitionKey: {
        paths: ['/user_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
        compositeIndexes: [
          [
            {
              path: '/user_id'
              order: 'ascending'
            }
            {
              path: '/display_order'
              order: 'ascending'
            }
          ]
        ]
      }
    }
  }
}

// Portfolio Entries Container
resource portfolioContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'portfolio_entries'
  properties: {
    resource: {
      id: 'portfolio_entries'
      partitionKey: {
        paths: ['/user_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
        compositeIndexes: [
          [
            {
              path: '/user_id'
              order: 'ascending'
            }
            {
              path: '/symbol'
              order: 'ascending'
            }
            {
              path: '/category'
              order: 'ascending'
            }
          ]
        ]
      }
    }
  }
}

// Outputs
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosAccountName string = cosmosAccount.name
output databaseName string = database.name
