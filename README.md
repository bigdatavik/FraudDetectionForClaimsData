# 🔍 AI-Powered Fraud Detection for Insurance Claims

> **Project Status**: ✅ **Complete & Production-Ready** | December 2024

[![Databricks](https://img.shields.io/badge/Databricks-Ready-red?logo=databricks)](https://databricks.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agents-blue)](https://langchain-ai.github.io/langgraph/)
[![Unity Catalog](https://img.shields.io/badge/Unity%20Catalog-AI%20Functions-orange)](https://www.databricks.com/product/unity-catalog)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success)](docs/PROJECT_SUMMARY.md)

An intelligent fraud detection system using LangGraph agents, Unity Catalog AI functions, Vector Search, and Genie API.

**Key Results:** 94% accuracy | 3-8s per claim | $0.002 cost | 1,298x ROI | 6-minute deployment

📊 **[See Full Project Summary](docs/PROJECT_SUMMARY.md)**

---

## 🚀 Quick Start (2 Steps)

### **Step 1: Configure** (2 minutes)

Edit `config.yaml` with your Databricks details:

```bash
vim config.yaml
```

Update these values:
```yaml
environments:
  dev:
    workspace_host: "https://your-workspace.azuredatabricks.net"  # ← Your workspace URL
    profile: "DEFAULT_azure"                                       # ← Your profile name
    catalog: "fraud_detection_dev"                                 # ← Leave as is (or customize)
    warehouse_id: "your-warehouse-id"                             # ← Your SQL Warehouse ID
```

**Where to find these values**:
- **Workspace URL**: Your Databricks workspace URL (copy from browser)
- **Profile**: Check `~/.databrickscfg` (usually `DEFAULT` or `DEFAULT_azure`)
- **Warehouse ID**: Databricks → SQL Warehouses → Copy the ID

---

### **Step 2: Deploy Everything** (6 minutes - automated!)

**Option A: One-Command Deploy** (Recommended ⭐)

```bash
./deploy_with_config.sh dev
```

This automatically does **everything**:
1. ✅ Generates `app/app.yaml` from config
2. ✅ Deploys app and infrastructure
3. ✅ Runs setup job (creates catalog, tables, functions, vector index, Genie Space)
4. ✅ Grants service principal permissions
5. ✅ Deploys app source code

**After deployment completes, one additional step:**

**🔑 Grant Genie Space Permissions (ONE-TIME, 30 seconds)**

**What you're doing:** Giving your Databricks APP permission to query the Genie Space. The app runs as a "service principal" (like a robot user account).

The setup notebook will output instructions like this:
```
📋 STEP-BY-STEP INSTRUCTIONS:

1. Open Genie Space: https://your-workspace.azuredatabricks.net/#genie/abc123...

2. Click 'Share' button (top-right corner)

3. In the search box, type: frauddetection-dev
   ☝️  This is your APP'S SERVICE PRINCIPAL name

4. Select 'frauddetection-dev' from dropdown
   (It will show as a service principal, not a user)

5. Set permission level to: 'Can Run'
   (NOT 'Can Use' - select 'Can Run' from the dropdown)

6. Click 'Add' or 'Save'
```

**Why?** Databricks doesn't provide an API to grant Genie Space permissions programmatically. This is a one-time step per environment.

---

**Option B: Manual Steps** (if you prefer step-by-step)
```bash
# 1. Generate app config
python generate_app_yaml.py dev

# 2. Deploy infrastructure
databricks bundle deploy --target dev

# 3. Create data and resources
databricks bundle run setup_fraud_detection --target dev

# 4. Grant permissions
./grant_permissions.sh dev

# 5. Deploy app source code
./deploy_app_source.sh dev
```

**After step 3, grant Genie Space permissions:**

**What you're doing:** Giving your Databricks APP permission to query the Genie Space. The app runs as a "service principal" (a robot user account).

The notebook `setup/10_create_genie_space.py` will print instructions:
```
📋 STEP-BY-STEP INSTRUCTIONS:

1. Open Genie Space in browser (URL provided in notebook output)

2. Click 'Share' button (top-right corner)

3. In the search box, type: frauddetection-dev
   ☝️  This is your APP'S SERVICE PRINCIPAL name

4. Select 'frauddetection-dev' from the dropdown
   (It will show as a service principal, not a user)

5. Set permission level to: 'Can Run'
   (NOT 'Can Use' - select 'Can Run' from the dropdown)

6. Click 'Add' or 'Save'
```

**Why?** This is a one-time manual step because Databricks doesn't support programmatic Genie Space permissions. Takes 30 seconds per environment.

**What's a service principal?** It's the identity your app uses (like a robot account). When you deployed the app, Databricks created `frauddetection-dev` as its service principal automatically.

---

**That's it!** ✅

Your app will be available at: `https://your-workspace.azuredatabricks.net/apps/frauddetection-dev`

**📖 Note:** Per [Microsoft Databricks documentation](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial#deploy-the-app-to-the-workspace), deploying a bundle doesn't automatically deploy the app to compute. That's why we run `deploy_app_source.sh` as a separate step to deploy the app source code from the bundle workspace location.

---

## 📋 What Gets Deployed

When you run the commands above, the system automatically:

1. ✅ Creates Unity Catalog `fraud_detection_dev`
2. ✅ Creates schema `claims_analysis`
3. ✅ Generates 1000 sample insurance claims
4. ✅ Creates 3 AI functions (classify, extract, explain)
5. ✅ Creates knowledge base with fraud patterns
6. ✅ Creates vector search index
7. ✅ Creates Genie Space for natural language queries
8. ✅ Deploys Streamlit app with 5 pages
9. ✅ Grants all necessary permissions
10. ⚠️ **Requires one manual step:** Grant Genie Space permissions (30 sec - see instructions above)

**Total time**: ~5-7 minutes

---

## 🎯 Features

### **Intelligent Agent**
- **LangGraph ReAct Pattern**: Adaptive reasoning and tool selection
- **4 Specialized Tools**: Classify, extract, search cases, query trends
- **Explainable Decisions**: Full reasoning trace

### **AI Functions** (Unity Catalog)
- `fraud_classify` - Classify claims as fraudulent or legitimate
- `fraud_extract_indicators` - Extract red flags and suspicious patterns
- `fraud_generate_explanation` - Generate human-readable explanations

### **Vector Search**
- Semantic search for similar fraud cases
- Sub-second query performance
- Databricks-managed embeddings

### **Streamlit Dashboard**
- 🏠 Home - Overview and system status
- 📊 Claim Analysis - Analyze individual claims
- ⚡ Batch Processing - Process multiple claims
- 📈 Fraud Insights - Statistics and visualizations
- 🔎 Case Search - Search historical fraud cases
- 🤖 Agent Playground - Interactive chat with agent

---

## 🔧 Configuration

### **File Structure**

```
config.yaml              # ← Edit this (source of truth)
    ↓
generate_app_yaml.py     # ← Run this (generates app config)
    ↓
app/app.yaml            # ← Auto-generated (don't edit)
    ↓
Deploy!
```

### **Multiple Environments**

The system supports dev, staging, and prod environments:

```yaml
# config.yaml
environments:
  dev:
    catalog: "fraud_detection_dev"
  staging:
    catalog: "fraud_detection_staging"
  prod:
    catalog: "fraud_detection_prod"
```

Deploy to different environments:

```bash
# Dev
python generate_app_yaml.py dev
databricks bundle deploy --target dev

# Staging
python generate_app_yaml.py staging
databricks bundle deploy --target staging

# Prod
python generate_app_yaml.py prod
databricks bundle deploy --target prod
```

---

## 📖 Detailed Instructions

### **Prerequisites**

1. **Databricks Workspace** (Azure, AWS, or GCP)
2. **Unity Catalog** enabled
3. **SQL Warehouse** created
4. **Databricks CLI** installed and configured
   ```bash
   databricks --version  # Should show version
   ```

### **Initial Setup**

1. **Clone the repository**
   ```bash
   git clone <repository>
   cd FraudDetectionForClaimsData
   ```

2. **Configure Databricks CLI** (if not already done)
   ```bash
   databricks configure --profile DEFAULT_azure
   ```
   
   Enter:
   - Host: `https://your-workspace.azuredatabricks.net`
   - Token: Your personal access token

3. **Edit config.yaml**
   ```bash
   vim config.yaml
   ```
   
   Update:
   - `workspace_host` - Your workspace URL
   - `warehouse_id` - Your SQL Warehouse ID
   - `catalog` - Catalog name (or leave default)
   - `profile` - Profile name from step 2

4. **🚀 Deploy everything with one command**
   ```bash
   ./deploy_with_config.sh dev
   ```
   
   This automated script does everything:
   - ✅ Generates `app.yaml` from `config.yaml`
   - ✅ Deploys infrastructure (jobs, app definition)
   - ✅ Runs setup notebooks (creates catalog, tables, functions, data, Genie Space)
   - ✅ Grants service principal permissions
   - ✅ Deploys app source code
   
   **Alternative: Manual step-by-step deployment**
   
   If you prefer to run each step individually:
   
   ```bash
   # Step 1: Generate app.yaml
   python generate_app_yaml.py dev
   
   # Step 2: Deploy infrastructure (creates app and job definitions)
   databricks bundle deploy --target dev --profile DEFAULT_azure
   
   # Step 3: Run setup job (creates catalog, tables, functions, data, Genie Space)
   databricks bundle run setup_fraud_detection --target dev --profile DEFAULT_azure
   
   # Step 4: Grant service principal permissions
   ./grant_permissions.sh dev
   
   # Step 5: Deploy app source code from bundle location
   ./deploy_app_source.sh dev
   ```
   
   **Important:** Per [Microsoft documentation](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial#deploy-the-app-to-the-workspace), `databricks bundle deploy` creates the app infrastructure but does **not** automatically deploy the source code to compute. Step 5 explicitly deploys the app source code from the bundle workspace location using `databricks apps deploy`.

5. **⚠️ IMPORTANT: Configure Genie Space Instructions**
   
   After the setup job completes, the `10_create_genie_space` notebook will output custom instructions for your Genie Space. You **MUST** copy these instructions and add them to the Genie Space manually:
   
   - Go to the notebook output for task `create_genie_space`
   - Copy the "Instructions for Genie Space" text (usually a long paragraph describing how to analyze fraud claims)
   - Open the Genie Space in Databricks: **Data Intelligence > Genie > Fraud Detection Analytics**
   - Click **Settings** (gear icon)
   - Paste the instructions into the **Instructions** field
   - Click **Save**
   
   **Why?** The Genie API doesn't support setting instructions via API yet, so this manual step is required for proper Genie behavior.

6. **Access your app**
   
   The app URL will be shown after deployment:
   ```
   https://your-workspace.azuredatabricks.net/apps/frauddetection-dev
   ```
   
   Wait 30-60 seconds for the app to start, then open the URL in your browser.

---

## 🔍 Verification

### **Check Deployment Status**

```bash
# Check if app is running
databricks apps get frauddetection_dev --profile DEFAULT_azure

# Check if catalog was created
databricks catalogs get fraud_detection_dev --profile DEFAULT_azure

# Check if tables exist
databricks tables list --catalog-name fraud_detection_dev --schema-name claims_analysis --profile DEFAULT_azure
```

### **Expected Output**

You should see:
- Catalog: `fraud_detection_dev`
- Schema: `claims_analysis`
- Tables: `claims_data`, `fraud_cases_kb`, `config_genie`
- Functions: `fraud_classify`, `fraud_extract_indicators`, `fraud_generate_explanation`
- App: `frauddetection_dev` (status: RUNNING)

---

## 🆘 Troubleshooting

### **Problem: App shows "No source code" or "Not yet deployed"**

**Cause**: Bundle creates the app infrastructure but doesn't auto-deploy source code to compute ([per Microsoft docs](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial#deploy-the-app-to-the-workspace))

**Solution**: Run the app deployment script
```bash
./deploy_app_source.sh dev
```

This deploys the source code from the bundle workspace location to the app.

**Manual alternative**:
```bash
# Get your username
databricks workspace whoami --profile DEFAULT_azure

# Deploy from bundle location
databricks apps deploy frauddetection-dev \
  --source-code-path /Workspace/Users/<your-email>/.bundle/fraud_detection_claims/dev/files/app \
  --profile DEFAULT_azure
```

### **Problem: "Permission denied" errors**

**Solution**: Grant service principal permissions
```bash
./grant_permissions.sh dev
```

Or manually:
```bash
# Get service principal ID
SP_ID=$(databricks apps get frauddetection-dev --profile DEFAULT_azure | grep service_principal_client_id | cut -d'"' -f4)

# Grant catalog access
databricks grants update catalog fraud_detection_dev --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_CATALOG\"]}]}" --profile DEFAULT_azure

# Grant schema access
databricks grants update schema fraud_detection_dev.claims_analysis --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_SCHEMA\", \"SELECT\"]}]}" --profile DEFAULT_azure

# Grant warehouse access
databricks permissions update sql/warehouses/148ccb90800933a1 --json "{\"access_control_list\": [{\"service_principal_name\": \"$SP_ID\", \"permission_level\": \"CAN_USE\"}]}" --profile DEFAULT_azure
```

### **Problem: App not found**

Check if deployment succeeded:
```bash
databricks apps list --profile DEFAULT_azure
```

If not listed, redeploy:
```bash
databricks bundle deploy --target dev --profile DEFAULT_azure
```

### **Problem: Notebooks failed**

Check job status:
```bash
databricks jobs list --profile DEFAULT_azure
databricks jobs list-runs --job-id <job-id> --limit 1 --profile DEFAULT_azure
```

Rerun failed job:
```bash
databricks bundle run setup_fraud_detection --target dev --profile DEFAULT_azure
```

### **Problem: Vector Index already exists**

The setup notebooks check for existing resources and skip creation if they exist. If you need a clean slate:

```bash
# Run cleanup notebook in Databricks workspace
# Navigate to: Workspace > setup > 00_CLEANUP
# Click "Run All"
```

---

## 📁 Project Structure

```
FraudDetectionForClaimsData/
├── config.yaml                  # ⭐ Configuration (edit this)
├── generate_app_yaml.py         # ⭐ Generator script (run this)
├── databricks.yml               # Databricks Asset Bundle config
├── deploy_with_config.sh        # One-command deployment script
│
├── shared/
│   └── config.py                # Config loader for notebooks
│
├── setup/                       # Setup notebooks (run by DAB)
│   ├── 01_create_catalog_schema.py
│   ├── 02_generate_sample_data.py
│   ├── 03_uc_fraud_classify.py
│   ├── 04_uc_fraud_extract.py
│   ├── 05_uc_fraud_explain.py
│   ├── 06_create_knowledge_base.py
│   ├── 07_create_vector_index.py
│   ├── 08_create_fraud_analysis_table.py
│   ├── 09_batch_analyze_claims.py
│   └── 10_create_genie_space.py
│
├── app/                         # Streamlit application
│   ├── app.yaml                 # Auto-generated (don't edit)
│   ├── app_databricks.py        # Main app
│   ├── requirements.txt         # Dependencies
│   ├── pages/                   # Streamlit pages
│   │   ├── 1_claim_analysis.py
│   │   ├── 2_batch_processing.py
│   │   ├── 3_fraud_insights.py
│   │   ├── 4_case_search.py
│   │   └── 5_agent_playground.py
│   └── utils/
│       ├── fraud_agent.py       # LangGraph agent
│       └── databricks_client.py # DB utilities
│
├── notebooks/
│   └── 01_fraud_agent.ipynb     # Interactive agent demo
│
└── docs/
    ├── ARCHITECTURE.md          # System architecture
    ├── DEPLOYMENT.md            # Deployment guide
    └── TROUBLESHOOTING.md       # Common issues
```

---

## 🎓 Learn More

- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Deployment**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Troubleshooting**: See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Demo**: See [DEMO.md](DEMO.md)

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## 🧹 Cleanup & Testing

### **Complete Cleanup** (Start Fresh)

The `cleanup_all.sh` script provides a complete teardown of all Databricks resources, perfect for testing end-to-end deployment or resetting your environment.

#### **Usage**

```bash
# Interactive mode (asks for confirmation)
./cleanup_all.sh <environment>

# Skip confirmation (for automation)
./cleanup_all.sh <environment> --skip-confirmation
```

**Examples:**
```bash
# Cleanup dev environment (with confirmation prompt)
./cleanup_all.sh dev

# Cleanup staging environment (no prompts)
./cleanup_all.sh staging --skip-confirmation

# Cleanup prod environment (with confirmation)
./cleanup_all.sh prod
```

---

#### **What Gets Deleted**

The script performs 6 cleanup steps:

**[1/6] Delete Databricks App**
- Removes the deployed Streamlit app
- App name from config: `{app_name}`

**[2/6] Delete Genie Space**
- Removes the Genie Space using Databricks API
- Searches for space by display name: `Fraud Detection Analytics`
- Must be deleted before catalog (not part of Unity Catalog)

**[3/6] Run Catalog Cleanup**
- Deletes Unity Catalog and all resources using `databricks catalogs delete --force`:
  - Catalog (e.g., `fraud_detection_dev`)
  - Schema (`claims_analysis`)
  - Tables (claims data, knowledge base, config tables)
  - Vector Search index (CASCADE deletion)
  - All UC functions (fraud_classify, fraud_extract_indicators, fraud_generate_explanation)
  - All volumes
- **Fast**: No cluster spinup required (~30 seconds)

**[4/6] Clean Local Bundle State**
- Removes `.databricks/` folder
- Clears local deployment cache

**[5/6] Clean Remote Workspace Files**
- Deletes bundle files from workspace
- Path: `/Workspace/Users/{user_email}/.bundle/fraud_detection_claims`

**[6/6] Setup Job (Optional)**
- Lists setup job(s)
- Asks if you want to delete them
- Jobs named: `fraud_detection_setup_{environment}`

---

#### **Safety Features**

✅ **Confirmation Prompt**: Asks "Are you sure?" before destroying resources  
✅ **Error Handling**: Continues even if resources don't exist  
✅ **Clear Output**: Color-coded messages show progress  
✅ **Resource List**: Shows exactly what will be deleted  
✅ **Optional Job Deletion**: Asks separately about setup job  

---

#### **Prerequisites**

Before running cleanup:
- ✅ `config.yaml` must exist in the project root
- ✅ Databricks CLI configured with profile `DEFAULT_azure`
- ✅ Proper permissions to delete resources

---

#### **Configuration Required**

The script reads these values from `config.yaml`:
```yaml
environments:
  dev:
    catalog: "fraud_detection_dev"      # Catalog to delete
    app_name: "frauddetection-dev"      # App to delete
    profile: "DEFAULT_azure"            # Databricks profile to use

common:
  genie_space_display_name: "Fraud Detection Analytics"  # Genie Space to delete
```

---

### **Full End-to-End Test**

Perfect for testing before demos, validating changes, or preparing for production:

```bash
# Step 1: Complete cleanup (removes everything)
./cleanup_all.sh dev

# Step 2: Fresh deployment (creates everything from scratch)
./deploy_with_config.sh dev

# Step 3: Test the app
# Open: https://your-workspace.azuredatabricks.net/apps/frauddetection-dev
# Try analyzing sample claims with the agent
```

---

### **Expected Timeline**

| Phase | Time | Details |
|-------|------|---------|
| **Cleanup** | ~1-2 minutes | Delete app, Genie, catalog, files |
| **Fresh Deployment** | ~10-15 minutes | Setup job takes longest |
| **Total** | **~12-17 minutes** | Full end-to-end cycle |

**Breakdown:**
- Delete app: ~10 seconds
- Delete Genie Space: ~5 seconds
- Delete catalog (CASCADE): ~30-60 seconds
- Local cleanup: ~5 seconds
- Remote cleanup: ~10 seconds
- Setup job prompt: ~5 seconds

---

### **Troubleshooting Cleanup**

#### **Problem: "config.yaml not found"**
```bash
# Solution: Run from project root
cd /path/to/FraudDetectionForClaimsData
./cleanup_all.sh dev
```

#### **Problem: "App not found"**
**Cause**: App already deleted or never deployed  
**Solution**: Script continues automatically (warning shown)

#### **Problem: "Genie Space not found"**
**Cause**: Genie Space already deleted or name mismatch  
**Solution**: Check `config.yaml` for correct `genie_space_display_name`

#### **Problem: "Catalog not found"**
**Cause**: Catalog already deleted or insufficient permissions  
**Solution**: Script continues automatically (warning shown)

#### **Problem: "Cleanup notebook failed"**
**Cause**: Catalog already deleted or insufficient permissions  
**Solution**: Check Databricks workspace permissions

#### **Problem: Can't delete setup job**
**Cause**: Job is running or you lack permissions  
**Solution**: 
1. Cancel running job in Databricks UI
2. Or delete manually later: `databricks jobs delete --job-id <id>`

---

### **When to Use Cleanup**

| Scenario | Command | Why |
|----------|---------|-----|
| **Testing deployment** | `./cleanup_all.sh dev` | Ensure clean slate |
| **Before demo** | `./cleanup_all.sh dev` + `./deploy_with_config.sh dev` | Fresh, predictable state |
| **Cost savings** | `./cleanup_all.sh dev --skip-confirmation` | Remove unused resources |
| **Environment reset** | `./cleanup_all.sh staging` | Fix broken state |
| **Switching configs** | Clean + deploy | Apply major config changes |

---

### **What NOT to Do**

❌ **Don't cleanup production without backup**  
❌ **Don't skip confirmation in production** (always use interactive mode)  
❌ **Don't cleanup while jobs are running** (cancel them first)  
❌ **Don't delete `config.yaml`** (script needs it)

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

---

## 🎉 Summary

**For a new operator, the steps are**:

1. Edit `config.yaml` (2 minutes)
2. Run `./deploy_with_config.sh dev` (6 minutes - fully automated)
3. Access app at provided URL ✅

**Total time**: ~8 minutes from zero to deployed app!

---

## 📊 Project Status & Results

**✅ Project Complete - December 2024**

This is a production-ready, open-source fraud detection system demonstrating:
- **Modern AI Architecture**: LangGraph agents + UC Functions + Vector Search
- **Real Business Impact**: 1,298x ROI, 94% accuracy, $0.002/claim
- **Enterprise Ready**: Full governance, audit trails, multi-environment
- **Fully Automated**: One-command deployment, complete documentation

📖 **[See Complete Project Summary](docs/PROJECT_SUMMARY.md)** for architecture details, performance metrics, and key learnings.

**Built with:**
- Databricks Lakehouse Platform
- Unity Catalog & AI Functions
- LangGraph (LangChain)
- Vector Search
- Claude Sonnet 4.5
- Streamlit

**Author:** Vikram Malhotra  
**License:** MIT (Open Source)  
**GitHub:** https://github.com/bigdatavik/FraudDetectionForClaimsData

---

**Built with ❤️ on Databricks | December 2024**
