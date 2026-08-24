// Workspace default storage account for the CT-report training scaffold.
//
// Governance posture (typical of a policy-governed / locked-down subscription):
//   * allowSharedKeyAccess = false  -> NO key-based auth. Every caller (the workspace MSI,
//     the compute-cluster MSI, and the deployer) reaches blob data purely through Entra ID +
//     data-plane RBAC. This is why mlworkspace.bicep sets systemDatastoresAuthMode='identity'
//     and roles.bicep grants Storage Blob Data roles instead of handing out keys.
//   * allowBlobPublicAccess = false and minimumTlsVersion = TLS1_2 satisfy common
//     transport-security / no-public-blob policies.
//   * publicNetworkAccess is a param: some subscriptions have an Azure Policy that may force it
//     to 'Disabled' regardless -- in that case reach the account over a private endpoint.
@description('Storage account name (globally unique, 3-24 lowercase alphanumerics).')
@minLength(3)
@maxLength(24)
param name string
param location string

@description('Blob containers to create up front.')
param containers array = []

@description('Set to Disabled to require private-endpoint access. Guardrailed subscriptions may force this.')
@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'

resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: name
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    allowSharedKeyAccess: false
    publicNetworkAccess: publicNetworkAccess
  }
}

resource blob 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: sa
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [for c in containers: {
  parent: blob
  name: c
  properties: { publicAccess: 'None' }
}]

output id string = sa.id
output name string = sa.name
