# 🎯 Configuration Flow - Visual Summary

## Single Command to Update Everything

```bash
# 1. Edit config
vim config.yaml

# 2. Generate app.yaml
python generate_app_yaml.py dev

# 3. Deploy
databricks bundle deploy
```

**Result**: Notebooks AND Streamlit app use your new config! ✅

---

## 📊 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     config.yaml                              │
│              (YOU EDIT THIS - Source of Truth)               │
│                                                              │
│  default_environment: dev                                    │
│                                                              │
│  environments:                                               │
│    dev:                                                      │
│      catalog: "fraud_detection_dev"                         │
│      schema: "claims_analysis"                              │
│      warehouse_id: "148ccb90800933a1"                       │
│      llm_endpoint: "databricks-claude-sonnet-4-5"          │
│                                                              │
│    staging: { ... }                                          │
│    prod: { ... }                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌───────────────┐ ┌────────────┐ ┌───────────────┐
│generate_app_  │ │  shared/   │ │ databricks.yml│
│   yaml.py     │ │  config.py │ │   (manual)    │
│               │ │            │ │               │
│ Reads yaml    │ │ Reads yaml │ │ References    │
│ Generates     │ │ Returns    │ │ config values │
│ app.yaml      │ │ object     │ │               │
└──────┬────────┘ └──────┬─────┘ └──────┬────────┘
       │                 │               │
       ▼                 ▼               │
┌──────────────┐  ┌──────────────┐      │
│ app/app.yaml │  │  Notebooks   │      │
│              │  │              │      │
│ env:         │  │ cfg.catalog  │      │
│ - CATALOG... │  │ cfg.schema   │      │
│ - SCHEMA...  │  │ cfg.warehouse│      │
│ - WAREHOUSE..│  └──────────────┘      │
└──────┬───────┘                        │
       │                                │
       ▼                                │
┌──────────────┐                        │
│ app/config.py│                        │
│              │                        │
│ os.getenv()  │                        │
│ Returns obj  │                        │
└──────┬───────┘                        │
       │                                │
       ▼                                ▼
┌─────────────────────────────────────────┐
│         Streamlit Pages                 │
│                                         │
│  from config import get_config          │
│  cfg = get_config()                     │
│                                         │
│  cfg.catalog    → "fraud_detection_dev" │
│  cfg.schema     → "claims_analysis"     │
│  cfg.warehouse  → "148ccb90800933a1"    │
└─────────────────────────────────────────┘
```

---

## 🔄 Two Execution Paths

### Path 1: Databricks Notebooks

```
config.yaml
    ↓ [shared/config.py reads file]
FraudDetectionConfig object
    ↓ [notebook imports]
cfg.catalog, cfg.schema, cfg.warehouse_id
```

**Code**:
```python
from shared.config import get_config
cfg = get_config()  # Reads config.yaml from disk
```

---

### Path 2: Streamlit App (Databricks Apps)

```
config.yaml
    ↓ [generate_app_yaml.py converts]
app/app.yaml (env vars)
    ↓ [Databricks Apps sets env]
AppConfig object
    ↓ [app imports]
cfg.catalog, cfg.schema, cfg.warehouse_id
```

**Code**:
```python
from config import get_config
cfg = get_config()  # Reads env vars from app.yaml
```

---

## 🎯 Key Insight

**Same API, Different Source**:

```python
# Both use identical code:
cfg = get_config()
print(cfg.catalog)
print(cfg.schema)
print(cfg.warehouse_id)

# But different implementations:
# - Notebooks: reads YAML file
# - Streamlit: reads environment variables
```

**Why?**
- Notebooks run in workspace with file access
- Databricks Apps run in containers with env vars only

---

## 📝 Example: Changing Catalog Name

### Before
```yaml
# config.yaml
environments:
  dev:
    catalog: "fraud_detection_dev"
```

### Step 1: Edit
```yaml
# config.yaml
environments:
  dev:
    catalog: "my_fraud_system"  # ← CHANGED
```

### Step 2: Generate
```bash
python generate_app_yaml.py dev
```

**Generates**:
```yaml
# app/app.yaml (AUTO-GENERATED)
env:
  - name: 'CATALOG_NAME'
    value: 'my_fraud_system'  # ← UPDATED
```

### Step 3: Deploy
```bash
databricks bundle deploy
```

### Result
- ✅ Notebooks use `my_fraud_system`
- ✅ Streamlit uses `my_fraud_system`
- ✅ Changed in ONE place, works EVERYWHERE

---

## 🚀 Environment Switching

```bash
# Deploy to dev
python generate_app_yaml.py dev
databricks bundle deploy
# App uses: fraud_detection_dev

# Deploy to staging
python generate_app_yaml.py staging
databricks bundle deploy
# App uses: fraud_detection_staging

# Deploy to prod
python generate_app_yaml.py prod
databricks bundle deploy
# App uses: fraud_detection_prod
```

**Same code, different data!**

---

## 📋 File Purposes

| File | Type | Purpose | Edit? |
|------|------|---------|-------|
| `config.yaml` | YAML | Source of truth | ✅ YES |
| `generate_app_yaml.py` | Python | Generator | Only to add new vars |
| `app/app.yaml` | YAML | Generated config | ❌ NO (auto-gen) |
| `shared/config.py` | Python | Notebook loader | Only for features |
| `app/config.py` | Python | App loader | Only to add new vars |
| `databricks.yml` | YAML | DAB config | ✅ YES (manual) |

---

## 🎓 Quick Reference

### I want to...

**Change a setting**:
1. Edit `config.yaml`
2. Run `python generate_app_yaml.py [env]`
3. Deploy

**Switch environments**:
```bash
python generate_app_yaml.py staging
```

**Add new configuration**:
1. Add to `config.yaml`
2. Update `generate_app_yaml.py` (add env var)
3. Update `app/config.py` (read env var)
4. Regenerate and deploy

**Check current config**:
```bash
# For notebooks
cat config.yaml

# For app
cat app/app.yaml
```

**Test config loading**:
```bash
# Test app config
cd app && python config.py
```

---

## ✅ Benefits of This Architecture

1. **Single Source of Truth** - Edit once, works everywhere
2. **Environment Isolation** - Dev/staging/prod in one file
3. **Type Safety** - Python objects, not string parsing
4. **Validation** - Catch missing configs early
5. **Documentation** - Config values self-documented
6. **Version Control** - Track config changes in Git
7. **Testable** - Can test config loading independently

---

## 🚨 Common Mistakes to Avoid

❌ **Editing app/app.yaml directly**
```bash
# DON'T DO THIS
vim app/app.yaml  # Gets overwritten!
```

✅ **Edit config.yaml instead**
```bash
# DO THIS
vim config.yaml
python generate_app_yaml.py dev
```

---

❌ **Using shared/config.py in Streamlit**
```python
# DON'T DO THIS (in Streamlit pages)
from shared.config import get_config
```

✅ **Use app/config.py in Streamlit**
```python
# DO THIS (in Streamlit pages)
from config import get_config
```

---

❌ **Hardcoding values**
```python
# DON'T DO THIS
spark.sql("SELECT * FROM fraud_detection_dev.claims_analysis.claims_data")
```

✅ **Use config object**
```python
# DO THIS
cfg = get_config()
spark.sql(f"SELECT * FROM {cfg.claims_table}")
```

---

## 🎊 Summary

```
┌────────────────────────────────────────────┐
│  1. Edit config.yaml (source of truth)     │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│  2. Run: python generate_app_yaml.py dev   │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│  3. Deploy: databricks bundle deploy       │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│  ✅ Notebooks AND App use new config!      │
└────────────────────────────────────────────┘
```

**One source, many consumers, zero confusion!**

---

**See CONFIG_ARCHITECTURE.md for detailed documentation**

