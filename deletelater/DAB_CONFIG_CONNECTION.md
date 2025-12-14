# 🎯 How DAB Targets Connect to config.yaml

## ✅ THE COMPLETE FLOW

```
databricks bundle deploy --target prod
         ↓
databricks.yml (defines targets)
         ↓
targets.prod.variables.environment = "prod"
         ↓
Passes "environment=prod" to notebooks
         ↓
Notebook: dbutils.widgets.get("environment")  # Gets "prod"
         ↓
shared/config.py: get_config()  # Detects widget value
         ↓
Reads config.yaml environments.prod section
         ↓
Uses: fraud_detection_prod catalog
```

---

## 📝 HOW IT WORKS NOW (UPDATED)

### **Step 1: databricks.yml Defines Targets**

```yaml
targets:
  dev:
    variables:
      environment: dev    # ← Sets widget value
  
  staging:
    variables:
      environment: staging  # ← Sets widget value
  
  prod:
    variables:
      environment: prod     # ← Sets widget value
```

### **Step 2: Targets Pass to Notebooks**

```yaml
tasks:
  - task_key: create_catalog
    notebook_task:
      notebook_path: ./setup/01_create_catalog_schema.py
      base_parameters:
        environment: ${var.environment}  # ← Passed as widget
```

### **Step 3: Notebooks Receive Widget**

When DAB deploys, it creates a widget in each notebook:
```python
# Databricks automatically creates:
dbutils.widgets.text("environment", "prod")  # If --target prod
```

### **Step 4: shared/config.py Detects Widget**

```python
# shared/config.py (lines 114-117)
try:
    environment = dbutils.widgets.get("environment")  # ← Gets "prod"
    print(f"✅ Using environment from DAB widget: {environment}")
except:
    pass
```

### **Step 5: Reads config.yaml for That Environment**

```python
# shared/config.py (lines 140-143)
env_config = config['environments']['prod']  # ← Loads prod section
common_config = config['common']

return FraudDetectionConfig(env_config, common_config)
```

### **Step 6: Notebook Uses Prod Values**

```python
from shared.config import get_config
cfg = get_config()
# ✅ Using environment from DAB widget: prod

print(cfg.catalog)  # "fraud_detection_prod"
print(cfg.schema)   # "claims_analysis"

spark.sql(f"CREATE CATALOG IF NOT EXISTS {cfg.catalog}")
# Creates: fraud_detection_prod
```

---

## 🚀 USAGE EXAMPLES

### **Deploy to Dev**
```bash
databricks bundle deploy --target dev
databricks bundle run setup_fraud_detection --target dev

# Result:
# - Job name: fraud_detection_setup_dev
# - Widget: environment=dev
# - Config reads: environments.dev from config.yaml
# - Creates: fraud_detection_dev catalog
```

### **Deploy to Staging**
```bash
databricks bundle deploy --target staging
databricks bundle run setup_fraud_detection --target staging

# Result:
# - Job name: fraud_detection_setup_staging
# - Widget: environment=staging
# - Config reads: environments.staging from config.yaml
# - Creates: fraud_detection_staging catalog
```

### **Deploy to Prod**
```bash
databricks bundle deploy --target prod
databricks bundle run setup_fraud_detection --target prod

# Result:
# - Job name: fraud_detection_setup_prod
# - Widget: environment=prod
# - Config reads: environments.prod from config.yaml
# - Creates: fraud_detection_prod catalog
```

---

## 📊 COMPLETE ARCHITECTURE

```
┌─────────────────────────────────────────────┐
│  YOU RUN:                                   │
│  databricks bundle deploy --target prod     │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  databricks.yml                             │
│                                             │
│  targets:                                   │
│    prod:                                    │
│      variables:                             │
│        environment: prod  ← TARGET VALUE    │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Databricks Creates Widget in Notebook      │
│                                             │
│  dbutils.widgets.text("environment", "prod")│
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Notebook Runs: get_config()                │
│                                             │
│  shared/config.py detects widget:           │
│  environment = dbutils.widgets.get(...)     │
│  # Returns: "prod"                          │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  shared/config.py Reads config.yaml         │
│                                             │
│  config['environments']['prod']  ← MATCHES! │
│                                             │
│  Returns:                                   │
│  - catalog: "fraud_detection_prod"         │
│  - schema: "claims_analysis"               │
│  - warehouse_id: "..."                     │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Notebook Uses Values                       │
│                                             │
│  spark.sql(f"CREATE CATALOG {cfg.catalog}")│
│  # Creates: fraud_detection_prod           │
└─────────────────────────────────────────────┘
```

---

## 🎯 KEY POINTS

1. **databricks.yml targets** define the environment name
2. **DAB passes it as a widget** to notebooks
3. **shared/config.py detects the widget** automatically
4. **config.yaml provides the actual values** for that environment
5. **Notebooks use the right environment** without code changes

---

## ✅ WHAT YOU NEED TO KNOW

### **To Switch Environments**:
```bash
# Just change --target flag:
databricks bundle deploy --target dev      # Uses dev config
databricks bundle deploy --target staging  # Uses staging config
databricks bundle deploy --target prod     # Uses prod config
```

### **No Code Changes Needed**:
- Notebooks stay the same
- config.yaml has all three environments
- databricks.yml connects the dots
- Everything is automatic!

---

## 📝 QUICK REFERENCE

```bash
# Deploy to environment
databricks bundle deploy --target [dev|staging|prod]

# Run job in environment
databricks bundle run setup_fraud_detection --target [dev|staging|prod]

# What happens:
1. DAB reads databricks.yml target
2. Sets widget: environment=[dev|staging|prod]
3. Notebook calls: get_config()
4. Config reads: config.yaml environments.[dev|staging|prod]
5. Uses: fraud_detection_[dev|staging|prod] catalog
```

---

## 🎊 SUMMARY

**Question**: "When I use `databricks bundle deploy --target prod`, does it pick values from config.yaml?"

**Answer**: YES! Here's how:
1. `--target prod` → Sets `environment` variable to `"prod"` in databricks.yml
2. DAB passes `environment=prod` as widget to notebooks
3. Notebooks call `get_config()` from shared/config.py
4. `get_config()` detects widget value `"prod"`
5. Reads `config.yaml` → `environments.prod` section
6. Uses prod values: `fraud_detection_prod`, etc.

**One command, automatic environment detection, values from config.yaml!** ✅

