// Data-plane RBAC for the CT-report training scaffold.
//
// Why this module exists: control-plane roles (Owner/Contributor) do NOT grant blob-data, AML,
// or Key Vault-secret access. Because the storage account has allowSharedKeyAccess=false, EVERY
// identity that touches training data must hold an explicit Storage Blob Data role or it hits a
// 403 / mount PermissionDenied. Two principals need explicit grants here:
//   1. compute-cluster MSI -> mounts job inputs/outputs at run time. AML does NOT grant this one
//      automatically, which is the classic ScriptExecution.StreamAccess.Authentication gotcha.
//   2. the deployer (optional) -> browse blobs, submit jobs, read secrets from the portal/CLI.
//
// NOTE: the WORKSPACE MSI is intentionally NOT granted here. When the workspace is created with
// systemDatastoresAuthMode='identity', Azure ML AUTO-assigns the workspace MSI the storage roles
// it needs (Storage Blob Data Contributor + File Data Privileged Contributor) and Key Vault
// Administrator. Granting Blob Data Contributor to it again fails the deploy with
// RoleAssignmentExists, so we leave it to AML.
//
// Creating role assignments requires the deployer to be Owner or User Access Administrator on
// the RG (Contributor is NOT enough).

@description('Storage account name (existing, created by storage.bicep).')
param storageName string
@description('Azure ML workspace name (existing, created by mlworkspace.bicep).')
param workspaceName string
@description('Key Vault name (existing, created by observability.bicep).')
param keyVaultName string

@description('Compute cluster system-assigned identity principal id.')
param computePrincipalId string

@description('Object id of the human/SP deployer to grant demo-time data-plane access. Empty = skip.')
param deployerPrincipalId string = ''
@allowed([ 'User', 'ServicePrincipal', 'Group' ])
param deployerPrincipalType string = 'User'

// Built-in role definition GUIDs.
var blobDataContributor = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'    // Storage Blob Data Contributor
var blobDataOwner = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'          // Storage Blob Data Owner
var amlDataScientist = 'f6c7c914-8db3-469d-8ca1-694a8f32e121'       // AzureML Data Scientist
var keyVaultSecretsOfficer = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7' // Key Vault Secrets Officer

resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageName
}
resource mlw 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: workspaceName
}
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// --- Compute cluster MSI (always granted; job data mounts fail without it) ---

resource computeBlobGrant 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sa.id, computePrincipalId, blobDataContributor)
  scope: sa
  properties: {
    principalId: computePrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', blobDataContributor)
    principalType: 'ServicePrincipal'
  }
}

// --- Deployer (optional: skipped entirely when deployerPrincipalId is empty) ---

var grantDeployer = !empty(deployerPrincipalId)

resource deployerBlobGrant 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantDeployer) {
  name: guid(sa.id, deployerPrincipalId, blobDataOwner)
  scope: sa
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', blobDataOwner)
    principalType: deployerPrincipalType
  }
}

resource deployerMlGrant 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantDeployer) {
  name: guid(mlw.id, deployerPrincipalId, amlDataScientist)
  scope: mlw
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', amlDataScientist)
    principalType: deployerPrincipalType
  }
}

resource deployerKvGrant 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantDeployer) {
  name: guid(kv.id, deployerPrincipalId, keyVaultSecretsOfficer)
  scope: kv
  properties: {
    principalId: deployerPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsOfficer)
    principalType: deployerPrincipalType
  }
}
