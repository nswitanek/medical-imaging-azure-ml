# Subscription pre-flight — run BEFORE deploying `infra/main.bicep`

These checks catch the governance failures that otherwise surface mid-deploy or mid-training.
Run them against the target subscription + the ONE resource group you were given. Commands are
Azure CLI (Cloud Shell / bash); PowerShell equivalents are noted where they differ.

## 0. Context

```bash
az account show --query "{sub:id, tenant:tenantId, user:user.name}" -o table
RG=<your-existing-rg>
LOC=$(az group show -n "$RG" --query location -o tsv)
```

> Some tenants sign you in as a **read-only guest** — if `user.name` looks
> foreign or writes 403, you're in the wrong context.

## 1. You can create role assignments

`infra/roles.bicep` creates role assignments, which requires **Owner** or **User Access
Administrator** on the RG — Contributor is NOT enough.

```bash
az role assignment list --assignee "$(az ad signed-in-user show --query id -o tsv)" \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RG" \
  --query "[].roleDefinitionName" -o tsv
```

Expect `Owner` or `User Access Administrator`. If neither, ask the RG owner to run the deploy
or to grant you UAA on the RG.

## 2. Resource providers are registered

```bash
for p in Microsoft.MachineLearningServices Microsoft.Storage Microsoft.KeyVault \
         Microsoft.Insights Microsoft.OperationalInsights; do
  echo "$p -> $(az provider show -n $p --query registrationState -o tsv)"
done
# Register any that say NotRegistered (needs subscription-level rights):
# az provider register -n Microsoft.MachineLearningServices --wait
```

## 3. Log Analytics workspace id

Governed subs deny creating `Microsoft.OperationalInsights/workspaces`. Find an existing one to
pass as `existingLogAnalyticsWorkspaceId`:

```bash
az monitor log-analytics workspace list --query "[].{name:name, id:id, rg:resourceGroup}" -o table
```

If none exists and you can't create one, ask the platform team for a workspace id.

## 4. Compute quota AND offerability

Two independent gates — check both. GPU quota is frequently **0** in governed subs.

```bash
# (a) Quota — cores available per family:
az vm list-usage -l "$LOC" --query "[?contains(localName,'DSv2') || contains(localName,'NCADS')].{name:localName, used:currentValue, limit:limit}" -o table

# (b) Offerability — is the SKU even sellable here (empty restrictions == usable):
az vm list-skus -l "$LOC" --size Standard_DS3_v2 --query "[].{name:name, restrictions:restrictions}" -o json
```

- Default deploy uses **Standard_DS3_v2 (CPU)** — usually quota-clear everywhere.
- For GPU, confirm a specific SKU (e.g. `Standard_NC24ads_A100_v4`) shows `limit > 0` AND
  `restrictions: []` BEFORE setting `computeVmSize`. If `limit == 0`, file a quota increase and
  stay on CPU until granted.

## 5. Storage guardrail probe (throwaway)

An Azure Policy (common in governed subs) can silently force `publicNetworkAccess=Disabled`
and disable shared keys. Our template already sets `allowSharedKeyAccess=false`, but probe
whether public network access will stick:

```bash
az storage account create -n probe$RANDOM -g "$RG" -l "$LOC" --sku Standard_LRS \
  --allow-shared-key-access false --public-network-access Enabled -o none && echo "created"
az storage account show -n <that-name> -g "$RG" --query "{pna:publicNetworkAccess, shared:allowSharedKeyAccess}" -o table
# If pna comes back Disabled, plan on private-endpoint access and deploy with
#   --parameters publicNetworkAccess=Disabled
az storage account delete -n <that-name> -g "$RG" -y
```

## 6. Ready

All green → proceed to [`ADMIN-SETUP.md`](../ADMIN-SETUP.md) to deploy the Bicep.
