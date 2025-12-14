# Testing the Fix: Step-by-Step Verification

## Problem Recap
- **Debug query** (cell 9): Returns perfect JSON ✅
- **Test function** (cell 14): Failed with `TypeError: unsupported format string passed to NoneType.__format__` ❌

## Root Cause
The function's prompt was poorly structured, causing Claude to return non-JSON text that `FROM_JSON()` couldn't parse, resulting in `None` values.

## The Fix
Updated the function prompt in `setup/04_uc_fraud_extract.py` to match the debug query's structure.

---

## Verification Steps

### Step 1: Re-run the Setup Notebook

Open and run: `setup/04_uc_fraud_extract.py`

This will:
1. Drop the old function
2. Create the new function with the fixed prompt
3. Run the debug query (should still work)
4. Run the test function (should now work too!)

### Step 2: Expected Output - Debug Query (Cell 9)

You should see something like:

```
🔍 RAW MODEL RESPONSE:
======================================================================
```json
{
  "red_flags": [
    "CPT code 99215 billed for routine check-up when complex visit code not supported by documentation",
    "Claim amount $450 significantly exceeds typical $150 for actual service provided"
  ],
  "suspicious_patterns": [
    "Provider has 4 similar upcoding incidents within single month indicating systematic fraud pattern"
  ],
  "risk_score": 0.85,
  "affected_entities": [
    "Provider",
    "CPT code 99215",
    "Medical documentation"
  ]
}
```
======================================================================
```

### Step 3: Expected Output - Test Function (Cell 14)

**Before Fix** (what you saw):
```
Test Result:
  Red Flags: None
  Suspicious Patterns: None
  
  TypeError: unsupported format string passed to NoneType.__format__
```

**After Fix** (what you should now see):
```
Test Result:
  Red Flags: ['CPT code 99215 billed for routine check-up when complex visit code not supported by documentation', 'Claim amount $450 significantly exceeds typical $150 for actual service provided']
  Suspicious Patterns: ['Provider has 4 similar upcoding incidents within single month indicating systematic fraud pattern']
  Risk Score: 0.85
  Affected Entities: ['Provider', 'CPT code 99215', 'Medical documentation']
```

---

## What Changed

### Before (Broken Prompt):
```sql
CONCAT(
  'Return ONLY valid JSON with NO extra text. CLAIM: ', claim_text, 
  ' JSON format: {{"red_flags": ["flag1"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}} Return ONLY the JSON.'
)
```

### After (Fixed Prompt):
```sql
CONCAT(
  'You are a healthcare fraud investigator. Extract fraud indicators from this claim.\\n\\n',
  'CLAIM: ', claim_text, '\\n\\n',
  'Return ONLY JSON: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
  'Return ONLY the JSON object.'
)
```

### Key Improvements:
1. ✅ Added role context
2. ✅ Used `\\n\\n` for visual separation
3. ✅ Moved claim into labeled section
4. ✅ Showed multiple array items in example
5. ✅ Added final reinforcement line

---

## Additional Testing

### Test with Other Claims

Try the function with different claim texts:

```sql
SELECT {cfg.catalog}.{cfg.schema}.fraud_extract_indicators(
  'Patient received unnecessary MRI scan. Doctor owns the imaging center and refers all patients there regardless of medical need.'
) as indicators
```

Expected structure:
```python
{
  'red_flags': [...list of red flags...],
  'suspicious_patterns': [...list of patterns...],
  'risk_score': 0.XX,  # Number between 0 and 1
  'affected_entities': [...list of entities...]
}
```

### Verify Error Handling

The updated test code now handles `None` gracefully:

```python
if indicators:
    # Process indicators
else:
    print("  ❌ Function returned None - FROM_JSON likely failed to parse the response")
```

This means:
- If the function works: You see results
- If the function fails: You see a clear error message (not a cryptic TypeError)

---

## Success Criteria

✅ **All of these should be true:**

1. Debug query (cell 9) still works
2. Test function (cell 14) now works without TypeError
3. Both outputs show similar JSON structure
4. Risk score is formatted as decimal (e.g., "0.85")
5. Arrays contain actual values (not None)

---

## If It Still Fails

If you still see errors:

### Check 1: Verify the Prompt
Run the debug query to confirm Claude is returning valid JSON.

### Check 2: Check FROM_JSON Schema
Ensure the schema matches exactly:
```sql
'STRUCT<red_flags:ARRAY<STRING>,suspicious_patterns:ARRAY<STRING>,risk_score:DOUBLE,affected_entities:ARRAY<STRING>>'
```

### Check 3: Test FROM_JSON Directly
```sql
SELECT FROM_JSON(
  '{"red_flags": ["test"], "suspicious_patterns": ["test"], "risk_score": 0.9, "affected_entities": ["test"]}',
  'STRUCT<red_flags:ARRAY<STRING>,suspicious_patterns:ARRAY<STRING>,risk_score:DOUBLE,affected_entities:ARRAY<STRING>>'
) as test
```

This should return a valid struct.

### Check 4: Compare to Working Functions
Look at `fraud_classify` or `fraud_generate_explanation` - they use the same pattern and work correctly.

---

## Next Steps After Verification

Once verified:

1. ✅ The function is fixed and working
2. ✅ The test code has better error handling
3. ✅ The pattern can be applied to other functions if needed
4. ✅ You understand why debug worked but test failed

**You're ready to use the function in production!** 🎉

