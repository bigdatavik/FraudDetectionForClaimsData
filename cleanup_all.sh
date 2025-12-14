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
PROFILE="DEFAULT_azure"

# Load config
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}Error: config.yaml not found${NC}"
    exit 1
fi

# Parse config values
CATALOG=$(grep "catalog_name:" config.yaml | awk '{print $2}' | tr -d '"')
USER_EMAIL=$(grep "user_email:" config.yaml | awk '{print $2}' | tr -d '"')
APP_NAME=$(grep "app_name:" config.yaml | awk '{print $2}' | tr -d '"')

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}   CLEANUP ALL RESOURCES - ${ENVIRONMENT}${NC}"
echo -e "${YELLOW}============================================${NC}"
echo ""
echo "This will DELETE:"
echo "  • App: ${APP_NAME}-${ENVIRONMENT}"
echo "  • Catalog: ${CATALOG}"
echo "  • All tables, vector indexes, Genie Space"
echo "  • Local bundle state (.databricks/)"
echo "  • Remote workspace files"
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
if databricks apps delete ${APP_NAME}-${ENVIRONMENT} --profile ${PROFILE} 2>/dev/null; then
    echo -e "${GREEN}✓ App deleted${NC}"
else
    echo -e "${YELLOW}⚠ App not found or already deleted${NC}"
fi
echo ""

# Step 2: Run cleanup notebook
echo -e "${YELLOW}[2/5] Running cleanup notebook to delete catalog and resources...${NC}"

# Import cleanup notebook
TEMP_CLEANUP_PATH="/Workspace/Users/${USER_EMAIL}/.temp_cleanup_$(date +%s)"
if databricks workspace import ./setup/00_CLEANUP.py "${TEMP_CLEANUP_PATH}" \
    --language PYTHON \
    --overwrite \
    --profile ${PROFILE} 2>&1; then
    
    echo -e "${GREEN}✓ Cleanup notebook imported${NC}"
    
    # Run cleanup notebook
    echo "  Running cleanup (this may take a minute)..."
    if databricks workspace run "${TEMP_CLEANUP_PATH}" --profile ${PROFILE} 2>&1; then
        echo -e "${GREEN}✓ Cleanup notebook completed${NC}"
    else
        echo -e "${YELLOW}⚠ Cleanup notebook failed or resources already deleted${NC}"
    fi
    
    # Delete temp cleanup notebook
    databricks workspace delete "${TEMP_CLEANUP_PATH}" --profile ${PROFILE} 2>/dev/null || true
else
    echo -e "${YELLOW}⚠ Could not import cleanup notebook${NC}"
fi
echo ""

# Step 3: Clean local bundle state
echo -e "${YELLOW}[3/5] Cleaning local bundle state...${NC}"
if [ -d ".databricks" ]; then
    rm -rf .databricks
    echo -e "${GREEN}✓ Local .databricks/ deleted${NC}"
else
    echo -e "${YELLOW}⚠ No local .databricks/ folder found${NC}"
fi
echo ""

# Step 4: Clean remote bundle state
echo -e "${YELLOW}[4/5] Cleaning remote workspace files...${NC}"
BUNDLE_PATH="/Users/${USER_EMAIL}/.bundle/fraud_detection_claims"
if databricks workspace delete "${BUNDLE_PATH}" --recursive --profile ${PROFILE} 2>/dev/null; then
    echo -e "${GREEN}✓ Remote bundle files deleted${NC}"
else
    echo -e "${YELLOW}⚠ Remote bundle files not found or already deleted${NC}"
fi
echo ""

# Step 5: List and optionally delete setup job
echo -e "${YELLOW}[5/5] Checking for setup job...${NC}"
JOB_LIST=$(databricks jobs list --profile ${PROFILE} --output json 2>/dev/null | jq -r '.jobs[] | select(.settings.name == "fraud_detection_claims_setup_fraud_detection") | .job_id' || echo "")

if [ -n "$JOB_LIST" ]; then
    echo "  Found setup job(s): $JOB_LIST"
    read -p "  Delete setup job? (yes/no): " delete_job
    if [ "$delete_job" == "yes" ]; then
        for job_id in $JOB_LIST; do
            if databricks jobs delete --job-id "$job_id" --profile ${PROFILE} 2>/dev/null; then
                echo -e "${GREEN}✓ Job $job_id deleted${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠ Setup job not deleted (you can delete it manually later)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No setup job found${NC}"
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

