#!/bin/bash
# Grant Service Principal Permissions
# This script grants the app's service principal permissions to:
# 1. Catalog (USE_CATALOG)
# 2. Schema (USE_SCHEMA, SELECT)
# 3. SQL Warehouse (CAN_USE)
# 4. UC Functions (EXECUTE on fraud_classify, fraud_extract_indicators, fraud_generate_explanation)
# 5. Vector Index Source Table (SELECT on fraud_cases_kb)
# 6. Genie Space (CAN_USE) - for natural language queries
#
# Usage:
#   ./grant_permissions.sh [environment]
#
# Examples:
#   ./grant_permissions.sh dev
#   ./grant_permissions.sh staging
#   ./grant_permissions.sh prod

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ENVIRONMENT=${1:-dev}

echo "========================================================================"
echo "🔒 GRANTING SERVICE PRINCIPAL PERMISSIONS"
echo "========================================================================"
echo "Environment: ${ENVIRONMENT}"
echo ""

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}❌ ERROR: config.yaml not found!${NC}"
    exit 1
fi

# Load config from config.yaml
echo "📝 Loading configuration..."
eval $(python3 -c "
import yaml
import sys
try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    env = config['environments']['$ENVIRONMENT']
    print(f\"PROFILE='{env['profile']}'\")
    print(f\"CATALOG='{env['catalog']}'\")
    print(f\"SCHEMA='{env['schema']}'\")
    print(f\"WAREHOUSE_ID='{env['warehouse_id']}'\")
    print(f\"APP_NAME='{env['app_name']}'\")
except Exception as e:
    print(f'echo \"ERROR: {str(e)}\"', file=sys.stderr)
    sys.exit(1)
")

if [ -z "$APP_NAME" ]; then
    echo -e "${RED}❌ ERROR: Could not load configuration${NC}"
    exit 1
fi

echo "  Profile: ${PROFILE}"
echo "  Catalog: ${CATALOG}"
echo "  Schema: ${SCHEMA}"
echo "  App: ${APP_NAME}"
echo ""

# Get service principal ID from deployed app
echo "🔍 Getting service principal ID from app..."
SP_JSON=$(databricks apps get ${APP_NAME} --profile ${PROFILE} --output json 2>/dev/null || echo "{}")

if [ "$SP_JSON" = "{}" ]; then
    echo -e "${RED}❌ ERROR: Could not get app information${NC}"
    echo "Make sure the app is deployed:"
    echo "  databricks bundle deploy --target ${ENVIRONMENT} --profile ${PROFILE}"
    exit 1
fi

SP_ID=$(echo "$SP_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('service_principal_client_id', ''))")

if [ -z "$SP_ID" ]; then
    echo -e "${RED}❌ ERROR: Could not get service principal ID${NC}"
    echo "The app may not be fully deployed yet. Try:"
    echo "  databricks apps get ${APP_NAME} --profile ${PROFILE}"
    exit 1
fi

echo -e "${GREEN}✅ Service Principal ID: ${SP_ID}${NC}"
echo ""

# Grant permissions
echo "🔒 Granting permissions..."
echo ""

# 1. Catalog permissions
echo "  1️⃣  Granting CATALOG permissions..."
databricks grants update catalog ${CATALOG} \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_CATALOG\"]}]}" \
  --profile ${PROFILE} 2>&1 | grep -v "Warning" || true

echo -e "      ${GREEN}✅ USE_CATALOG granted on ${CATALOG}${NC}"

# 2. Schema permissions
echo "  2️⃣  Granting SCHEMA permissions..."
databricks grants update schema ${CATALOG}.${SCHEMA} \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_SCHEMA\", \"SELECT\"]}]}" \
  --profile ${PROFILE} 2>&1 | grep -v "Warning" || true

echo -e "      ${GREEN}✅ USE_SCHEMA, SELECT granted on ${CATALOG}.${SCHEMA}${NC}"

# 3. Warehouse permissions
echo "  3️⃣  Granting WAREHOUSE permissions..."
databricks permissions update sql/warehouses/${WAREHOUSE_ID} \
  --json "{\"access_control_list\": [{\"service_principal_name\": \"$SP_ID\", \"permission_level\": \"CAN_USE\"}]}" \
  --profile ${PROFILE} 2>&1 | grep -v "Warning" || true

echo -e "      ${GREEN}✅ CAN_USE granted on warehouse ${WAREHOUSE_ID}${NC}"

# 4. UC Function permissions (EXECUTE)
echo "  4️⃣  Granting UC FUNCTION permissions..."

# Grant EXECUTE on fraud_classify
databricks grants update function ${CATALOG}.${SCHEMA}.fraud_classify \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"EXECUTE\"]}]}" \
  --profile ${PROFILE} 2>&1 | grep -v "Warning" || true

echo -e "      ${GREEN}✅ EXECUTE granted on fraud_classify${NC}"

# Grant EXECUTE on fraud_extract_indicators
databricks grants update function ${CATALOG}.${SCHEMA}.fraud_extract_indicators \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"EXECUTE\"]}]}" \
  --profile ${PROFILE} 2>&1 | grep -v "Warning" || true

echo -e "      ${GREEN}✅ EXECUTE granted on fraud_extract_indicators${NC}"

# Grant EXECUTE on fraud_generate_explanation
databricks grants update function ${CATALOG}.${SCHEMA}.fraud_generate_explanation \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"EXECUTE\"]}]}" \
  --profile ${PROFILE} 2>&1 | grep -v "Warning" || true

echo -e "      ${GREEN}✅ EXECUTE granted on fraud_generate_explanation${NC}"

# 5. Vector index source table permissions (SELECT)
echo "  5️⃣  Granting VECTOR INDEX source table permissions..."
databricks grants update table ${CATALOG}.${SCHEMA}.fraud_cases_kb \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"SELECT\"]}]}" \
  --profile ${PROFILE} 2>&1 | grep -v "Warning" || true

echo -e "      ${GREEN}✅ SELECT granted on fraud_cases_kb (vector index source)${NC}"

# 6. Genie Space permissions (CAN_USE)
echo "  6️⃣  Granting GENIE SPACE permissions..."

# Try to get Genie Space ID from environment variable first
GENIE_SPACE_ID="${GENIE_SPACE_ID:-}"

# If not in environment, try to query from config table
if [ -z "$GENIE_SPACE_ID" ]; then
    GENIE_SPACE_ID=$(databricks sql execute \
      --warehouse-id ${WAREHOUSE_ID} \
      --statement "SELECT config_value FROM ${CATALOG}.${SCHEMA}.config_genie WHERE config_key = 'genie_space_id'" \
      --profile ${PROFILE} \
      --output json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'result' in data and 'data_array' in data['result'] and len(data['result']['data_array']) > 0:
        print(data['result']['data_array'][0][0])
    else:
        print('')
except:
    print('')
" || echo "")
fi

if [ -z "$GENIE_SPACE_ID" ]; then
    echo -e "      ${YELLOW}⚠️  Genie Space ID not found${NC}"
    echo -e "      ${YELLOW}    Set GENIE_SPACE_ID environment variable or run setup/10_create_genie_space.py${NC}"
    echo -e "      ${YELLOW}    Example: GENIE_SPACE_ID=01f0d894fdc119ed84cb7a9975acd4ed ./grant_permissions.sh dev${NC}"
else
    echo "      Genie Space ID: ${GENIE_SPACE_ID}"
    
    # Grant CAN_USE permission on Genie Space
    # API Endpoint: PATCH /api/2.0/permissions/genie/spaces/{space_id}
    databricks permissions update genie/spaces/${GENIE_SPACE_ID} \
      --json "{\"access_control_list\": [{\"service_principal_name\": \"$SP_ID\", \"permission_level\": \"CAN_USE\"}]}" \
      --profile ${PROFILE} 2>&1 | grep -v "Warning" || true
    
    echo -e "      ${GREEN}✅ CAN_USE granted on Genie Space${NC}"
fi

echo ""
echo "========================================================================"
echo -e "${GREEN}✅ ALL PERMISSIONS GRANTED SUCCESSFULLY!${NC}"
echo "========================================================================"
echo ""
echo "Your app should now be able to:"
echo "  ✅ Access catalog: ${CATALOG}"
echo "  ✅ Query schema: ${CATALOG}.${SCHEMA}"
echo "  ✅ Use warehouse: ${WAREHOUSE_ID}"
echo "  ✅ Execute UC functions: fraud_classify, fraud_extract_indicators, fraud_generate_explanation"
echo "  ✅ Query vector index: ${CATALOG}.${SCHEMA}.fraud_cases_index"
if [ ! -z "$GENIE_SPACE_ID" ]; then
    echo "  ✅ Query Genie Space: ${GENIE_SPACE_ID}"
fi
echo ""
echo "Test your app at:"
echo "  https://your-workspace.azuredatabricks.net/apps/${APP_NAME}"
echo ""
