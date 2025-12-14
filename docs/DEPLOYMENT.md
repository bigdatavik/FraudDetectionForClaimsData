# Deployment Guide

Complete guide for deploying the Fraud Detection Agent across environments.

## Prerequisites

### Required

- ✅ Databricks workspace (Azure, AWS, or GCP)
- ✅ Unity Catalog enabled
- ✅ SQL Warehouse (any size)
- ✅ Databricks CLI installed
- ✅ Python 3.10+

### Recommended

- ✅ Vector Search endpoint created
- ✅ Service Principal for app authentication
- ✅ Git repository for version control

## Step-by-Step Deployment

### 1. Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd FraudDetectionForClaimsData

# Verify you have Databricks CLI
databricks --version
# Should show: Databricks CLI 0.270.0+

# Configure Databricks authentication
databricks configure --profile DEFAULT_azure
# Or use existing profile
```

### 2. Configure Environment

Edit `config.yaml` with your Databricks details:

```bash
vim config.yaml
```

**Required Configuration**:

```yaml
environments:
  dev:
    workspace_host: "https://your-workspace.azuredatabricks.net"
    profile: "DEFAULT_azure"
    warehouse_id: "your-warehouse-id"  # From SQL → Warehouses
    vector_endpoint: "your-endpoint"    # From Compute → Vector Search
    catalog: "fraud_detection_dev"
    llm_endpoint: "databricks-claude-sonnet-4-5"
```

**How to Find Values**:

1. **workspace_host**: Copy from browser URL
2. **warehouse_id**: 
   - Go to SQL → Warehouses
   - Click your warehouse
   - Copy ID from URL or details
3. **vector_endpoint**:
   - Go to Compute → Vector Search
   - Create endpoint if needed
   - Use the endpoint name

### 3. Deploy (One Command)

```bash
# Deploy everything to dev environment
./deploy_with_config.sh dev
```

**What it does automatically**:
1. ✅ Generates `app.yaml` from `config.yaml`
2. ✅ Deploys bundle (creates app and job definitions)
3. ✅ Runs setup job (creates catalog, tables, functions, data, Genie Space)
4. ✅ Grants service principal permissions
5. ✅ Deploys app source code from bundle location

**Expected time**: 6-8 minutes

**Manual alternative** (if you prefer step-by-step):
```bash
# Step 1: Generate app.yaml
python generate_app_yaml.py dev

# Step 2: Deploy infrastructure
databricks bundle deploy --target dev --profile DEFAULT_azure

# Step 3: Run setup job
databricks bundle run setup_fraud_detection --target dev --profile DEFAULT_azure

# Step 4: Grant permissions
./grant_permissions.sh dev

# Step 5: Deploy app source code
./deploy_app_source.sh dev
```

**Important:** Per [Microsoft documentation](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial#deploy-the-app-to-the-workspace), `databricks bundle deploy` creates the app infrastructure but does NOT automatically deploy the source code to compute. Step 5 explicitly deploys the app source code using `databricks apps deploy`.

### 4. Configure Genie Space (Manual Step)

After setup completes, you must manually add instructions to the Genie Space:

1. Go to job output for task `create_genie_space`
2. Copy the "Instructions for Genie Space" text
3. Open: **Data Intelligence > Genie > Fraud Detection Analytics**
4. Click **Settings** (gear icon)
5. Paste instructions into the **Instructions** field
6. Click **Save**

**Why manual?** The Genie API doesn't support setting instructions via API yet.

### 5. Verify Deployment

```bash
# Check catalog created
databricks catalogs list --profile DEFAULT_azure | grep fraud_detection_dev

# Check app deployed and source code present
databricks apps get frauddetection-dev --profile DEFAULT_azure

# Check app is running
databricks apps get frauddetection-dev --profile DEFAULT_azure | grep state
```

**Manual Verification**:

1. Open Databricks workspace
2. Navigate to Catalog → `fraud_detection_dev` → `claims_analysis`
3. Verify tables exist:
   - ✅ claims_data
   - ✅ fraud_cases_kb
   - ✅ fraud_claims_complete
   - ✅ config_genie
4. Check functions:
   - ✅ fraud_classify
   - ✅ fraud_extract_indicators
   - ✅ fraud_generate_explanation
5. Check Compute → Apps → `frauddetection-dev`:
   - ✅ Status: "Running" (green dot)
   - ✅ Deployment shows source code path
   - ✅ URL is active

### 6. Access Application

The app URL is shown at the end of deployment:
```
https://frauddetection-dev-<workspace-id>.azuredatabricksapps.com
```

Or find it with:
```bash
databricks apps get frauddetection-dev --profile DEFAULT_azure | grep url
```

Open in browser and verify:
- ✅ Home page loads
- ✅ Environment shows "dev"
- ✅ System status shows resources connected
- ✅ All 5 pages accessible (Claim Analysis, Batch Processing, Fraud Insights, Case Search, Agent Playground)

## Multi-Environment Deployment

### Dev Environment

```bash
# Deploy to dev
./deploy.sh dev

# Characteristics:
# - Synthetic data
# - Single-node warehouse
# - Smaller vector index
# - Debug logging enabled
```

### Staging Environment

```bash
# Deploy to staging
./deploy_with_config.sh staging
```

**Characteristics**:
- Production-like data
- Multi-cluster warehouse
- Full vector index
- Performance testing

### Production Environment

```bash
# Deploy to prod
./deploy_with_config.sh prod
```

**Characteristics**:
- Real customer data
- High-availability warehouse
- Optimized vector index
- Audit logging enabled
- Service principal auth

## Configuration Per Environment

### config.yaml Structure

```yaml
environments:
  dev:
    # Dev-specific settings
    catalog: "fraud_detection_dev"
    warehouse_id: "dev-warehouse"
    app_name: "fraud-detection-dev"
    
  staging:
    # Staging-specific settings
    catalog: "fraud_detection_staging"
    warehouse_id: "staging-warehouse"
    app_name: "fraud-detection-staging"
    
  prod:
    # Production-specific settings
    catalog: "fraud_detection_prod"
    warehouse_id: "prod-warehouse"
    app_name: "fraud-detection-prod"

common:
  # Shared across all environments
  num_claims: 1000
  fraud_rate: 0.08
  # ...
```

## Advanced Deployment

### Using CI/CD

**GitHub Actions Example**:

```yaml
name: Deploy to Databricks

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Databricks CLI
        run: pip install databricks-cli
      
      - name: Configure Databricks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          echo "$DATABRICKS_HOST" > ~/.databrickscfg
          echo "$DATABRICKS_TOKEN" >> ~/.databrickscfg
      
      - name: Deploy
        run: ./deploy.sh prod
```

### Manual Deployment Steps

If `deploy.sh` fails, you can run steps manually:

```bash
# 1. Generate databricks.yml
python -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
# ... generate databricks.yml
"

# 2. Deploy bundle
databricks bundle validate
databricks bundle deploy

# 3. Run setup job
JOB_ID=$(databricks jobs list | grep setup | awk '{print $1}')
databricks jobs run-now --job-id $JOB_ID

# 4. Deploy app
databricks apps deploy app --app-name fraud-detection-dev

# 5. Grant permissions
./grant_permissions.sh dev
```

## Troubleshooting Deployment

### Common Issues

**1. Permission Denied**

```
Error: User does not have CREATE CATALOG permission
```

**Solution**:
```bash
# Have admin grant permissions:
# In Databricks workspace:
# Admin Settings → Unity Catalog → Grant "CREATE CATALOG"
```

**2. Warehouse Not Found**

```
Error: SQL warehouse <id> not found
```

**Solution**:
```bash
# Verify warehouse ID
databricks sql-warehouses list

# Update config.yaml with correct ID
```

**3. Vector Endpoint Missing**

```
Error: Vector search endpoint not found
```

**Solution**:
```bash
# Create endpoint first
databricks vector-search create-endpoint \
  --endpoint-name one-env-shared-endpoint-2 \
  --endpoint-type STANDARD

# Wait for endpoint to be ready
databricks vector-search get-endpoint \
  --endpoint-name one-env-shared-endpoint-2
```

**4. App Deploy Fails**

```
Error: App already exists
```

**Solution**:
```bash
# Delete existing app
databricks apps delete fraud-detection-dev

# Redeploy
./deploy.sh dev
```

### Debug Mode

```bash
# Enable debug output
DATABRICKS_DEBUG=1 ./deploy.sh dev

# Check logs
databricks apps logs fraud-detection-dev

# Check job logs
databricks jobs runs list --job-id <job-id>
```

## Rollback Strategy

### If Deployment Fails

```bash
# 1. Check what was created
databricks catalogs list | grep fraud
databricks apps list | grep fraud

# 2. Clean up (if needed)
databricks apps delete fraud-detection-dev
databricks jobs delete --job-id <setup-job-id>

# 3. Fix issue in config.yaml

# 4. Redeploy
./deploy.sh dev
```

### If App is Broken

```bash
# Redeploy just the app
databricks apps deploy app \
  --app-name fraud-detection-dev \
  --source-code-path ./app

# Or delete and redeploy
databricks apps delete fraud-detection-dev
./deploy.sh dev --app-only
```

## Post-Deployment

### Verification Checklist

- [ ] Catalog and schema exist
- [ ] Tables have data
- [ ] UC functions callable
- [ ] Vector index synced
- [ ] Genie Space accessible
- [ ] App loads and responds
- [ ] Test claim analysis works
- [ ] Permissions granted

### Performance Tuning

```bash
# Scale warehouse
databricks sql-warehouses update <id> \
  --cluster-size "LARGE"

# Scale vector index
# (Done automatically by Databricks)

# Monitor app logs
databricks apps logs fraud-detection-dev --follow
```

### Security Hardening

```bash
# Use service principal (not personal PAT)
databricks service-principals create \
  --display-name "fraud-detection-app"

# Grant minimum permissions
databricks grants update \
  --service-principal <sp-id> \
  --privilege SELECT \
  --table fraud_detection_prod.claims_analysis.claims_fraud

# Enable audit logs
# (Automatic with Unity Catalog)
```

## Maintenance

### Updates

```bash
# Update code
git pull origin main

# Redeploy
./deploy.sh dev

# Test
# Access app and verify changes
```

### Monitoring

```bash
# Check app health
databricks apps get fraud-detection-dev

# View logs
databricks apps logs fraud-detection-dev --since 1h

# Check costs
# Databricks workspace → Account Console → Usage
```

---

**Need help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)


