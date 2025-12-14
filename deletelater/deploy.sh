#!/bin/bash
# Fraud Detection Claims - End-to-End Deployment Script
# Usage: ./deploy.sh <environment>
# Example: ./deploy.sh dev

set -e  # Exit on any error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ENVIRONMENT=${1:-dev}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Fraud Detection Claims Deployment${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}ERROR: config.yaml not found!${NC}"
    echo "Please copy config.yaml.template to config.yaml and fill in your values."
    exit 1
fi

# Check if Python and PyYAML are available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found!${NC}"
    exit 1
fi

# Parse config.yaml using Python
parse_config() {
    python3 - <<EOF
import yaml
import sys

try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    print(f"ERROR: Failed to parse config.yaml: {e}", file=sys.stderr)
    sys.exit(1)

if '$ENVIRONMENT' not in config['environments']:
    print(f"ERROR: Environment '$ENVIRONMENT' not found in config.yaml", file=sys.stderr)
    print(f"Available: {', '.join(config['environments'].keys())}", file=sys.stderr)
    sys.exit(1)

env = config['environments']['$ENVIRONMENT']
common = config['common']

# Export as environment variables
print(f"export WORKSPACE_HOST='{env['workspace_host']}'")
print(f"export PROFILE='{env['profile']}'")
print(f"export CATALOG='{env['catalog']}'")
print(f"export SCHEMA='{env['schema']}'")
print(f"export WAREHOUSE_ID='{env['warehouse_id']}'")
print(f"export VECTOR_ENDPOINT='{env['vector_endpoint']}'")
print(f"export LLM_ENDPOINT='{env['llm_endpoint']}'")
print(f"export APP_NAME='{env['app_name']}'")
print(f"export SPARK_VERSION='{common['spark_version']}'")
print(f"export NUM_CLAIMS='{common['num_claims']}'")
print(f"export FRAUD_RATE='{common['fraud_rate']}'")
print(f"export GENIE_DISPLAY_NAME='{common['genie_space_display_name']}'")
print(f"export GENIE_DESCRIPTION='{common['genie_space_description']}'")
EOF
}

# Load configuration
echo -e "${YELLOW}Loading configuration...${NC}"
eval $(parse_config)

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to load configuration${NC}"
    exit 1
fi

echo "  Workspace: $WORKSPACE_HOST"
echo "  Profile: $PROFILE"
echo "  Catalog: $CATALOG"
echo "  App: $APP_NAME"
echo ""

# Step 1: Generate databricks.yml
echo -e "${YELLOW}Step 1: Generating databricks.yml...${NC}"
cat > databricks.yml <<EOF_DAB
bundle:
  name: fraud_detection_claims_${ENVIRONMENT}

workspace:
  host: ${WORKSPACE_HOST}
  profile: ${PROFILE}

variables:
  environment:
    default: ${ENVIRONMENT}

resources:
  jobs:
    setup_fraud_detection:
      name: fraud_detection_setup_${ENVIRONMENT}
      job_clusters:
        - job_cluster_key: main_cluster
          new_cluster:
            spark_version: "${SPARK_VERSION}"
            node_type_id: "${node_type:-Standard_DS3_v2}"
            num_workers: 2
      
      tasks:
        - task_key: create_catalog
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/01_create_catalog_schema.py
        
        - task_key: generate_data
          depends_on:
            - task_key: create_catalog
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/02_generate_sample_data.py
        
        - task_key: create_uc_classify
          depends_on:
            - task_key: create_catalog
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/03_uc_fraud_classify.py
        
        - task_key: create_uc_extract
          depends_on:
            - task_key: create_catalog
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/04_uc_fraud_extract.py
        
        - task_key: create_uc_explain
          depends_on:
            - task_key: create_catalog
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/05_uc_fraud_explain.py
        
        - task_key: create_knowledge_base
          depends_on:
            - task_key: create_catalog
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/06_create_knowledge_base.py
        
        - task_key: create_vector_index
          depends_on:
            - task_key: create_knowledge_base
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/07_create_vector_index.py
        
        - task_key: create_genie_space
          depends_on:
            - task_key: generate_data
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: ./setup/08_create_genie_space.py
  
  apps:
    fraud_detection_app:
      name: ${APP_NAME}
      description: "AI-Powered Fraud Detection for Insurance Claims - ${ENVIRONMENT}"
      source_code_path: ./app
EOF_DAB

echo -e "${GREEN}✅ databricks.yml generated${NC}"

# Step 2: Generate app/app.yaml
echo -e "${YELLOW}Step 2: Generating app/app.yaml...${NC}"
mkdir -p app
cat > app/app.yaml <<EOF_APP
# Auto-generated by deploy.sh from config.yaml
# DO NOT EDIT THIS FILE DIRECTLY - edit config.yaml instead!

command: ['streamlit', 'run', 'app.py']

env:
  - name: 'DATABRICKS_HOST'
    value: '${WORKSPACE_HOST#https://}'
  - name: 'ENVIRONMENT'
    value: '${ENVIRONMENT}'
EOF_APP

echo -e "${GREEN}✅ app/app.yaml generated${NC}"

# Step 3: Validate bundle
echo -e "${YELLOW}Step 3: Validating bundle...${NC}"
if ! databricks bundle validate --profile ${PROFILE}; then
    echo -e "${RED}❌ Bundle validation failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Bundle validated${NC}"

# Step 4: Deploy bundle
echo -e "${YELLOW}Step 4: Deploying bundle...${NC}"
if ! databricks bundle deploy --profile ${PROFILE}; then
    echo -e "${RED}❌ Bundle deployment failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Bundle deployed${NC}"

# Step 5: Run setup job
echo -e "${YELLOW}Step 5: Running setup job (this takes ~15-20 minutes)...${NC}"
RUN_OUTPUT=$(databricks bundle run setup_fraud_detection --profile ${PROFILE} 2>&1)
RUN_ID=$(echo "$RUN_OUTPUT" | grep -oE 'run_id: [0-9]+' | head -1 | cut -d' ' -f2)

if [ -z "$RUN_ID" ]; then
    echo -e "${YELLOW}⚠️  Could not get run ID from output${NC}"
    echo "You can check job status in the Databricks UI"
else
    echo "  Job Run ID: $RUN_ID"
    echo "  View progress: ${WORKSPACE_HOST}/#job/${RUN_ID}"
fi

# Step 6: Deploy Streamlit app
echo -e "${YELLOW}Step 6: Deploying Streamlit app...${NC}"
if ! databricks apps deploy ${APP_NAME} --source-code-path app --profile ${PROFILE}; then
    echo -e "${RED}❌ App deployment failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ App deployed${NC}"

# Step 7: Grant permissions
echo -e "${YELLOW}Step 7: Configuring permissions...${NC}"
sleep 5  # Wait for app to initialize

SP_ID=$(databricks apps get ${APP_NAME} --profile ${PROFILE} 2>/dev/null | grep -oE 'service_principal_client_id: [a-f0-9-]+' | cut -d' ' -f2)

if [ -z "$SP_ID" ]; then
    echo -e "${YELLOW}⚠️  Could not get service principal ID automatically${NC}"
    echo "Run permissions manually after app starts:"
    echo "  ./grant_permissions.sh ${ENVIRONMENT}"
else
    echo "  Service Principal: $SP_ID"
    
    # Grant catalog permissions
    echo "  Granting catalog permissions..."
    databricks grants update catalog ${CATALOG} \
      --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_CATALOG\"]}]}" \
      --profile ${PROFILE} 2>/dev/null || echo "    (may already have permissions)"
    
    # Grant schema permissions
    echo "  Granting schema permissions..."
    databricks grants update schema ${CATALOG}.${SCHEMA} \
      --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_SCHEMA\", \"SELECT\"]}]}" \
      --profile ${PROFILE} 2>/dev/null || echo "    (may already have permissions)"
    
    # Grant warehouse permissions
    echo "  Granting warehouse permissions..."
    databricks permissions update sql/warehouses ${WAREHOUSE_ID} \
      --json "{\"access_control_list\": [{\"service_principal_name\": \"$SP_ID\", \"permission_level\": \"CAN_USE\"}]}" \
      --profile ${PROFILE} 2>/dev/null || echo "    (may already have permissions)"
    
    echo -e "${GREEN}✅ Permissions granted${NC}"
fi

# Step 8: Get app URL
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
APP_URL=$(databricks apps get ${APP_NAME} --profile ${PROFILE} 2>/dev/null | grep -oE 'url: https://[^[:space:]]+' | cut -d' ' -f2)
echo "  Environment: $ENVIRONMENT"
echo "  Catalog: $CATALOG"
echo "  App Name: $APP_NAME"
if [ -n "$APP_URL" ]; then
    echo "  App URL: $APP_URL"
else
    echo "  App URL: ${WORKSPACE_HOST}/apps/${APP_NAME}"
fi
echo ""
echo "Next steps:"
echo "  1. Open app URL above"
echo "  2. View logs: databricks apps logs ${APP_NAME} --profile ${PROFILE}"
echo "  3. Check status: databricks apps get ${APP_NAME} --profile ${PROFILE}"
echo -e "${GREEN}========================================${NC}"

