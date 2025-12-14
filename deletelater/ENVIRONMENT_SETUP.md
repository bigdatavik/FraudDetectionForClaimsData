# ✅ Option 1: Single Workspace, Multiple Catalogs

## 🎯 Configuration Summary

**Strategy**: All environments (dev/staging/prod) run in the **same Databricks workspace**, separated by **different Unity Catalog names**.

---

## 📊 Current Setup

### **Workspace**
- **URL**: `https://adb-984752964297111.11.azuredatabricks.net`
- **Profile**: `DEFAULT_azure`
- **Used by**: All environments (dev, staging, prod)

### **Separation Method**
Environments are separated by Unity Catalog names:

| Environment | Catalog Name | App Name |
|-------------|--------------|----------|
| **dev** | `fraud_detection_dev` | `fraud-detection-dev` |
| **staging** | `fraud_detection_staging` | `fraud-detection-staging` |
| **prod** | `fraud_detection_prod` | `fraud-detection-prod` |

---

## 📁 File Configuration

### **databricks.yml**
```yaml
targets:
  dev:
    workspace:
      host: https://adb-984752964297111.11.azuredatabricks.net
      profile: DEFAULT_azure
    variables:
      environment: dev

  staging:
    workspace:
      host: https://adb-984752964297111.11.azuredatabricks.net  # Same!
      profile: DEFAULT_azure  # Same!
    variables:
      environment: staging

  prod:
    workspace:
      host: https://adb-984752964297111.11.azuredatabricks.net  # Same!
      profile: DEFAULT_azure  # Same!
    variables:
      environment: prod
```

### **config.yaml**
```yaml
environments:
  dev:
    workspace_host: "https://adb-984752964297111.11.azuredatabricks.net"
    catalog: "fraud_detection_dev"  # Unique

  staging:
    workspace_host: "https://adb-984752964297111.11.azuredatabricks.net"  # Same!
    catalog: "fraud_detection_staging"  # Unique

  prod:
    workspace_host: "https://adb-984752964297111.11.azuredatabricks.net"  # Same!
    catalog: "fraud_detection_prod"  # Unique
```

**✅ Both files now match!**

---

## 🔄 Complete Flow

```
┌─────────────────────────────────────────────────────────┐
│ YOU RUN: databricks bundle deploy --target staging     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ databricks.yml (WHERE)                                  │
│                                                         │
│ targets.staging:                                        │
│   workspace:                                            │
│     host: https://adb-984752964297111.11...            │
│     profile: DEFAULT_azure                              │
│   variables:                                            │
│     environment: staging                                │
│                                                         │
│ → Deploys to: Same workspace as dev                   │
│ → Passes: environment=staging to notebooks             │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Notebook runs: cfg = get_config()                      │
│                                                         │
│ shared/config.py detects widget: "staging"             │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ config.yaml (WHAT)                                      │
│                                                         │
│ environments.staging:                                   │
│   workspace_host: (informational only)                 │
│   catalog: "fraud_detection_staging"                   │
│   warehouse_id: "148ccb90800933a1"                     │
│   llm_endpoint: "databricks-claude-sonnet-4-5"        │
│                                                         │
│ → Creates: fraud_detection_staging catalog            │
│ → Uses: staging-specific resources                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Usage Examples

### **Deploy Dev Environment**
```bash
databricks bundle deploy --target dev
databricks bundle run setup_fraud_detection --target dev

# Result:
# - Deploys to: adb-984752964297111.11.azuredatabricks.net
# - Creates: fraud_detection_dev catalog
# - App name: fraud-detection-dev
```

### **Deploy Staging Environment**
```bash
databricks bundle deploy --target staging
databricks bundle run setup_fraud_detection --target staging

# Result:
# - Deploys to: adb-984752964297111.11.azuredatabricks.net (same!)
# - Creates: fraud_detection_staging catalog (different!)
# - App name: fraud-detection-staging
```

### **Deploy Prod Environment**
```bash
databricks bundle deploy --target prod
databricks bundle run setup_fraud_detection --target prod

# Result:
# - Deploys to: adb-984752964297111.11.azuredatabricks.net (same!)
# - Creates: fraud_detection_prod catalog (different!)
# - App name: fraud-detection-prod
```

---

## ✅ Benefits of This Approach

### **Pros**:
1. ✅ **Simple** - One workspace to manage
2. ✅ **Same credentials** - One profile (DEFAULT_azure)
3. ✅ **Cost-effective** - Share compute resources
4. ✅ **Easy testing** - Switch environments instantly
5. ✅ **Clear separation** - Different catalogs prevent conflicts

### **How Separation Works**:
- **Unity Catalog isolation** - Each environment has its own catalog
- **Different tables** - `fraud_detection_dev.claims_analysis.claims_data` vs `fraud_detection_staging.claims_analysis.claims_data`
- **Different apps** - `fraud-detection-dev` vs `fraud-detection-staging` vs `fraud-detection-prod`
- **Can use different warehouses** (optional) - Change `warehouse_id` in config.yaml if needed

---

## 📋 What's in Each Environment

### **Dev** (`fraud_detection_dev`)
```
Catalog: fraud_detection_dev
├── Schema: claims_analysis
│   ├── Tables:
│   │   ├── claims_data
│   │   ├── fraud_cases_kb
│   │   └── config_genie
│   ├── Functions:
│   │   ├── fraud_classify
│   │   ├── fraud_extract_indicators
│   │   └── fraud_generate_explanation
│   └── Vector Index: fraud_cases_index
└── App: fraud-detection-dev
```

### **Staging** (`fraud_detection_staging`)
```
Catalog: fraud_detection_staging
├── Schema: claims_analysis
│   ├── Tables: (same structure as dev)
│   ├── Functions: (same structure as dev)
│   └── Vector Index: (same structure as dev)
└── App: fraud-detection-staging
```

### **Prod** (`fraud_detection_prod`)
```
Catalog: fraud_detection_prod
├── Schema: claims_analysis
│   ├── Tables: (same structure as dev)
│   ├── Functions: (same structure as dev)
│   └── Vector Index: (same structure as dev)
└── App: fraud-detection-prod
```

**All in the same workspace, completely isolated by catalog!**

---

## 🔧 Making Changes

### **To Add a New Configuration Value**:

1. **Edit config.yaml** (for all environments):
```yaml
environments:
  dev:
    new_setting: "value_dev"
  staging:
    new_setting: "value_staging"
  prod:
    new_setting: "value_prod"
```

2. **Regenerate app.yaml** (if needed for Streamlit):
```bash
python generate_app_yaml.py dev
```

3. **Deploy**:
```bash
databricks bundle deploy --target dev
```

### **To Switch Environments**:
Just change the `--target` flag:
```bash
databricks bundle deploy --target [dev|staging|prod]
```

---

## 🎯 Key Points

1. **Same workspace** - All environments use `adb-984752964297111.11.azuredatabricks.net`
2. **Different catalogs** - Separation via Unity Catalog names
3. **Same profile** - `DEFAULT_azure` for all
4. **Environment variable** - `databricks.yml` passes environment name to notebooks
5. **Config lookup** - `shared/config.py` reads correct section from `config.yaml`

---

## ✅ Configuration Alignment

**databricks.yml** (WHERE to deploy):
- ✅ dev → `adb-984752964297111.11.azuredatabricks.net`
- ✅ staging → `adb-984752964297111.11.azuredatabricks.net`
- ✅ prod → `adb-984752964297111.11.azuredatabricks.net`

**config.yaml** (WHAT to create):
- ✅ dev → `adb-984752964297111.11.azuredatabricks.net` + `fraud_detection_dev`
- ✅ staging → `adb-984752964297111.11.azuredatabricks.net` + `fraud_detection_staging`
- ✅ prod → `adb-984752964297111.11.azuredatabricks.net` + `fraud_detection_prod`

**✅ Files are now aligned!**

---

## 🎊 Summary

**Single workspace, multiple catalogs approach**:
- All environments in same workspace
- Unity Catalog provides isolation
- Simple to manage and deploy
- Cost-effective resource sharing
- Easy environment switching

**One workspace, three environments, zero confusion!** ✅

