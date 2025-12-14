# Databricks notebook source
# MAGIC %md
# MAGIC # Create Fraud Analysis Results Table
# MAGIC
# MAGIC Creates table to store fraud detection results from UC functions.
# MAGIC This table will be populated by batch analysis and queried by Genie.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

cfg = get_config()
print(f"Creating fraud analysis table in: {cfg.catalog}.{cfg.schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Drop Existing Table (if needed)

# COMMAND ----------

# Drop table if exists (for clean deployment)
spark.sql(f"DROP TABLE IF EXISTS {cfg.catalog}.{cfg.schema}.fraud_analysis")
print("✅ Dropped existing fraud_analysis table (if any)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Fraud Analysis Table

# COMMAND ----------

spark.sql(f"""
CREATE TABLE {cfg.catalog}.{cfg.schema}.fraud_analysis (
    -- Claim reference
    claim_id STRING NOT NULL,
    analysis_timestamp TIMESTAMP NOT NULL,
    
    -- From fraud_classify function
    is_fraudulent BOOLEAN,
    fraud_probability DOUBLE,
    fraud_type STRING,
    classification_confidence DOUBLE,
    
    -- From fraud_extract_indicators function
    red_flags ARRAY<STRING>,
    suspicious_patterns ARRAY<STRING>,
    risk_score DOUBLE,
    affected_entities ARRAY<STRING>,
    
    -- From fraud_generate_explanation function
    explanation STRING,
    evidence ARRAY<STRING>,
    recommendations ARRAY<STRING>
)
USING DELTA
COMMENT 'Fraud detection analysis results for all claims'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")

print(f"✅ Created fraud_analysis table: {cfg.catalog}.{cfg.schema}.fraud_analysis")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Unified View

# COMMAND ----------

# Create view that joins claims with fraud analysis
spark.sql(f"""
CREATE OR REPLACE VIEW {cfg.catalog}.{cfg.schema}.fraud_claims_complete AS
SELECT 
    -- Claim data (explicit columns to avoid conflicts)
    c.claim_id,
    c.claim_date,
    c.claim_type,
    c.claim_amount,
    c.provider_info,
    c.claimant_info,
    c.diagnosis_codes,
    c.treatment_description,
    c.claim_text,
    c.is_fraud as ground_truth_is_fraud,
    c.fraud_type as ground_truth_fraud_type,
    c.fraud_indicators as ground_truth_indicators,
    
    -- Fraud analysis results (from UC AI functions)
    f.analysis_timestamp,
    f.is_fraudulent as ai_detected_fraud,
    f.fraud_probability,
    f.fraud_type as ai_detected_fraud_type,
    f.classification_confidence,
    f.red_flags,
    f.suspicious_patterns,
    f.risk_score,
    f.affected_entities,
    f.explanation,
    f.evidence,
    f.recommendations
FROM {cfg.catalog}.{cfg.schema}.claims_data c
LEFT JOIN {cfg.catalog}.{cfg.schema}.fraud_analysis f 
    ON c.claim_id = f.claim_id
""")

print(f"✅ Created unified view: {cfg.catalog}.{cfg.schema}.fraud_claims_complete")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Show Table Schema

# COMMAND ----------

print("=" * 80)
print("FRAUD ANALYSIS TABLE SCHEMA")
print("=" * 80)
display(spark.sql(f"DESCRIBE {cfg.catalog}.{cfg.schema}.fraud_analysis"))

# COMMAND ----------

print("=" * 80)
print("FRAUD ANALYSIS TABLE CREATED!")
print("=" * 80)
print(f"✅ Table: {cfg.catalog}.{cfg.schema}.fraud_analysis")
print(f"✅ View:  {cfg.catalog}.{cfg.schema}.fraud_claims_complete")
print(f"✅ Change Data Feed: ENABLED")
print("=" * 80)
print("\n📝 Next step: Run 09_batch_analyze_claims.py to populate with fraud analysis results")
print("=" * 80)


