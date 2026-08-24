// Key Vault + Application Insights for the Azure ML workspace.
//
// Governance posture:
//   * Key Vault uses enableRbacAuthorization=true -> NO access-policy / key-based grants.
//     Secret access is data-plane RBAC only (Key Vault Secrets Officer, granted in roles.bicep).
//   * App Insights links to an EXISTING Log Analytics workspace when one is supplied.
//     Some governed subscriptions deny creating Microsoft.OperationalInsights/workspaces via
//     policy, so pass existingLogAnalyticsWorkspaceId there; leave empty only in a sandbox sub
//     where workspace creation is allowed.
param namePrefix string
param location string

@description('6+ char uniqueness suffix (e.g. take from uniqueString(resourceGroup().id)).')
param suffix string

@description('Resource id of an EXISTING Log Analytics workspace. Empty = create a new one (blocked by policy in some governed subs).')
param existingLogAnalyticsWorkspaceId string = ''

var createLaw = empty(existingLogAnalyticsWorkspaceId)

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: toLower('${namePrefix}kv${substring(suffix, 0, 6)}')
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
  }
}

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (createLaw) {
  name: '${namePrefix}-law'
  location: location
  properties: { sku: { name: 'PerGB2018' } }
}

var workspaceId = createLaw ? law.id : existingLogAnalyticsWorkspaceId

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namePrefix}-appi'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspaceId
  }
}

output keyVaultId string = kv.id
output keyVaultName string = kv.name
output appInsightsId string = appi.id
