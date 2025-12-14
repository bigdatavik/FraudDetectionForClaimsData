# Prompt Comparison: Why Debug Worked but Test Failed

## ❌ BROKEN: Original Function Prompt (Lines 54-56)

```sql
CONCAT(
  'Return ONLY valid JSON with NO extra text. CLAIM: ', claim_text, 
  ' JSON format: {{"red_flags": ["flag1"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}} Return ONLY the JSON.'
)
```

### What Claude Actually Saw:
```
Return ONLY valid JSON with NO extra text. CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150 for actual service rendered. JSON format: {"red_flags": ["flag1"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}} Return ONLY the JSON.
```

### Problems:
1. **No role context** - Claude doesn't know it's a fraud investigator
2. **Everything runs together** - claim text flows directly into instructions
3. **Confusing structure** - hard to parse where the claim ends and instructions begin
4. **Result**: Claude likely returned explanatory text or markdown-wrapped JSON
5. **Consequence**: `FROM_JSON()` couldn't parse it → returned `None` for all fields

---

## ✅ WORKING: Debug Query Prompt (Lines 73-83)

```sql
'You are a healthcare fraud investigator. Extract fraud indicators from this claim.

CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150.

Return ONLY JSON: {"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}

Return ONLY the JSON object.'
```

### What Claude Actually Saw:
```
You are a healthcare fraud investigator. Extract fraud indicators from this claim.

CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150.

Return ONLY JSON: {"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}

Return ONLY the JSON object.
```

### Why It Works:
1. ✅ **Clear role** - "You are a healthcare fraud investigator"
2. ✅ **Newlines separate sections** - claim is clearly marked
3. ✅ **Task is explicit** - "Extract fraud indicators"
4. ✅ **Format example is clear** - shows array structure with multiple items
5. ✅ **Reinforcement** - "Return ONLY the JSON object" at the end
6. ✅ **Result**: Claude returns pure JSON → `FROM_JSON()` parses successfully

---

## ✅ FIXED: New Function Prompt

```sql
CONCAT(
  'You are a healthcare fraud investigator. Extract fraud indicators from this claim.\\n\\n',
  'CLAIM: ', claim_text, '\\n\\n',
  'Return ONLY JSON: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
  'Return ONLY the JSON object.'
)
```

### Key Changes:
1. ✅ Added role context at the start
2. ✅ Used `\\n\\n` to create clear visual separation
3. ✅ Moved claim into its own section with "CLAIM:" label
4. ✅ Provided clearer JSON example with multiple array items
5. ✅ Added final reinforcement line

### What Claude Now Sees:
```
You are a healthcare fraud investigator. Extract fraud indicators from this claim.

CLAIM: Healthcare claim: Patient billed for CPT 99215 (complex office visit) but medical notes indicate routine check-up. Provider has 4 similar upcoding patterns this month. Claim amount $450 vs typical $150 for actual service rendered.

Return ONLY JSON: {"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}

Return ONLY the JSON object.
```

This matches the debug query structure exactly! 🎯

---

## The FROM_JSON Silent Failure

When `FROM_JSON()` receives unparseable input, it doesn't throw an error - it returns a struct with all fields set to `None`:

```python
{
  'red_flags': None,
  'suspicious_patterns': None,
  'risk_score': None,
  'affected_entities': None
}
```

Then when the test code tries:
```python
print(f"  Risk Score: {test_result['indicators']['risk_score']:.2f}")
```

It fails with:
```
TypeError: unsupported format string passed to NoneType.__format__
```

Because you can't format `None` with `.2f`!

---

## Summary

| Aspect | Original | Fixed |
|--------|----------|-------|
| Role context | ❌ None | ✅ "You are a healthcare fraud investigator" |
| Structure | ❌ Run-on sentence | ✅ Clear sections with newlines |
| Claim label | ❌ Embedded in instructions | ✅ "CLAIM:" with separation |
| Example quality | ❌ Single item arrays | ✅ Multiple items shown |
| Reinforcement | ⚠️ Weak | ✅ Clear final instruction |
| Result | ❌ FROM_JSON fails → None | ✅ FROM_JSON succeeds → Data |

