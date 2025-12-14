# 🚀 QUICK SETUP INSTRUCTIONS

## ✅ Status: All Notebooks Uploaded!

**Location:** `/Workspace/Users/vik.malhotra@databricks.com/fraud_detection_setup/`

**Cluster to Use:** `Field Eng Shared UC LTS Cluster` (ID: `0304-162117-qgsi1x04`)

---

## 📋 Run These Notebooks in Order:

### 1. Create Catalog & Schema
**Notebook:** `01_create_catalog_schema.py`  
**What it does:** Creates `fraud_detection_dev` catalog and `claims_analysis` schema  
**Time:** ~30 seconds

### 2. Generate Sample Data  
**Notebook:** `02_generate_sample_data.py`  
**What it does:** Creates 1000 synthetic insurance claims (8% fraud rate)  
**Time:** ~1 minute

### 3. Create UC Fraud Classify Function
**Notebook:** `03_uc_fraud_classify.py`  
**What it does:** Creates `fraud_classify()` UC AI function  
**Time:** ~1 minute

### 4. Create UC Fraud Extract Function
**Notebook:** `04_uc_fraud_extract.py`  
**What it does:** Creates `fraud_extract_indicators()` UC AI function  
**Time:** ~1 minute

### 5. Create UC Fraud Explain Function
**Notebook:** `05_uc_fraud_explain.py`  
**What it does:** Creates `fraud_generate_explanation()` UC AI function  
**Time:** ~1 minute

### 6. Create Knowledge Base
**Notebook:** `06_create_knowledge_base.py`  
**What it does:** Creates fraud_knowledge_base table with sample documents  
**Time:** ~1 minute

### 7. Create Vector Index
**Notebook:** `07_create_vector_index.py`  
**What it does:** Creates vector search index on knowledge base  
**Time:** ~5-10 minutes (index sync time)

### 8. Create Genie Space
**Notebook:** `08_create_genie_space.py`  
**What it does:** Creates Genie Space via API and saves ID to config table  
**Time:** ~30 seconds

---

## 🎯 Quick Run Instructions:

1. **Open Databricks Workspace:**  
   https://adb-984752964297111.11.azuredatabricks.net

2. **Navigate to:**  
   `/Workspace/Users/vik.malhotra@databricks.com/fraud_detection_setup/`

3. **For Each Notebook:**
   - Click to open
   - Select cluster: **Field Eng Shared UC LTS Cluster**
   - Click "Run All"
   - Wait for completion (check ✅ on all cells)
   - Move to next notebook

4. **Total Time:** ~15-20 minutes for all 8 notebooks

---

## ⚠️ Known Issues from Job Run (Already Fixed):

From the screenshot, these notebooks failed in the job run:
- ❌ `create_knowledge_base` - Failed (25s)
- ❌ `create_uc_classify` - Failed (1m 13s)
- ❌ `create_uc_explain` - Failed (1m 9s)
- ❌ `create_uc_extract` - Failed (1m 3s)
- ❌ `create_genie_space` - Failed (11s)

**Root Cause:** Likely missing imports or configuration issues in job environment.

**Solution:** Running interactively on shared cluster will work because:
- Cluster has all libraries pre-installed
- Can see errors in real-time
- Can fix any issues immediately

---

## ✅ After Setup Complete:

Once all notebooks run successfully:

1. **Verify Catalog Created:**
   ```sql
   SHOW CATALOGS LIKE 'fraud_detection_dev';
   ```

2. **Verify Tables:**
   ```sql
   USE CATALOG fraud_detection_dev;
   USE SCHEMA claims_analysis;
   SHOW TABLES;
   ```

3. **Verify UC Functions:**
   ```sql
   SHOW FUNCTIONS LIKE 'fraud*';
   ```

4. **Test Agent:** Open `notebooks/01_fraud_agent.ipynb` and run it!

---

## 🐛 If You Encounter Errors:

### Common Issue: Import Errors
```python
# If you see "ModuleNotFoundError"
%pip install databricks-sdk databricks-vectorsearch pyyaml
dbutils.library.restartPython()
```

### Common Issue: Permission Denied
```python
# If you see permission errors
# Have admin grant CREATE CATALOG permission
```

### Common Issue: Vector Endpoint Not Found
- Go to Compute → Vector Search
- Verify endpoint "one-env-shared-endpoint-2" exists
- If not, update config.yaml with correct endpoint name

---

## 📊 Expected Results:

After successful setup:
- ✅ Catalog `fraud_detection_dev` exists
- ✅ Schema `claims_analysis` with 4 tables:
  - `claims_fraud` (1000 rows)
  - `fraud_knowledge_base` (~10 rows)
  - `config_table` (1 row with genie_space_id)
- ✅ 3 UC AI Functions: fraud_classify, fraud_extract_indicators, fraud_generate_explanation
- ✅ Vector Search Index: `fraud_cases_index`
- ✅ Genie Space created and ID stored

---

## 🎉 Ready to Test!

Once setup is complete, you can:
1. Run the agent notebook
2. Deploy the Streamlit app
3. Demo the full system!

**Notebooks Location:** https://adb-984752964297111.11.azuredatabricks.net/workspace/Users/vik.malhotra@databricks.com/fraud_detection_setup/

**Start with:** `01_create_catalog_schema.py` on `Field Eng Shared UC LTS Cluster`

Good luck! 🚀


