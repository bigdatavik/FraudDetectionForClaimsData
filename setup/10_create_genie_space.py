# Databricks notebook source
# MAGIC %md
# MAGIC # Create Genie Space via API
# MAGIC
# MAGIC Creates Genie Space programmatically using Databricks Genie API.
# MAGIC All configuration from config.yaml.
# MAGIC
# MAGIC Reference: https://docs.databricks.com/api/workspace/genie/createspace

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config, print_config

from databricks.sdk import WorkspaceClient
import json
import uuid

cfg = get_config()
print_config(cfg)

w = WorkspaceClient()

print(f"Using workspace: {cfg.workspace_host}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check for Existing Genie Space

# COMMAND ----------

print("Checking for existing Genie spaces...")

try:
    # List spaces using WorkspaceClient API
    response = w.api_client.do(
        'GET',
        '/api/2.0/genie/spaces'
    )
    existing_spaces = response.get('spaces', [])
    
    # Look for space with matching title and DELETE it
    for space in existing_spaces:
        if space.get('title') == cfg.genie_display_name:
            old_space_id = space.get('space_id')
            print(f"🗑️  Found existing space: {old_space_id}")
            print(f"   Title: {space.get('title')}")
            print(f"   Deleting to create fresh...")
            
            # Delete the existing space using Trash API
            try:
                w.api_client.do(
                    'DELETE',
                    f'/api/2.0/genie/spaces/{old_space_id}'
                )
                print(f"✅ Deleted existing space: {old_space_id}")
            except Exception as delete_error:
                print(f"⚠️  Could not delete space: {delete_error}")
                print(f"   You may need to manually delete it from the UI")
    
    print("✅ Ready to create new Genie space")
        
except Exception as e:
    print(f"Error checking/deleting spaces: {e}")
    print("Will proceed with creation...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Fresh Genie Space

# COMMAND ----------

print(f"Creating new Genie Space: {cfg.genie_display_name}")

try:
    # Create minimal serialized space configuration
    # Point to fraud_claims_complete view (claims + fraud analysis)
    serialized_space = {
        "version": 1,
        "config": {
            "sample_questions": [
                {
                    "id": str(uuid.uuid4()).replace('-', ''),  # UUID without hyphens
                    "question": ["Show me all fraudulent claims"]
                },
                {
                    "id": str(uuid.uuid4()).replace('-', ''),  # UUID without hyphens
                    "question": ["What is the fraud rate by claim type?"]
                },
                {
                    "id": str(uuid.uuid4()).replace('-', ''),  # UUID without hyphens
                    "question": ["Which providers have the most fraud cases?"]
                }
            ],
            "instructions": "This space analyzes fraud detection results. All claims have been analyzed by AI fraud detection functions. Use ai_detected_fraud=TRUE to find fraud cases. Risk scores range from 0-1."
        },
        "data_sources": {
            "tables": [
                {"identifier": f"{cfg.catalog}.{cfg.schema}.fraud_claims_complete"}
            ]
        }
    }
    
    # Create space using WorkspaceClient API
    payload = {
        "title": cfg.genie_display_name,
        "description": cfg.genie_description,
        "warehouse_id": cfg.warehouse_id,
        "serialized_space": json.dumps(serialized_space)
    }
    
    response = w.api_client.do(
        'POST',
        '/api/2.0/genie/spaces',
        body=payload
    )
    
    GENIE_SPACE_ID = response.get('space_id')
    print(f"✅ Genie Space created: {GENIE_SPACE_ID}")
    print(f"   Title: {cfg.genie_display_name}")
    
except Exception as e:
    print(f"❌ Error creating space: {e}")
    raise e

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configure Genie Space

# COMMAND ----------

print(f"Configuring Genie Space {GENIE_SPACE_ID}...")

try:
    # Update space with warehouse using WorkspaceClient API
    payload = {
        "title": cfg.genie_display_name,
        "description": cfg.genie_description,
        "warehouse_id": cfg.warehouse_id
    }
    
    response = w.api_client.do(
        'PATCH',
        f'/api/2.0/genie/spaces/{GENIE_SPACE_ID}',
        body=payload
    )
    
    print(f"✅ Space configured with SQL Warehouse: {cfg.warehouse_id}")
    
except Exception as e:
    print(f"⚠️  Could not update space config: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Genie Space ID to Config Table

# COMMAND ----------

# Create config table if it doesn't exist
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {cfg.config_table} (
  config_key STRING NOT NULL,
  config_value STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  CONSTRAINT config_pk PRIMARY KEY(config_key)
)
USING DELTA
COMMENT 'Configuration values for fraud detection system'
""")

# Save Genie Space ID
spark.sql(f"""
MERGE INTO {cfg.config_table} t
USING (
  SELECT 
    'genie_space_id' as config_key,
    '{GENIE_SPACE_ID}' as config_value,
    current_timestamp() as updated_at
) s
ON t.config_key = s.config_key
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

print(f"✅ Genie Space ID saved to {cfg.config_table}")

# Verify
saved_id = spark.sql(f"""
SELECT config_value 
FROM {cfg.config_table} 
WHERE config_key = 'genie_space_id'
""").collect()[0][0]

print(f"   Verified saved ID: {saved_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Genie Space Instructions

# COMMAND ----------

instructions = f"""
# Fraud Detection Analytics - Data Guide

## Available Data

**Main Table:** {cfg.claims_table}

## Schema
- **claim_id**: Unique claim identifier (STRING)
- **claim_amount**: Dollar amount of claim (DOUBLE)
- **claim_date**: When claim was filed (TIMESTAMP)
- **claim_type**: Type of insurance (Medical, Auto, Property, Life, Dental, Vision)
- **claimant_info**: Claimant details (MAP<STRING, STRING>)
- **provider_info**: Provider details (MAP<STRING, STRING>)
- **diagnosis_codes**: Medical diagnosis codes (ARRAY<STRING>)
- **treatment_description**: Description of treatment (STRING)
- **claim_text**: Full claim narrative (STRING)
- **is_fraud**: Whether claim is fraudulent - ground truth (BOOLEAN)
- **fraud_type**: Type of fraud if applicable (STRING)
- **fraud_indicators**: List of red flags (ARRAY<STRING>)

## Common Queries

### Fraud Statistics
- "What percentage of claims are fraudulent?"
- "Show fraud rate by claim type"
- "What's the average fraudulent claim amount?"
- "How many fraud cases were detected this month?"

### Trend Analysis
- "Show fraud patterns over last 6 months"
- "Which claim types have highest fraud rates?"
- "Trend of fraud detection over time"
- "Monthly fraud amounts by type"

### Provider Analysis
- "Which providers have most fraud cases?"
- "Show provider fraud rates"
- "List top 10 providers by fraud claims"
- "Providers with unusual claim patterns"

### Pattern Detection
- "Show common fraud indicators"
- "What fraud types are most common?"
- "Claims with multiple red flags"
- "High-value fraud cases"

### Amount Analysis
- "Average claim amount by type"
- "Claims over $50,000"
- "Distribution of claim amounts"
- "Fraud vs legitimate claim amounts"

## SQL Tips
- Use `WHERE is_fraud = TRUE` for confirmed fraud
- Filter by `claim_type` for category analysis
- Use date functions on `claim_date` for time series
- Array functions for `fraud_indicators` analysis
- Map access: `claimant_info['location']` for nested data

## Example Queries

```sql
-- Fraud rate by claim type
SELECT 
  claim_type,
  COUNT(*) as total_claims,
  SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_claims,
  ROUND(100.0 * SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) / COUNT(*), 2) as fraud_rate_pct
FROM {cfg.claims_table}
GROUP BY claim_type
ORDER BY fraud_rate_pct DESC;

-- High-value fraud cases
SELECT claim_id, claim_type, claim_amount, fraud_type, claim_text
FROM {cfg.claims_table}
WHERE is_fraud = TRUE AND claim_amount > 30000
ORDER BY claim_amount DESC
LIMIT 10;
```
"""

print("=" * 80)
print("GENIE SPACE INSTRUCTIONS")
print("=" * 80)
print(instructions)
print("=" * 80)
print("\n💡 TIP: You can add these instructions to the Genie Space via the UI")
print(f"   Open: {cfg.workspace_host}/#genie/{GENIE_SPACE_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

print("=" * 80)
print("GENIE SPACE SETUP COMPLETE!")
print("=" * 80)
print(f"✅ Space ID:       {GENIE_SPACE_ID}")
print(f"✅ Title:          {cfg.genie_display_name}")
print(f"✅ Warehouse ID:   {cfg.warehouse_id}")
print(f"✅ Source Table:   {cfg.claims_table}")
print(f"✅ Saved to:       {cfg.config_table}")
print("=" * 80)
print("\nNext steps:")
print(f"1. Open Genie Space: {cfg.workspace_host}/#genie/{GENIE_SPACE_ID}")
print(f"2. Test queries against {cfg.claims_table}")
print(f"3. Agent will read GENIE_SPACE_ID from {cfg.config_table}")
print("=" * 80)

# Store as output for downstream tasks
try:
    dbutils.jobs.taskValues.set("genie_space_id", GENIE_SPACE_ID)
    print(f"\n✅ Set task value: genie_space_id = {GENIE_SPACE_ID}")
except:
    pass


