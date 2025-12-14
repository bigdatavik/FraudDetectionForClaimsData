# Python UDF approach to strip markdown properly

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

cfg = get_config()

# First, create a Python UDF to clean the response
spark.sql(f"DROP FUNCTION IF EXISTS {cfg.catalog}.{cfg.schema}.strip_markdown")

spark.sql(f"""
CREATE OR REPLACE FUNCTION {cfg.catalog}.{cfg.schema}.strip_markdown(text STRING)
RETURNS STRING
LANGUAGE PYTHON
AS $$
  import re
  # Remove markdown code fences
  text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
  text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
  # Remove any leading/trailing whitespace
  text = text.strip()
  return text
$$
""")

print("✅ Created strip_markdown UDF")

# Now create the fraud_extract_indicators function using the UDF
spark.sql(f"DROP FUNCTION IF EXISTS {cfg.catalog}.{cfg.schema}.fraud_extract_indicators")

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
    {cfg.catalog}.{cfg.schema}.strip_markdown(
      AI_QUERY(
        'databricks-claude-sonnet-4',
        CONCAT(
          'You are a healthcare fraud investigator. Extract fraud indicators from this claim.\\n\\n',
          'CLAIM: ', claim_text, '\\n\\n',
          'Return ONLY the raw JSON object.\\n\\n',
          'Format: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
          'Return ONLY the raw JSON object.'
        )
      )
    ),
    'STRUCT<red_flags:ARRAY<STRING>,suspicious_patterns:ARRAY<STRING>,risk_score:DOUBLE,affected_entities:ARRAY<STRING>>'
  )
""")

print("✅ Function updated to use Python UDF for markdown stripping!")

