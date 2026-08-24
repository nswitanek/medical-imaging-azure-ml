#!/usr/bin/env bash
# Deploy the CT-report training substrate into an existing resource group.
# Governance-compliant (identity-based, no key auth). See ../ADMIN-SETUP.md.
#
# Usage:
#   RG=<rg> LAW_ID=<log-analytics-id> ./deploy.sh
# Optional overrides:
#   NAME_PREFIX=ctrp COMPUTE_VM_SIZE=Standard_DS3_v2 PUBLIC_NET=Enabled DEPLOYER_TYPE=User
set -euo pipefail

: "${RG:?Set RG to the existing resource group name}"
: "${LAW_ID:?Set LAW_ID to an existing Log Analytics workspace resource id (governed subs often deny creating one)}"
NAME_PREFIX="${NAME_PREFIX:-ctrp}"
COMPUTE_VM_SIZE="${COMPUTE_VM_SIZE:-Standard_DS3_v2}"
PUBLIC_NET="${PUBLIC_NET:-Enabled}"
DEPLOYER_TYPE="${DEPLOYER_TYPE:-User}"

# Deployer object id. Prefer the Graph-free path (works on locked-down hosts): decode the "oid"
# claim from the ARM access token. Override by exporting DEPLOYER_OID yourself.
if [[ -z "${DEPLOYER_OID:-}" ]]; then
  DEPLOYER_OID=$(az account get-access-token --query accessToken -o tsv \
    | cut -d. -f2 | base64 -d 2>/dev/null | tr ',' '\n' \
    | grep -o '"oid":"[^"]*"' | cut -d'"' -f4 || true)
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "RG=$RG  prefix=$NAME_PREFIX  vm=$COMPUTE_VM_SIZE  publicNet=$PUBLIC_NET  deployer=$DEPLOYER_OID"

az deployment group create \
  --resource-group "$RG" \
  --template-file "$SCRIPT_DIR/main.bicep" \
  --parameters \
      namePrefix="$NAME_PREFIX" \
      existingLogAnalyticsWorkspaceId="$LAW_ID" \
      deployerPrincipalId="$DEPLOYER_OID" \
      deployerPrincipalType="$DEPLOYER_TYPE" \
      computeVmSize="$COMPUTE_VM_SIZE" \
      publicNetworkAccess="$PUBLIC_NET"
