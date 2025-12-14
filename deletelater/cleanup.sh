#!/bin/bash

##############################################################################
# CLEANUP SCRIPT - Remove All Fraud Detection Resources
#
# Usage:
#   ./cleanup.sh dev     # Clean dev environment
#   ./cleanup.sh staging # Clean staging environment
#   ./cleanup.sh prod    # Clean prod environment
#
# This will DELETE:
#   - Vector Search Index
#   - Genie Space
#   - Schema (all tables, volumes, functions)
#   - Optionally: Entire Catalog
##############################################################################

set -e

# Check if environment provided
if [ -z "$1" ]; then
    echo "❌ Error: Please specify environment (dev, staging, or prod)"
    echo "Usage: ./cleanup.sh <environment>"
    exit 1
fi

ENV=$1

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           FRAUD DETECTION CLEANUP SCRIPT                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Environment: $ENV"
echo ""

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found"
    exit 1
fi

# Install pyyaml if needed
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "📦 Installing pyyaml..."
    pip install pyyaml --break-system-packages 2>/dev/null || pip install pyyaml
fi

# Parse config.yaml to get variables
echo "📖 Reading config.yaml..."
CATALOG=$(python3 -c "import yaml; cfg=yaml.safe_load(open('config.yaml'))['environments']['$ENV']; print(cfg['catalog'])")
SCHEMA=$(python3 -c "import yaml; cfg=yaml.safe_load(open('config.yaml'))['environments']['$ENV']; print(cfg['schema'])")
PROFILE=$(python3 -c "import yaml; cfg=yaml.safe_load(open('config.yaml'))['environments']['$ENV']; print(cfg['profile'])")
GENIE_SPACE=$(python3 -c "import yaml; cfg=yaml.safe_load(open('config.yaml'))['common']; print(cfg['genie_space_display_name'])")

echo ""
echo "⚠️  WARNING: This will DELETE:"
echo "   • Vector Index: ${CATALOG}.${SCHEMA}.fraud_cases_index"
echo "   • Genie Space: ${GENIE_SPACE}"
echo "   • Schema: ${CATALOG}.${SCHEMA} (CASCADE)"
echo "     - All tables (claims, fraud_cases_kb)"
echo "     - All volumes"
echo "     - All UC functions"
echo ""
echo "   Catalog '${CATALOG}' will be PRESERVED (only schema deleted)"
echo ""

# Confirmation prompt
read -p "Are you SURE you want to delete these resources? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🗑️  Starting cleanup..."
echo ""

# Upload cleanup notebook to workspace
echo "📤 Uploading cleanup notebook..."
CLEANUP_PATH="/Workspace/Users/$(databricks auth describe --profile $PROFILE 2>/dev/null | grep Username | awk '{print $2}')/fraud_detection_cleanup"

databricks workspace import \
    --profile $PROFILE \
    --file setup/00_CLEANUP.py \
    --path "${CLEANUP_PATH}" \
    --language PYTHON \
    --format SOURCE \
    --overwrite 2>/dev/null || echo "   Note: Using existing cleanup notebook"

echo ""
echo "🚀 Running cleanup notebook..."
echo "   Notebook: ${CLEANUP_PATH}"
echo ""

# Create a temporary job to run cleanup
JOB_NAME="fraud-detection-cleanup-${ENV}-$(date +%s)"

databricks jobs create --json @- --profile $PROFILE <<EOF
{
  "name": "${JOB_NAME}",
  "tasks": [
    {
      "task_key": "cleanup",
      "notebook_task": {
        "notebook_path": "${CLEANUP_PATH}",
        "source": "WORKSPACE"
      },
      "job_cluster_key": "cleanup_cluster",
      "libraries": []
    }
  ],
  "job_clusters": [
    {
      "job_cluster_key": "cleanup_cluster",
      "new_cluster": {
        "spark_version": "16.4.x-scala2.12",
        "node_type_id": "Standard_D4ds_v5",
        "num_workers": 0,
        "spark_conf": {
          "spark.databricks.cluster.profile": "singleNode",
          "spark.master": "local[*]"
        },
        "custom_tags": {
          "ResourceClass": "SingleNode"
        }
      }
    }
  ],
  "max_concurrent_runs": 1
}
EOF

# Get job ID
JOB_ID=$(databricks jobs list --profile $PROFILE --output json | jq -r ".jobs[] | select(.settings.name==\"${JOB_NAME}\") | .job_id")

echo "   Job created: ${JOB_ID}"

# Run the job
RUN_ID=$(databricks jobs run-now --profile $PROFILE --job-id $JOB_ID --output json | jq -r '.run_id')
echo "   Run started: ${RUN_ID}"

# Wait for completion
echo ""
echo "⏳ Waiting for cleanup to complete..."
while true; do
    STATUS=$(databricks runs get --profile $PROFILE --run-id $RUN_ID --output json | jq -r '.state.life_cycle_state')
    if [ "$STATUS" = "TERMINATED" ]; then
        RESULT=$(databricks runs get --profile $PROFILE --run-id $RUN_ID --output json | jq -r '.state.result_state')
        if [ "$RESULT" = "SUCCESS" ]; then
            echo "✅ Cleanup completed successfully!"
            break
        else
            echo "❌ Cleanup failed!"
            echo "   View logs: https://$(databricks auth describe --profile $PROFILE | grep Host | awk '{print $2}')/#job/${JOB_ID}/run/${RUN_ID}"
            exit 1
        fi
    fi
    echo "   Status: $STATUS"
    sleep 5
done

# Delete the cleanup job
echo ""
echo "🧹 Cleaning up temporary job..."
databricks jobs delete --profile $PROFILE --job-id $JOB_ID 2>/dev/null || echo "   Job already deleted"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   ✅ CLEANUP COMPLETE!                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 What was deleted:"
echo "   ✅ Vector Search Index"
echo "   ✅ Genie Space"
echo "   ✅ Schema ${CATALOG}.${SCHEMA} (all tables, volumes, functions)"
echo ""
echo "📋 What was preserved:"
echo "   ✅ Catalog ${CATALOG}"
echo ""
echo "🎯 Ready for fresh deployment!"
echo "   Run: ./deploy.sh ${ENV}"
echo ""

