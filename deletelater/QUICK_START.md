# ⚡ Quick Reference Card

## 🚀 New Operator - 3 Steps to Deploy

### **Step 1: Configure (2 min)**
```bash
vim config.yaml
```
Update:
- `workspace_host` → Your Databricks URL
- `warehouse_id` → Your SQL Warehouse ID  
- `profile` → Your CLI profile name

---

### **Step 2: Generate (10 sec)**
```bash
python generate_app_yaml.py dev
```

---

### **Step 3: Deploy (5 min)**
```bash
databricks bundle deploy --target dev
databricks bundle run setup_fraud_detection --target dev
```

### **Step 4: Grant Permissions ⚠️**
```bash
./grant_permissions.sh dev
```

**Done!** App at: `https://your-workspace/apps/frauddetection_dev`

---

## 📋 Common Commands

```bash
# Deploy to different environments
databricks bundle deploy --target [dev|staging|prod]

# Run setup job
databricks bundle run setup_fraud_detection --target [dev|staging|prod]

# Generate app config
python generate_app_yaml.py [dev|staging|prod]

# Check app status
databricks apps get frauddetection_dev

# Check logs
databricks apps logs frauddetection_dev

# List catalogs
databricks catalogs list

# List tables
databricks tables list --catalog-name fraud_detection_dev --schema-name claims_analysis
```

---

## 🔧 Configuration Files

| File | Purpose | Edit? |
|------|---------|-------|
| `config.yaml` | Source of truth | ✅ YES |
| `generate_app_yaml.py` | Generator script | ❌ NO |
| `app/app.yaml` | Generated config | ❌ NO (auto-gen) |
| `databricks.yml` | DAB config | ❌ NO |

---

## 🎯 What Gets Created

| Environment | Catalog | App Name |
|-------------|---------|----------|
| dev | `fraud_detection_dev` | `frauddetection_dev` |
| staging | `fraud_detection_staging` | `frauddetection_staging` |
| prod | `fraud_detection_prod` | `frauddetection_prod` |

---

## 🆘 Quick Fixes

**Permission Error?**
```bash
SP_ID=$(databricks apps get frauddetection_dev | grep service_principal_id | cut -d'"' -f4)
databricks grants update catalog fraud_detection_dev --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_CATALOG\"]}]}"
```

**App Not Running?**
```bash
databricks apps get frauddetection_dev
databricks apps logs frauddetection_dev
```

**Redeploy?**
```bash
databricks bundle deploy --target dev
```

---

## 📁 Important Files

```
config.yaml              ← Edit this
generate_app_yaml.py     ← Run this
app/app.yaml            ← Auto-generated
databricks.yml          ← Don't touch
```

---

## 🎉 That's It!

**Remember**: 
1. Edit `config.yaml`
2. Run `python generate_app_yaml.py dev`
3. Deploy with `databricks bundle deploy`

**Simple!** ✅

