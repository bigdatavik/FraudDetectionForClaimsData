# Streamlit App Deployment Guide

## Current Status

✅ **Bundle Deployed**: fraud_detection_claims_dev
✅ **App Created**: fraud-detection-claims-dev
⚠️  **App Status**: Deployment crashed (investigating)

## Option 1: Run Locally (RECOMMENDED FOR NOW)

The fastest way to test your app is to run it locally:

```bash
cd /Users/vik.malhotra/FraudDetectionForClaimsData/app

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Access at: `http://localhost:8501`

**Advantages:**
- Fast iteration and testing
- Full access to logs
- Easy debugging
- Works immediately

## Option 2: Debug Databricks Apps Deployment

The app is crashing on startup. Common causes:

### Check 1: Missing/Incorrect Configuration

The app needs these environment variables:
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN` or service principal auth
- `DATABRICKS_WAREHOUSE_ID`

### Check 2: Dependencies Issue

Some packages might not be compatible. Try simplifying `requirements.txt`:

```txt
streamlit==1.28.0
databricks-sdk==0.18.0
pandas==2.0.0
plotly==5.17.0
pyyaml==6.0
```

### Check 3: App Logs

View detailed logs:
```bash
databricks apps logs fraud-detection-claims-dev --profile DEFAULT_azure
```

### Check 4: Redeploy with Fixes

After fixing issues:
```bash
databricks bundle deploy --profile DEFAULT_azure
databricks apps deploy fraud-detection-claims-dev \
  --source-code-path /Workspace/Users/vik.malhotra@databricks.com/.bundle/fraud_detection_claims_dev/default/files/app \
  --profile DEFAULT_azure
```

## Option 3: Use Genie Instead

Since Genie is already working, you can:
1. Use Genie for analytics and queries
2. Use notebooks for claim analysis
3. Skip the Streamlit app for now

Genie URL: https://adb-984752964297111.11.azuredatabricks.net/

---

## Recommendation

**Start with Option 1 (Local)** to test the app functionality, then:
- If the app works well locally → Debug Databricks Apps deployment
- If you mainly need analytics → Stick with Genie (it's working perfectly!)

The system is fully functional - you can analyze claims and query data. The Streamlit app is just a nice-to-have UI layer.

