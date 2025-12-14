# Databricks notebook source
# MAGIC %md
# MAGIC # UC Function: fraud_extract_indicators
# MAGIC
# MAGIC Extracts specific healthcare fraud indicators and red flags from claims for payers.

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

spark.sql(f"DROP FUNCTION IF EXISTS {cfg.catalog}.{cfg.schema}.fraud_extract_indicators")
print("✅ Dropped existing function (if any)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create UC Function (with Markdown Stripping)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {cfg.catalog}.{cfg.schema}.fraud_extract_indicators(claim_text STRING)
RETURNS STRUCT<
  red_flags: ARRAY<STRING>,
  suspicious_patterns: ARRAY<STRING>,
  risk_score: DOUBLE,
  affected_entities: ARRAY<STRING>
>
COMMENT 'Extracts healthcare fraud indicators and red flags from claims for payers'
RETURN 
  FROM_JSON(
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(
      AI_QUERY(
        'databricks-claude-sonnet-4-5',
        CONCAT(
          'You are a healthcare fraud detection AI. Return ONLY a JSON object.\\n\\n',
          'CLAIM: ', claim_text, '\\n\\n',
          'Return this JSON: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
          'Return ONLY the JSON object, no other text.'
        )
      ), '```json', ''), '```', '')),
    'STRUCT<red_flags:ARRAY<STRING>,suspicious_patterns:ARRAY<STRING>,risk_score:DOUBLE,affected_entities:ARRAY<STRING>>'
  )
""")

print(f"✅ Function created: {cfg.catalog}.{cfg.schema}.fraud_extract_indicators")
print(f"✅ Includes markdown stripping (removes ```json and ``` wrappers)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debug: Test AI_QUERY Directly (using SQL)

# COMMAND ----------

# Debug - see raw AI_QUERY response
debug_result = spark.sql("""
SELECT AI_QUERY(
  'databricks-claude-sonnet-4-5',
  'You are a healthcare fraud detection AI. Return ONLY a JSON object.

CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150.

Return this JSON: {"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}

Return ONLY the JSON object, no other text.'
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

test_result = spark.sql(f"""
SELECT {cfg.catalog}.{cfg.schema}.fraud_extract_indicators(
  'Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150 for actual service rendered.'
) as indicators
""").collect()[0]

print("Test Result:")
print("=" * 70)
indicators = test_result['indicators']
if indicators and indicators['red_flags'] is not None:
    print(f"  ✅ Red Flags: {indicators['red_flags']}")
    print(f"  ✅ Suspicious Patterns: {indicators['suspicious_patterns']}")
    risk_score = indicators['risk_score']
    if risk_score is not None:
        print(f"  ✅ Risk Score: {risk_score:.2f}")
    else:
        print(f"  ⚠️  Risk Score: None")
    print(f"  ✅ Affected Entities: {indicators['affected_entities']}")
else:
    print("  ❌ Function returned None - FROM_JSON failed to parse the response")
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("=" * 80)
print("✅ UC FUNCTION CREATED SUCCESSFULLY!")
print("=" * 80)
print(f"Function: {cfg.catalog}.{cfg.schema}.fraud_extract_indicators")
print(f"LLM: {cfg.llm_endpoint}")
print(f"Returns: red_flags, suspicious_patterns, risk_score, affected_entities")
print("=" * 80)
