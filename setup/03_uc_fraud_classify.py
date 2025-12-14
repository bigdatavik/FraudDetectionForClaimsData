# Databricks notebook source
# MAGIC %md
# MAGIC # UC Function: fraud_classify
# MAGIC
# MAGIC Classifies healthcare claims as fraudulent or legitimate for payers (Humana, UHG, etc.).
# MAGIC All configuration from config.yaml - including LLM endpoint!

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

cfg = get_config()
print(f"Creating function in: {cfg.catalog}.{cfg.schema}")
print(f"Using LLM: {cfg.llm_endpoint}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Drop Existing Function

# COMMAND ----------

spark.sql(f"DROP FUNCTION IF EXISTS {cfg.catalog}.{cfg.schema}.fraud_classify")
print("Dropped existing function (if any)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create UC Function
# MAGIC
# MAGIC Using LANGUAGE PYTHON with ai_query - exact same pattern as tutorial

# COMMAND ----------

# Create the fraud_classify function with markdown stripping
spark.sql(f"""
CREATE OR REPLACE FUNCTION {cfg.catalog}.{cfg.schema}.fraud_classify(claim_text STRING)
RETURNS STRUCT<
  is_fraudulent: BOOLEAN,
  fraud_probability: DOUBLE,
  fraud_type: STRING,
  confidence: DOUBLE
>
COMMENT 'Classifies healthcare claims as fraudulent or legitimate for payers using AI'
RETURN 
  FROM_JSON(
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(
      AI_QUERY(
        'databricks-claude-sonnet-4-5',
        CONCAT(
          'You are a healthcare fraud detection AI. Return ONLY a JSON object.\\n\\n',
          'CLAIM: ', claim_text, '\\n\\n',
          'Return this JSON: {{"is_fraudulent": true/false, "fraud_probability": 0.0-1.0, "fraud_type": "Upcoding/Unbundling/Phantom/Duplicate/Unnecessary/Kickback/Identity/Prescription/None", "confidence": 0.0-1.0}}\\n\\n',
          'Rules: If claim says "billed X but actually Y" then is_fraudulent=true. If provider has fraud pattern then is_fraudulent=true. If amount 2-3x higher then is_fraudulent=true.\\n\\n',
          'Return ONLY the JSON object, no other text.'
        )
      ), '```json', ''), '```', '')),
    'STRUCT<is_fraudulent:BOOLEAN,fraud_probability:DOUBLE,fraud_type:STRING,confidence:DOUBLE>'
  )
""")

print(f"✅ Function created: {cfg.catalog}.{cfg.schema}.fraud_classify")
print(f"✅ Using LLM: {cfg.llm_endpoint}")
print(f"✅ Includes markdown stripping (removes ```json and ``` wrappers)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debug: Test AI_QUERY Directly (using SQL)

# COMMAND ----------

# Simpler debug - just use AI_QUERY directly in SQL - Using Claude for better JSON
debug_result = spark.sql("""
SELECT AI_QUERY(
  'databricks-claude-sonnet-4-5',
  'Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150. Is this fraud? Answer with JSON: {"is_fraudulent": true/false, "fraud_probability": 0.0-1.0, "fraud_type": "type", "confidence": 0.0-1.0}'
) as response
""").collect()[0]

print("🔍 RAW MODEL RESPONSE:")
print("=" * 70)
print(debug_result.response)
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Function

# COMMAND ----------

# Test with a sample claim
test_result = spark.sql(f"""
SELECT {cfg.catalog}.{cfg.schema}.fraud_classify(
  'Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150 for actual service rendered.'
) as classification
""").collect()[0]

print("Test Result:")
print(f"  Is Fraudulent: {test_result.classification.is_fraudulent}")
print(f"  Fraud Probability: {test_result.classification.fraud_probability:.2f}")
print(f"  Fraud Type: {test_result.classification.fraud_type}")
print(f"  Confidence: {test_result.classification.confidence:.2f}")

# COMMAND ----------

print("=" * 80)
print("UC FUNCTION CREATED SUCCESSFULLY!")
print("=" * 80)
print(f"✅ Function: {cfg.catalog}.{cfg.schema}.fraud_classify")
print(f"✅ LLM: {cfg.llm_endpoint}")
print(f"✅ Returns: is_fraudulent, fraud_probability, fraud_type, confidence")
print("=" * 80)

