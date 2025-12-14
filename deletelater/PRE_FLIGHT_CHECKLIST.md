# ✅ Pre-Flight Checklist - Testing From Scratch

## 📋 Before You Start

### **1. Verify Prerequisites**
```bash
# Check Databricks CLI is installed
databricks --version

# Check you're authenticated
databricks workspace list --profile DEFAULT_azure | head -5

# Check Python is available
python --version
```

---

## 🔧 Clean Setup Files

### **Already Done** ✅
- [x] Removed all `.bak` files from `setup/` folder
- [x] Cleaned up old documentation to `deletelater/`
- [x] Updated `README.md` with clear instructions

---

## 🚀 Testing Steps (Follow README.md)

### **Step 1: Configure** (2 minutes)
```bash
# Edit config.yaml
vim config.yaml
```

**Update these values**:
- Line 10: `workspace_host` - Your Databricks URL
- Line 11: `profile` - Your profile name (usually `DEFAULT_azure`)
- Line 14: `warehouse_id` - Your SQL Warehouse ID

**How to find values**:
```bash
# Check your profile
cat ~/.databrickscfg

# Get warehouse ID from UI:
# Databricks → SQL → Warehouses → Click warehouse → Copy ID from URL
```

---

### **Step 2: Generate App Config** (10 seconds)
```bash
python generate_app_yaml.py dev
```

**Expected output**:
```
======================================================================
🤖 GENERATING app.yaml FROM config.yaml
======================================================================
Environment: dev
Catalog:     fraud_detection_dev
...
✅ Generated: /Users/vik.malhotra/FraudDetectionForClaimsData/app/app.yaml

✅ SUCCESS!
```

**Verify**:
```bash
cat app/app.yaml | head -20
```

---

### **Step 3: Deploy** (5-7 minutes)
```bash
# Deploy infrastructure
databricks bundle deploy --target dev --profile DEFAULT_azure

# Run setup job (creates everything)
databricks bundle run setup_fraud_detection --target dev --profile DEFAULT_azure
```

**Expected**:
- Job creates catalog
- Generates sample data
- Creates UC functions
- Creates vector index
- Deploys app

---

### **Step 4: Grant Permissions** ⚠️ **CRITICAL**

After app is deployed, grant service principal permissions:

```bash
./grant_permissions.sh dev
```

**This grants**:
- ✅ Catalog access (`USE_CATALOG`)
- ✅ Schema access (`USE_SCHEMA`, `SELECT`)
- ✅ Warehouse access (`CAN_USE`)

**Expected output**:
```
======================================================================
🔒 GRANTING SERVICE PRINCIPAL PERMISSIONS
======================================================================
✅ Service Principal ID: abc123-def456-...
  1️⃣  Granting CATALOG permissions...
      ✅ USE_CATALOG granted
  2️⃣  Granting SCHEMA permissions...
      ✅ USE_SCHEMA, SELECT granted
  3️⃣  Granting WAREHOUSE permissions...
      ✅ CAN_USE granted
✅ ALL PERMISSIONS GRANTED SUCCESSFULLY!
```

**Why this matters**: Without permissions, app shows "Database connection error"

---

## 🔍 Verification Commands

### **Check Catalog**
```bash
databricks catalogs get fraud_detection_dev --profile DEFAULT_azure
```

### **Check Tables**
```bash
databricks tables list \
  --catalog-name fraud_detection_dev \
  --schema-name claims_analysis \
  --profile DEFAULT_azure
```

### **Check App**
```bash
databricks apps get frauddetection_dev --profile DEFAULT_azure
```

### **Check App Logs** (if issues)
```bash
databricks apps logs frauddetection_dev --profile DEFAULT_azure
```

---

## 🎯 Expected Results

### **After Deployment**:
- ✅ Catalog: `fraud_detection_dev`
- ✅ Schema: `claims_analysis`
- ✅ Tables: `claims_data`, `fraud_cases_kb`, `config_genie`
- ✅ Functions: `fraud_classify`, `fraud_extract_indicators`, `fraud_generate_explanation`
- ✅ App: `frauddetection_dev` (status: RUNNING)

### **App URL**:
```
https://adb-984752964297111.11.azuredatabricks.net/apps/frauddetection_dev
```

---

## 🆘 If Something Goes Wrong

### **Job Failed?**
```bash
# Check job status
databricks jobs list --profile DEFAULT_azure | grep fraud_detection

# Get job ID and check logs
databricks jobs list-runs --job-id <JOB_ID> --limit 1 --profile DEFAULT_azure
```

### **Permission Error?**
```bash
# Get service principal ID
SP_ID=$(databricks apps get frauddetection_dev --profile DEFAULT_azure | grep service_principal_id | cut -d'"' -f4)

# Grant permissions
databricks grants update catalog fraud_detection_dev \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_CATALOG\"]}]}" \
  --profile DEFAULT_azure
```

### **App Not Starting?**
```bash
# Check app status
databricks apps get frauddetection_dev --profile DEFAULT_azure

# Check logs
databricks apps logs frauddetection_dev --profile DEFAULT_azure

# Redeploy
databricks bundle deploy --target dev --profile DEFAULT_azure
```

---

## 📝 Test Checklist

- [ ] Step 1: Edited `config.yaml`
- [ ] Step 2: Ran `python generate_app_yaml.py dev`
- [ ] Step 3: Ran `databricks bundle deploy --target dev`
- [ ] Step 4: Ran `databricks bundle run setup_fraud_detection --target dev`
- [ ] Verified: Catalog exists
- [ ] Verified: Tables exist
- [ ] Verified: Functions exist
- [ ] Verified: App is running
- [ ] Tested: Opened app URL in browser

---

## 🎉 Success Criteria

**You're done when**:
1. ✅ All commands run without errors
2. ✅ App status shows "RUNNING"
3. ✅ App URL opens in browser
4. ✅ Dashboard shows all components working

---

## 📞 Quick Commands Reference

```bash
# Deploy
databricks bundle deploy --target dev --profile DEFAULT_azure

# Run setup
databricks bundle run setup_fraud_detection --target dev --profile DEFAULT_azure

# Check app
databricks apps get frauddetection_dev --profile DEFAULT_azure

# Check logs
databricks apps logs frauddetection_dev --profile DEFAULT_azure

# List catalogs
databricks catalogs list --profile DEFAULT_azure

# List tables
databricks tables list --catalog-name fraud_detection_dev --schema-name claims_analysis --profile DEFAULT_azure
```

---

**Good luck with testing! Everything is clean and ready to go!** 🚀

