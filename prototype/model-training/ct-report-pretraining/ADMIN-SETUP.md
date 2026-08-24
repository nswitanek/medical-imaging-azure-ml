# Admin setup — provision the Azure ML workspace with IaC

This section is for an **administrator** provisioning the training substrate for the
CT-report pretraining scaffold into **one existing resource group**, under the governance
constraints of a policy-governed / locked-down subscription. Everything is identity-based with **no
key-based auth**.

## What gets provisioned

All in [`infra/`](infra/), scoped to the existing RG (`targetScope = 'resourceGroup'`):

| Resource | Module | Governance posture |
|---|---|---|
| Storage account | `modules/storage.bicep` | `allowSharedKeyAccess=false` (no keys), `allowBlobPublicAccess=false`, TLS1.2 |
| Key Vault | `modules/observability.bicep` | `enableRbacAuthorization=true` (no access policies) |
| Application Insights | `modules/observability.bicep` | Linked to an **existing** Log Analytics workspace |
| Azure ML workspace | `modules/mlworkspace.bicep` | SystemAssigned identity, `systemDatastoresAuthMode=identity` |
| CPU compute cluster | `modules/mlworkspace.bicep` | Own SystemAssigned identity so job mounts authenticate |
| Data-plane RBAC | `modules/roles.bicep` | Blob Data / AML Data Scientist / KV Secrets Officer to the MSIs + deployer |

No Function App, Event Grid, or online endpoint — this is the **training** substrate only.

## Why identity-based (the failures this avoids)

- **Control-plane ≠ data-plane.** Owner/Contributor does **not** grant blob, AML, or Key Vault
  data access — you get a 403 without the explicit Storage Blob Data / AML / KV roles in
  `roles.bicep`.
- **Job mounts use the *compute* MSI**, not the workspace MSI. A bare `amlcompute` has no
  identity and fails with `ScriptExecution.StreamAccess.Authentication`. The cluster here has
  its own SystemAssigned identity, granted Storage Blob Data Contributor.
- **Key-less storage needs identity datastores.** With `allowSharedKeyAccess=false`, the default
  `workspaceblobstore` only works because `systemDatastoresAuthMode=identity`. Real data must go
  through the credential-less datastore ([`azureml/datastore.yml`](azureml/datastore.yml)), never
  a bare blob URL.

## Prerequisites

1. Run every check in [`scripts/preflight.md`](scripts/preflight.md) first.
2. You need **Owner** or **User Access Administrator** on the RG (to create role assignments).
3. Have ready: the RG name, region, and an **existing Log Analytics workspace id**.

## Deploy

```bash
RG=<your-existing-rg>
LAW_ID=<existing-log-analytics-workspace-resource-id>

# Object id of whoever will operate/demo the workspace. On a locked-down host where Graph is
# unreachable, decode it from the ARM token instead of `az ad signed-in-user`:
DEPLOYER_OID=$(az account get-access-token --query accessToken -o tsv | cut -d. -f2 \
  | base64 -d 2>/dev/null | tr ',' '\n' | grep -o '"oid":"[^"]*"' | cut -d'"' -f4)

az deployment group create \
  --resource-group "$RG" \
  --template-file infra/main.bicep \
  --parameters \
      namePrefix=ctrp \
      existingLogAnalyticsWorkspaceId="$LAW_ID" \
      deployerPrincipalId="$DEPLOYER_OID" \
      deployerPrincipalType=User
```

There is a ready-made [`deploy.sh`](infra/deploy.sh) that wires these together.

> **Guardrailed storage.** If the pre-flight probe (preflight §5) showed public network access
> gets forced off, add `--parameters publicNetworkAccess=Disabled` and reach the account/workspace
> over a private endpoint.

> **Deployer is a CI service principal?** Set `deployerPrincipalType=ServicePrincipal`. Leave
> `deployerPrincipalId` empty to grant no human roles (the MSIs are still wired up).

## Post-deploy verification

```bash
WS=$(az deployment group show -g "$RG" -n main --query properties.outputs.workspaceName.value -o tsv)
SA=$(az deployment group show -g "$RG" -n main --query properties.outputs.storageAccountName.value -o tsv)

az ml workspace show -n "$WS" -g "$RG" --query "{name:name, identity:identity.type}" -o table
az ml compute show   -n cpu-cluster -g "$RG" -w "$WS" --query "{name:name, identity:identity.type, state:provisioningState}" -o table
az role assignment list --scope "$(az storage account show -n $SA -g $RG --query id -o tsv)" \
  --query "[].{who:principalId, role:roleDefinitionName}" -o table
```

You should see the workspace + compute both `SystemAssigned`. On the storage account you'll see
Storage Blob Data Contributor for the **compute** MSI (granted by `roles.bicep`) plus a
Contributor + File Data Privileged Contributor that **Azure ML auto-assigns to the workspace
MSI** because the workspace uses identity-based datastores — the template deliberately does not
grant the workspace MSI itself (doing so fails with `RoleAssignmentExists`).

## GPU

The cluster is CPU (`Standard_DS3_v2`) by default because governed subs usually have GPU quota
`= 0`. Once a quota increase is granted for a GPU SKU that preflight §4 shows as offerable,
redeploy with `--parameters computeVmSize=Standard_NC24ads_A100_v4` (keep the RG/region fixed).

## Hand off to the data scientist

Once provisioned, submitting jobs is covered in [`scripts/submit.md`](scripts/submit.md):
register the credential-less datastore, then `az ml job create -f azureml/pipeline.yml`.
