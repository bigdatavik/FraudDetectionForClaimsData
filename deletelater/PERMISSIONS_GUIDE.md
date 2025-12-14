# 🔒 Service Principal Permissions Guide

## ⚠️ **WHY THIS IS CRITICAL**

When Databricks deploys your app, it creates a **service principal** (machine identity) that runs the app. This service principal needs permissions to:
1. Access your Unity Catalog
2. Query your schema/tables
3. Use your SQL Warehouse

**Without these permissions, your app will fail with**: `"Database connection error: Error during request to server"`

---

## 🚀 **Quick Start - Grant Permissions**

### **After deploying your app, run**:

```bash
./grant_permissions.sh dev
```

That's it! The script automatically:
1. Gets your app's service principal ID
2. Grants catalog permissions
3. Grants schema permissions
4. Grants warehouse permissions

---

## 📋 **What the Script Does**

The `grant_permissions.sh` script executes these 3 commands:

### **1. Catalog Permission**
```bash
databricks grants update catalog fraud_detection_dev \
  --json '{"changes": [{"principal": "<SP_ID>", "add": ["USE_CATALOG"]}]}'
```

### **2. Schema Permission**
```bash
databricks grants update schema fraud_detection_dev.claims_analysis \
  --json '{"changes": [{"principal": "<SP_ID>", "add": ["USE_SCHEMA", "SELECT"]}]}'
```

### **3. Warehouse Permission**
```bash
databricks permissions update sql/warehouses/<WAREHOUSE_ID> \
  --json '{"access_control_list": [{"service_principal_name": "<SP_ID>", "permission_level": "CAN_USE"}]}'
```

---

## 🎯 **Usage Examples**

### **Dev Environment**
```bash
./grant_permissions.sh dev
```

### **Staging Environment**
```bash
./grant_permissions.sh staging
```

### **Prod Environment**
```bash
./grant_permissions.sh prod
```

---

## 🔍 **How to Find Service Principal ID**

If you need to check the service principal manually:

```bash
# Get app details
databricks apps get frauddetection_dev --profile DEFAULT_azure

# Look for this line:
# service_principal_client_id: abc123-def456-...
```

---

## 🛠️ **Manual Permission Grant** (if script fails)

If the automated script doesn't work, grant permissions manually:

### **Step 1: Get Service Principal ID**
```bash
SP_ID=$(databricks apps get frauddetection_dev --profile DEFAULT_azure --output json | python3 -c "import sys, json; print(json.load(sys.stdin)['service_principal_client_id'])")

echo "Service Principal: $SP_ID"
```

### **Step 2: Grant Catalog Access**
```bash
databricks grants update catalog fraud_detection_dev \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_CATALOG\"]}]}" \
  --profile DEFAULT_azure
```

### **Step 3: Grant Schema Access**
```bash
databricks grants update schema fraud_detection_dev.claims_analysis \
  --json "{\"changes\": [{\"principal\": \"$SP_ID\", \"add\": [\"USE_SCHEMA\", \"SELECT\"]}]}" \
  --profile DEFAULT_azure
```

### **Step 4: Grant Warehouse Access**
```bash
WAREHOUSE_ID="148ccb90800933a1"  # Your warehouse ID

databricks permissions update sql/warehouses/$WAREHOUSE_ID \
  --json "{\"access_control_list\": [{\"service_principal_name\": \"$SP_ID\", \"permission_level\": \"CAN_USE\"}]}" \
  --profile DEFAULT_azure
```

---

## 📊 **Permission Levels Explained**

| Resource | Permission | What It Allows |
|----------|------------|----------------|
| **Catalog** | `USE_CATALOG` | Access the catalog |
| **Schema** | `USE_SCHEMA` | Access the schema |
| **Schema** | `SELECT` | Query tables in the schema |
| **Warehouse** | `CAN_USE` | Execute queries on the warehouse |

---

## 🔴 **Common Issues**

### **Problem: "Database connection error"**
**Symptom**: App loads but shows database connection error

**Solution**: Grant permissions
```bash
./grant_permissions.sh dev
```

---

### **Problem: "App not found"**
**Symptom**: Script says "Could not get app information"

**Solution**: Make sure app is deployed
```bash
# Check if app exists
databricks apps list --profile DEFAULT_azure | grep frauddetection

# If not listed, deploy first
databricks bundle deploy --target dev --profile DEFAULT_azure
```

---

### **Problem: "Service principal ID not found"**
**Symptom**: Script can't find the service principal

**Solution**: Wait for app to fully initialize
```bash
# Wait 30 seconds after deployment
sleep 30

# Then try again
./grant_permissions.sh dev
```

---

## 🎯 **Verification**

### **Check if permissions were granted**:

```bash
# Check catalog permissions
databricks grants get catalog fraud_detection_dev --profile DEFAULT_azure

# Check schema permissions
databricks grants get schema fraud_detection_dev.claims_analysis --profile DEFAULT_azure

# Check warehouse permissions
databricks permissions get sql/warehouses/<WAREHOUSE_ID> --profile DEFAULT_azure
```

---

## 🔄 **When to Re-Grant Permissions**

You need to grant permissions again when:
1. ✅ **New app deployment** - Always after deploying a new app
2. ✅ **App redeployment** - If the service principal changes
3. ✅ **New environment** - When deploying to staging/prod for the first time
4. ❌ **Code changes** - Not needed for code-only updates
5. ❌ **Data changes** - Not needed when just updating data

---

## 📝 **Checklist**

After deploying a new app:

- [ ] App is deployed: `databricks apps get frauddetection_dev`
- [ ] Run permission script: `./grant_permissions.sh dev`
- [ ] Script shows "✅ ALL PERMISSIONS GRANTED"
- [ ] Test app URL in browser
- [ ] App shows no database connection errors

---

## 🎓 **Best Practices**

1. **Always grant after deployment** - Make it part of your deploy process
2. **Use the script** - Automated is better than manual
3. **Check the logs** - If app fails, check logs first
4. **Document custom permissions** - If you need extra permissions, document them

---

## 🚀 **Automated Deployment** (Recommended)

The `deploy_with_config.sh` script automatically grants permissions:

```bash
./deploy_with_config.sh dev
```

This script:
1. ✅ Generates app.yaml
2. ✅ Deploys infrastructure
3. ✅ **Automatically grants permissions** ← Done for you!
4. ✅ Shows next steps

**Use this for zero-manual-steps deployment!**

---

## 📞 **Quick Reference**

```bash
# Grant permissions (after app deployment)
./grant_permissions.sh [dev|staging|prod]

# Check app status
databricks apps get frauddetection_dev --profile DEFAULT_azure

# Check permissions
databricks grants get catalog fraud_detection_dev --profile DEFAULT_azure

# Full automated deploy (includes permissions)
./deploy_with_config.sh dev
```

---

## 🎉 Summary

**The Problem**: Apps need permissions to access data

**The Solution**: Run `./grant_permissions.sh dev` after deployment

**The Automation**: Use `./deploy_with_config.sh dev` for everything

**Remember**: No permissions = Database connection error ❌  
**With permissions**: App works perfectly ✅

---

**See MY_ENVIRONMENT.md for the standard pattern this follows!**

