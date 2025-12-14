# Debug Resolution: FROM_JSON Parsing Issue

## Problem Summary

The `fraud_extract_indicators` UC function was returning `None` for all fields, causing the test function to fail with:
```
TypeError: unsupported format string passed to NoneType.__format__
```

## Root Cause

**The prompt was too abbreviated and unclear**, causing Claude to return text that wasn't pure JSON. The function definition used:

```sql
'Return ONLY valid JSON with NO extra text. CLAIM: ', claim_text, 
' JSON format: {"red_flags": ["flag1"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}} Return ONLY the JSON.'
```

This concatenated prompt was confusing and didn't give Claude enough context about its role.

## Why Debug Query Worked

The debug query in cell 9 used a **much better prompt**:
```sql
'You are a healthcare fraud investigator. Extract fraud indicators from this claim.

CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150.

Return ONLY JSON: {"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}

Return ONLY the JSON object.'
```

This gave Claude:
1. **Role context** ("You are a healthcare fraud investigator")
2. **Clear separation** with newlines
3. **Explicit task** ("Extract fraud indicators")
4. **Clear example** of expected format

## The Fix

### 1. Updated the Function Prompt

Changed the function definition to match the debug query's structure:

```sql
CONCAT(
  'You are a healthcare fraud investigator. Extract fraud indicators from this claim.\\n\\n',
  'CLAIM: ', claim_text, '\\n\\n',
  'Return ONLY JSON: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
  'Return ONLY the JSON object.'
)
```

### 2. Added Error Handling in Test

Updated the test code to handle `None` values gracefully:

```python
indicators = test_result['indicators']
if indicators:
    print(f"  Red Flags: {indicators['red_flags']}")
    print(f"  Suspicious Patterns: {indicators['suspicious_patterns']}")
    risk_score = indicators['risk_score']
    if risk_score is not None:
        print(f"  Risk Score: {risk_score:.2f}")
    else:
        print(f"  Risk Score: None")
    print(f"  Affected Entities: {indicators['affected_entities']}")
else:
    print("  ❌ Function returned None - FROM_JSON likely failed to parse the response")
```

## Key Lessons

1. **LLM prompts need context**: Even when asking for "just JSON", provide role context
2. **Use newlines liberally**: Helps the LLM parse the request structure
3. **Match debug to production**: When debug works, use the EXACT same prompt pattern
4. **FROM_JSON silently fails**: When it can't parse, it returns None for all fields - no error!
5. **Always check for None**: Before using `.format()` or accessing nested fields

## Testing the Fix

To verify the fix works:

1. Re-run the notebook `setup/04_uc_fraud_extract.py`
2. The debug query (cell 9) should still work ✅
3. The test function (cell 14) should now also work ✅
4. Both should show the same structure of output

## Expected Output After Fix

```
Test Result:
  Red Flags: ['CPT code 99215 billed for routine check-up when complex visit code not supported by documentation', 'Claim amount $450 significantly exceeds typical $150 for actual service provided']
  Suspicious Patterns: ['Provider has 4 similar upcoding incidents within single month indicating systematic fraud pattern']
  Risk Score: 0.85
  Affected Entities: ['Provider', 'CPT code 99215', 'Medical documentation']
```

