// Monitoring Infrastructure - Log Analytics + Application Insights

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Resource name suffix')
param resourceSuffix string

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'mystock-${environment}-logs-${resourceSuffix}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: environment == 'prod' ? 90 : 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
  tags: {
    Environment: environment
    Application: 'MyStock'
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'mystock-${environment}-ai-${resourceSuffix}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: {
    Environment: environment
    Application: 'MyStock'
  }
}

// Outputs
output logAnalyticsWorkspaceId string = logAnalytics.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
