# Databricks notebook source
# MAGIC %md
# MAGIC # UC Function: fraud_generate_explanation
# MAGIC
# MAGIC Generates human-readable explanations for healthcare fraud decisions for payer adjudicators.
# MAGIC All configuration from config.yaml.

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

spark.sql(f"DROP FUNCTION IF EXISTS {cfg.catalog}.{cfg.schema}.fraud_generate_explanation")
print("Dropped existing function (if any)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create UC Function

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {cfg.catalog}.{cfg.schema}.fraud_generate_explanation(
  claim_text STRING,
  is_fraudulent BOOLEAN,
  fraud_type STRING
)
RETURNS STRUCT<
  explanation: STRING,
  evidence: ARRAY<STRING>,
  recommendations: ARRAY<STRING>
>
COMMENT 'Generates human-readable explanations for healthcare fraud detection decisions for payers'
RETURN 
  FROM_JSON(
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(
      AI_QUERY(
        'databricks-claude-sonnet-4-5',
        CONCAT(
          'Explain this fraud decision for a healthcare payer claims adjuster.\\n\\n',
          'CLAIM: ', claim_text, '\\n',
          'DECISION: ', IF(is_fraudulent, 'FRAUDULENT', 'LEGITIMATE'), '\\n',
          'FRAUD TYPE: ', fraud_type, '\\n\\n',
          'Return ONLY JSON: {{"explanation": "summary text", "evidence": ["fact1", "fact2"], "recommendations": ["action1", "action2"]}}\\n\\n',
          'Return ONLY the JSON object.'
        )
      ), '```json', ''), '```', '')),
    'STRUCT<explanation:STRING,evidence:ARRAY<STRING>,recommendations:ARRAY<STRING>>'
  )
""")

print(f"✅ Function created: {cfg.catalog}.{cfg.schema}.fraud_generate_explanation")
print(f"✅ Includes markdown stripping (removes ```json and ``` wrappers)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debug: Test AI_QUERY Directly (using SQL)

# COMMAND ----------

# Debug - see raw AI_QUERY response
debug_result = spark.sql("""
SELECT AI_QUERY(
  'databricks-claude-sonnet-4-5',
  'Explain this fraud decision for a healthcare payer claims adjuster.

CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month.
DECISION: FRAUDULENT
FRAUD TYPE: Upcoding

Return ONLY JSON: {"explanation": "summary text", "evidence": ["fact1", "fact2"], "recommendations": ["action1", "action2"]}

Return ONLY the JSON object.'
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
SELECT {cfg.catalog}.{cfg.schema}.fraud_generate_explanation(
  'Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150.',
  TRUE,
  'Upcoding'
) as explanation
""").collect()[0]

print("Test Result:")
print(f"  Explanation: {test_result['explanation']['explanation']}")
print(f"  Evidence: {test_result['explanation']['evidence']}")
print(f"  Recommendations: {test_result['explanation']['recommendations']}")

# COMMAND ----------

print("=" * 80)
print("UC FUNCTION CREATED SUCCESSFULLY!")
print("=" * 80)
print(f"✅ Function: {cfg.catalog}.{cfg.schema}.fraud_generate_explanation")
print("=" * 80)

# COMMAND ----------

print("\n✅ All 3 UC AI Functions created!")
print(f"   - {cfg.catalog}.{cfg.schema}.fraud_classify")
print(f"   - {cfg.catalog}.{cfg.schema}.fraud_extract_indicators")
print(f"   - {cfg.catalog}.{cfg.schema}.fraud_generate_explanation")

