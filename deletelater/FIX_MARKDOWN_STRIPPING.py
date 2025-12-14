# Quick fix: Strip markdown before FROM_JSON

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

cfg = get_config()

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
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        AI_QUERY(
          'databricks-claude-sonnet-4',
          CONCAT(
            'You are a healthcare fraud investigator. Extract fraud indicators from this claim.\\n\\n',
            'CLAIM: ', claim_text, '\\n\\n',
            'Return ONLY the raw JSON object. DO NOT wrap in markdown. DO NOT use code fences.\\n\\n',
            'Format: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
            'Return ONLY the raw JSON object.'
          )
        ),
        '^```json\\\\s*',
        ''
      ),
      '```\\\\s*$',
      ''
    ),
    'STRUCT<red_flags:ARRAY<STRING>,suspicious_patterns:ARRAY<STRING>,risk_score:DOUBLE,affected_entities:ARRAY<STRING>>'
  )
""")

print("✅ Function updated with markdown stripping!")
print("✅ Now it will remove ```json and ``` wrappers before parsing")

