// Azure ML workspace + a CPU training cluster for the CT-report pretraining scaffold.
//
// Governance posture (identity-based, no key auth):
//   * The workspace has a SystemAssigned identity and systemDatastoresAuthMode='identity',
//     so the built-in workspaceblobstore reaches the storage account with the workspace MSI
//     instead of stored account keys. This is what makes allowSharedKeyAccess=false on the
//     storage account workable.
//   * The compute cluster ALSO gets a SystemAssigned identity. Azure ML jobs mount input data
//     with the COMPUTE cluster's MSI (not the workspace MSI) -- a bare amlcompute has no
//     identity and hits ScriptExecution.StreamAccess.Authentication / PermissionDenied on
//     mount. roles.bicep grants BOTH MSIs Storage Blob Data roles so mounts succeed.
//   * CPU SKU by default: governed subscriptions routinely have GPU quota = 0 in every family
//     (T4/A100/H100/ND all limit=0). The smoke pipeline runs fine on CPU. Flip computeVmSize
//     to a GPU SKU once a quota increase is granted -- see ADMIN-SETUP.md / scripts/preflight.md.
param namePrefix string
param location string
param storageId string
param keyVaultId string
param appInsightsId string

@description('Training cluster VM size. Default CPU because governed subs usually have GPU quota=0.')
param computeVmSize string = 'Standard_DS3_v2'

@description('Cluster priority. Dedicated avoids eviction; LowPriority is cheap pre-emptible capacity.')
@allowed([ 'Dedicated', 'LowPriority' ])
param computeVmPriority string = 'Dedicated'

@description('Max nodes the CPU cluster can scale to. Scales to zero when idle.')
param computeMaxNodes int = 2

@description('Public network access to the workspace. Disable + use private endpoints in locked-down subs.')
@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'

resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: '${namePrefix}-mlw'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    friendlyName: '${namePrefix} CT-report pretraining'
    storageAccount: storageId
    keyVault: keyVaultId
    applicationInsights: appInsightsId
    systemDatastoresAuthMode: 'identity'
    publicNetworkAccess: publicNetworkAccess
  }
}

@description('CPU training cluster with its own MSI so job data mounts authenticate. Scales to zero.')
resource cpuCluster 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = {
  parent: workspace
  name: 'cpu-cluster'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: computeVmSize
      vmPriority: computeVmPriority
      scaleSettings: {
        minNodeCount: 0
        maxNodeCount: computeMaxNodes
        nodeIdleTimeBeforeScaleDown: 'PT300S'
      }
    }
  }
}

output workspaceName string = workspace.name
output workspacePrincipalId string = workspace.identity.principalId
output computePrincipalId string = cpuCluster.identity.principalId
