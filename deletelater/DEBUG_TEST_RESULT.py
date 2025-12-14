# Databricks notebook source
# MAGIC %md
# MAGIC # Debug: What is test_result Actually Returning?

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

cfg = get_config()
print(f"Using: {cfg.catalog}.{cfg.schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: What does the function return?

# COMMAND ----------

test_result = spark.sql(f"""
SELECT {cfg.catalog}.{cfg.schema}.fraud_extract_indicators(
  'Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150 for actual service rendered.'
) as indicators
""").collect()[0]

print("=" * 70)
print("STEP 1: What is test_result?")
print("=" * 70)
print(f"Type: {type(test_result)}")
print(f"test_result: {test_result}")
print()
print("=" * 70)
print("STEP 2: What is test_result['indicators']?")
print("=" * 70)
indicators = test_result['indicators']
print(f"Type: {type(indicators)}")
print(f"Value: {indicators}")
print()
print("=" * 70)
print("STEP 3: Individual fields")
print("=" * 70)
if indicators:
    print(f"red_flags: {indicators['red_flags']} (type: {type(indicators['red_flags'])})")
    print(f"suspicious_patterns: {indicators['suspicious_patterns']} (type: {type(indicators['suspicious_patterns'])})")
    print(f"risk_score: {indicators['risk_score']} (type: {type(indicators['risk_score'])})")
    print(f"affected_entities: {indicators['affected_entities']} (type: {type(indicators['affected_entities'])})")
else:
    print("indicators is None or empty!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: What is Claude actually returning? (Raw AI_QUERY)

# COMMAND ----------

raw_response = spark.sql(f"""
SELECT AI_QUERY(
  'databricks-claude-sonnet-4',
  CONCAT(
    'You are a healthcare fraud investigator. Extract fraud indicators from this claim.\\n\\n',
    'CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150 for actual service rendered.\\n\\n',
    'Return ONLY JSON: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
    'Return ONLY the JSON object.'
  )
) as response
""").collect()[0]

print("=" * 70)
print("RAW CLAUDE RESPONSE:")
print("=" * 70)
print(raw_response.response)
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Can FROM_JSON parse it?

# COMMAND ----------

# Try to parse what Claude returned
try:
    parsed = spark.sql(f"""
    SELECT FROM_JSON(
      '''{raw_response.response}''',
      'STRUCT<red_flags:ARRAY<STRING>,suspicious_patterns:ARRAY<STRING>,risk_score:DOUBLE,affected_entities:ARRAY<STRING>>'
    ) as parsed_result
    """).collect()[0]
    
    print("=" * 70)
    print("FROM_JSON RESULT:")
    print("=" * 70)
    print(f"Parsed result: {parsed.parsed_result}")
    print()
    if parsed.parsed_result:
        print("✅ FROM_JSON successfully parsed the response!")
        print(f"  red_flags: {parsed.parsed_result['red_flags']}")
        print(f"  risk_score: {parsed.parsed_result['risk_score']}")
    else:
        print("❌ FROM_JSON returned None - couldn't parse the response")
except Exception as e:
    print(f"❌ Error trying to parse: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Test with hardcoded valid JSON

# COMMAND ----------

# Test if FROM_JSON works with perfect JSON
hardcoded_test = spark.sql("""
SELECT FROM_JSON(
  '{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}',
  'STRUCT<red_flags:ARRAY<STRING>,suspicious_patterns:ARRAY<STRING>,risk_score:DOUBLE,affected_entities:ARRAY<STRING>>'
) as test_result
""").collect()[0]

print("=" * 70)
print("HARDCODED JSON TEST:")
print("=" * 70)
print(f"Result: {hardcoded_test.test_result}")
if hardcoded_test.test_result:
    print("✅ FROM_JSON CAN parse valid JSON!")
else:
    print("❌ FROM_JSON failed even with valid JSON - schema mismatch?")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Diagnosis
# MAGIC
# MAGIC Based on the output above:
# MAGIC
# MAGIC 1. If **raw_response** shows valid JSON but **FROM_JSON** returns None → Schema mismatch or JSON format issue
# MAGIC 2. If **raw_response** has extra text (not pure JSON) → Prompt issue, Claude adding explanation
# MAGIC 3. If **hardcoded test** fails → Schema definition problem
# MAGIC 4. If **hardcoded test** works but function fails → The function definition in UC needs to be updated

