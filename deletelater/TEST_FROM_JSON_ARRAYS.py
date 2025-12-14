# Databricks notebook source
# MAGIC %md
# MAGIC # Test FROM_JSON with Arrays - Diagnose the Issue

# COMMAND ----------

# Test 1: Can FROM_JSON parse Claude's response with arrays?
test1 = spark.sql("""
SELECT FROM_JSON(
  AI_QUERY(
    'databricks-claude-sonnet-4',
    'Return this JSON with NO extra text: {"red_flags": ["flag1", "flag2"], "risk_score": 0.9}'
  ),
  'STRUCT<red_flags:ARRAY<STRING>,risk_score:DOUBLE>'
) as result
""").collect()[0]

print("Test 1 - Simple array extraction:")
print(test1.result)
print()

# COMMAND ----------

# Test 2: What does Claude actually return for array requests?
test2 = spark.sql("""
SELECT AI_QUERY(
  'databricks-claude-sonnet-4',
  'Return ONLY this JSON: {"items": ["a", "b", "c"]}'
) as response
""").collect()[0]

print("Test 2 - Raw Claude array response:")
print(test2.response)
print()

# COMMAND ----------

# Test 3: Can we parse that response?
try:
    test3 = spark.sql("""
    SELECT FROM_JSON(
      '{"items": ["a", "b", "c"]}',
      'STRUCT<items:ARRAY<STRING>>'
    ) as result
    """).collect()[0]
    print("Test 3 - FROM_JSON with hardcoded array JSON:")
    print(test3.result)
except Exception as e:
    print(f"Test 3 failed: {e}")

