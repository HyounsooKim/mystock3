// Frontend - Azure Static Web Apps

@description('Environment name')
param environment string

@description('Resource name suffix')
param resourceSuffix string

@description('Backend API URL')
param backendUrl string

// Static Web App
resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: 'mystock-${environment}-web-${resourceSuffix}'
  location: 'eastasia'  // Static Web Apps not available in koreacentral
  sku: {
    name: environment == 'prod' ? 'Standard' : 'Free'
    tier: environment == 'prod' ? 'Standard' : 'Free'
  }
  properties: {
    buildProperties: {
      appLocation: '/frontend'
      apiLocation: ''
      outputLocation: 'dist'
    }
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
  }
  tags: {
    Environment: environment
    Application: 'MyStock'
  }
}

// Static Web App Config (stored as app settings)
resource staticWebAppConfig 'Microsoft.Web/staticSites/config@2023-01-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    VITE_API_BASE_URL: backendUrl
    VITE_ENVIRONMENT: environment
  }
}

// Outputs
output frontendUrl string = 'https://${staticWebApp.properties.defaultHostname}'
output staticWebAppName string = staticWebApp.name
output staticWebAppId string = staticWebApp.id
