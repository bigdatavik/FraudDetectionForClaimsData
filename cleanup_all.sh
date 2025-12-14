#!/bin/bash

# cleanup_all.sh - Destroy all Databricks resources for fraud detection project
# Usage: ./cleanup_all.sh <environment> [--skip-confirmation]
# Example: ./cleanup_all.sh dev

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Environment parameter required${NC}"
    echo "Usage: ./cleanup_all.sh <environment> [--skip-confirmation]"
    echo "Example: ./cleanup_all.sh dev"
    exit 1
fi

ENVIRONMENT=$1
SKIP_CONFIRM=$2

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}Error: config.yaml not found${NC}"
    exit 1
fi

# Load config from config.yaml using Python
echo "📝 Loading configuration from config.yaml..."
CONFIG_OUTPUT=$(python3 -c "
import yaml
import sys
try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    env = config['environments']['$ENVIRONMENT']
    print(f\"PROFILE='{env['profile']}'\")
    print(f\"CATALOG='{env['catalog']}'\")
    print(f\"APP_NAME='{env['app_name']}'\")
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}${CONFIG_OUTPUT}${NC}"
    exit 1
fi

eval "$CONFIG_OUTPUT"

if [ -z "$APP_NAME" ]; then
    echo -e "${RED}Error: Failed to load configuration from config.yaml${NC}"
    exit 1
fi

# Get current user email from Databricks CLI
USER_EMAIL=$(databricks current-user me --profile ${PROFILE} --output json 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin)['userName'])" 2>&1)

if [ $? -ne 0 ] || [ -z "$USER_EMAIL" ]; then
    echo -e "${RED}Error: Could not determine current Databricks user${NC}"
    echo "Please ensure Databricks CLI is configured properly"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Configuration loaded${NC}"
echo "   Profile: $PROFILE"
echo "   Catalog: $CATALOG"
echo "   App Name: $APP_NAME"
echo "   User: $USER_EMAIL"
echo ""

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}   CLEANUP ALL RESOURCES - ${ENVIRONMENT}${NC}"
echo -e "${YELLOW}============================================${NC}"
echo ""
echo "This will DELETE:"
echo "  • App: ${APP_NAME}"
echo "  • Catalog: ${CATALOG}"
echo "  • All tables, vector indexes, Genie Space"
echo "  • Local bundle state (.databricks/)"
echo "  • Remote workspace files: /Workspace/Users/${USER_EMAIL}/.bundle/fraud_detection_claims"
echo ""

# Confirmation prompt
if [ "$SKIP_CONFIRM" != "--skip-confirmation" ]; then
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Cleanup cancelled${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${GREEN}Starting cleanup...${NC}"
echo ""

# Step 1: Delete the app
echo -e "${YELLOW}[1/5] Deleting Databricks app...${NC}"
if databricks apps delete ${APP_NAME} --profile ${PROFILE} 2>/dev/null; then
    echo -e "${GREEN}✓ App deleted: ${APP_NAME}${NC}"
else
    echo -e "${YELLOW}⚠ App not found or already deleted: ${APP_NAME}${NC}"
fi
echo ""

# Step 2: Delete Genie Space (must be done before catalog deletion)
echo -e "${YELLOW}[2/6] Deleting Genie Space...${NC}"

# Get Genie Space display name from config
GENIE_DISPLAY_NAME=$(python3 -c "
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
print(config['common']['genie_space_display_name'])
" 2>&1)

echo "  Looking for Genie Space: ${GENIE_DISPLAY_NAME}"

# Find and delete Genie Space using Databricks API
GENIE_SPACE_ID=$(databricks api get /api/2.0/genie/spaces --profile ${PROFILE} --output json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    spaces = data.get('spaces', [])
    for space in spaces:
        if space.get('title') == '${GENIE_DISPLAY_NAME}' or space.get('name') == '${GENIE_DISPLAY_NAME}':
            print(space.get('space_id', ''))
            break
except:
    pass
" 2>&1)

if [ -n "$GENIE_SPACE_ID" ]; then
    echo "  Found Genie Space ID: ${GENIE_SPACE_ID}"
    echo "  Deleting Genie Space..."
    
    DELETE_GENIE=$(databricks api delete "/api/2.0/genie/spaces/${GENIE_SPACE_ID}" --profile ${PROFILE} 2>&1)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Genie Space deleted: ${GENIE_DISPLAY_NAME}${NC}"
    else
        echo -e "${YELLOW}⚠ Error deleting Genie Space: ${DELETE_GENIE}${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Genie Space not found (may already be deleted)${NC}"
fi
echo ""

# Step 3: Delete catalog and all resources
echo -e "${YELLOW}[3/6] Deleting catalog and all resources...${NC}"
echo "  This will delete:"
echo "    - Catalog: ${CATALOG}"
echo "    - All schemas, tables, functions, volumes"
echo "    - Vector Search index (if exists)"
echo "    - Genie Space (will be deleted separately)"
echo ""

echo "  Deleting catalog (this may take 1-2 minutes)..."

# Delete catalog using Databricks CLI - CASCADE will delete everything inside
DELETE_OUTPUT=$(databricks catalogs delete "${CATALOG}" --force --profile ${PROFILE} 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Catalog deleted: ${CATALOG}${NC}"
    echo "  All tables, schemas, functions, and volumes were deleted"
else
    if echo "$DELETE_OUTPUT" | grep -q "not found\|does not exist"; then
        echo -e "${YELLOW}⚠ Catalog not found (already deleted): ${CATALOG}${NC}"
    else
        echo -e "${YELLOW}⚠ Catalog deletion had errors${NC}"
        echo "  ${DELETE_OUTPUT}"
    fi
fi
echo ""

# Step 3: Clean local bundle state
echo -e "${YELLOW}[4/6] Cleaning local bundle state...${NC}"
if [ -d ".databricks" ]; then
    rm -rf .databricks
    echo -e "${GREEN}✓ Local .databricks/ deleted${NC}"
else
    echo -e "${YELLOW}⚠ No local .databricks/ folder found${NC}"
fi
echo ""

# Step 4: Clean remote bundle state
echo -e "${YELLOW}[5/6] Cleaning remote workspace files...${NC}"
BUNDLE_PATH="/Workspace/Users/${USER_EMAIL}/.bundle/fraud_detection_claims"
echo "  Deleting: ${BUNDLE_PATH}"
if databricks workspace delete "${BUNDLE_PATH}" --recursive --profile ${PROFILE} 2>&1; then
    echo -e "${GREEN}✓ Remote bundle files deleted: ${BUNDLE_PATH}${NC}"
else
    echo -e "${YELLOW}⚠ Remote bundle files not found or already deleted${NC}"
fi
echo ""

# Step 5: List and optionally delete setup job
echo -e "${YELLOW}[6/6] Checking for setup job...${NC}"

# Use Databricks CLI to list and find jobs
JOB_IDS=$(databricks jobs list --profile ${PROFILE} --output json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    jobs = data.get('jobs', [])
    for job in jobs:
        settings = job.get('settings', {})
        job_name = settings.get('name', '')
        if job_name == 'fraud_detection_setup_${ENVIRONMENT}':
            print(job.get('job_id', ''))
except:
    pass
" 2>&1)

if [ -n "$JOB_IDS" ]; then
    echo "  Found setup job(s): $JOB_IDS"
    
    if [ "$SKIP_CONFIRM" != "--skip-confirmation" ]; then
        read -p "  Delete setup job? (yes/no): " delete_job
    else
        delete_job="yes"
    fi
    
    if [ "$delete_job" == "yes" ]; then
        for job_id in $JOB_IDS; do
            echo "  Deleting job: $job_id"
            if databricks jobs delete --job-id "$job_id" --profile ${PROFILE} 2>&1; then
                echo -e "${GREEN}✓ Job $job_id deleted${NC}"
            else
                echo -e "${YELLOW}⚠ Could not delete job $job_id${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠ Setup job not deleted (you can delete it manually later)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No setup job found for environment: ${ENVIRONMENT}${NC}"
fi
echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   CLEANUP COMPLETE!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify cleanup in Databricks workspace"
echo "  2. Run fresh deployment: ./deploy_with_config.sh ${ENVIRONMENT}"
echo ""

