// CT-report multimodal pretraining -- Azure ML training substrate (governance-compliant IaC).
//
// Deploys into ONE EXISTING resource group (targetScope = resourceGroup). It provisions only
// what the training pipeline needs -- no Function App, Event Grid, or online endpoint:
//
//   storage.bicep        Storage account (key-less: allowSharedKeyAccess=false, TLS1_2, no public blob)
//   observability.bicep  Key Vault (RBAC-auth) + App Insights (linked to an EXISTING LAW)
//   mlworkspace.bicep    AML workspace (identity-based datastores) + CPU cluster (own MSI)
//   roles.bicep          Data-plane RBAC for workspace MSI, compute MSI, and the deployer
//
// See ADMIN-SETUP.md for the end-to-end admin walkthrough and scripts/preflight.md for the
// subscription checks to run first.

targetScope = 'resourceGroup'

@description('Short lowercase prefix for resource names (e.g. "ctrp"). 2-11 chars.')
@minLength(2)
@maxLength(11)
param namePrefix string = 'ctrp'

@description('Azure region. Keep workspace, storage, and compute in ONE region (AmlCompute is region-bound).')
param location string = resourceGroup().location

@description('Resource id of an EXISTING Log Analytics workspace to link App Insights to. Required in governed subs that deny Log Analytics workspace creation.')
param existingLogAnalyticsWorkspaceId string = ''

@description('Object id of the human or service principal that will operate/demo the workspace. Empty = grant no deployer roles (managed identities are still granted).')
param deployerPrincipalId string = ''

@description('Principal type of the deployer.')
@allowed([ 'User', 'ServicePrincipal', 'Group' ])
param deployerPrincipalType string = 'User'

@description('Training cluster VM size. Default CPU -- governed subs typically have GPU quota=0.')
param computeVmSize string = 'Standard_DS3_v2'

@description('Training cluster priority.')
@allowed([ 'Dedicated', 'LowPriority' ])
param computeVmPriority string = 'Dedicated'

@description('Public network access for storage + workspace. Guardrails may force Disabled.')
@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'

var suffix = uniqueString(resourceGroup().id)
var storageName = toLower('${namePrefix}st${substring(suffix, 0, 8)}')

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: storageName
    location: location
    containers: [ 'ct-report-gold' ]
    publicNetworkAccess: publicNetworkAccess
  }
}

module observability 'modules/observability.bicep' = {
  name: 'observability'
  params: {
    namePrefix: namePrefix
    location: location
    suffix: suffix
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
  }
}

module mlworkspace 'modules/mlworkspace.bicep' = {
  name: 'mlworkspace'
  params: {
    namePrefix: namePrefix
    location: location
    storageId: storage.outputs.id
    keyVaultId: observability.outputs.keyVaultId
    appInsightsId: observability.outputs.appInsightsId
    computeVmSize: computeVmSize
    computeVmPriority: computeVmPriority
    publicNetworkAccess: publicNetworkAccess
  }
}

module roles 'modules/roles.bicep' = {
  name: 'roles'
  params: {
    storageName: storage.outputs.name
    workspaceName: mlworkspace.outputs.workspaceName
    keyVaultName: observability.outputs.keyVaultName
    computePrincipalId: mlworkspace.outputs.computePrincipalId
    deployerPrincipalId: deployerPrincipalId
    deployerPrincipalType: deployerPrincipalType
  }
}

output workspaceName string = mlworkspace.outputs.workspaceName
output storageAccountName string = storage.outputs.name
output keyVaultName string = observability.outputs.keyVaultName
output resourceGroupName string = resourceGroup().name
