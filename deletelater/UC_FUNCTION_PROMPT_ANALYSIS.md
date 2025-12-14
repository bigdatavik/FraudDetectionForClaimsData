# UC Function Prompt Quality Analysis

## Issue Found and Fixed

### ❌ `04_uc_fraud_extract.py` - FIXED
**Status**: Had broken prompt, now fixed

**Original Problem**:
```sql
'Return ONLY valid JSON with NO extra text. CLAIM: ', claim_text, 
' JSON format: {"red_flags": ["flag1"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}} Return ONLY the JSON.'
```

**Fixed Version**:
```sql
'You are a healthcare fraud investigator. Extract fraud indicators from this claim.\\n\\n',
'CLAIM: ', claim_text, '\\n\\n',
'Return ONLY JSON: {{"red_flags": ["flag1", "flag2"], "suspicious_patterns": ["pattern1"], "risk_score": 0.9, "affected_entities": ["entity1"]}}\\n\\n',
'Return ONLY the JSON object.'
```

---

## Other Functions - Already Good

### ✅ `03_uc_fraud_classify.py` - GOOD
**Status**: Prompt is well-structured

```sql
'You are a healthcare fraud detection AI. Return ONLY a JSON object.\\n\\n',
'CLAIM: ', claim_text, '\\n\\n',
'Return this JSON: {{"is_fraudulent": true/false, "fraud_probability": 0.0-1.0, "fraud_type": "Upcoding/Unbundling/Phantom/Duplicate/Unnecessary/Kickback/Identity/Prescription/None", "confidence": 0.0-1.0}}\\n\\n',
'Rules: If claim says "billed X but actually Y" then is_fraudulent=true. If provider has fraud pattern then is_fraudulent=true. If amount 2-3x higher then is_fraudulent=true.\\n\\n',
'Return ONLY the JSON object, no other text.'
```

**Why it works**:
- ✅ Role context: "You are a healthcare fraud detection AI"
- ✅ Clear sections with `\\n\\n`
- ✅ Explicit rules provided
- ✅ Clear JSON format
- ✅ Final reinforcement

---

### ✅ `05_uc_fraud_explain.py` - GOOD
**Status**: Prompt is adequate

```sql
'Explain this fraud decision for a healthcare payer claims adjuster.\\n\\n',
'CLAIM: ', claim_text, '\\n',
'DECISION: ', IF(is_fraudulent, 'FRAUDULENT', 'LEGITIMATE'), '\\n',
'FRAUD TYPE: ', fraud_type, '\\n\\n',
'Return ONLY JSON: {{"explanation": "summary text", "evidence": ["fact1", "fact2"], "recommendations": ["action1", "action2"]}}\\n\\n',
'Return ONLY the JSON object.'
```

**Why it works**:
- ✅ Task context: "Explain this fraud decision for a healthcare payer claims adjuster"
- ✅ Clear sections with `\\n\\n` or `\\n`
- ✅ Input parameters clearly labeled
- ✅ Clear JSON format with array examples
- ✅ Final reinforcement

---

## Best Practices for UC AI Function Prompts

Based on this debugging experience:

### 1. **Always Include Role/Task Context**
```sql
'You are a [role]. [Task description].'
```

### 2. **Use Visual Separation**
```sql
'\\n\\n'  -- Double newline between sections
'\\n'     -- Single newline within sections
```

### 3. **Label Inputs Clearly**
```sql
'CLAIM: ', claim_text, '\\n\\n'
'DECISION: ', decision, '\\n'
```

### 4. **Provide Clear JSON Examples**
```sql
'Return ONLY JSON: {{"field1": ["item1", "item2"], "field2": 0.9}}'
```
- Show array examples with multiple items
- Show numeric examples with realistic values
- Use escaped double quotes `{{}}`

### 5. **Add Reinforcement**
```sql
'Return ONLY the JSON object.'
```

### 6. **Structure Pattern**
```sql
CONCAT(
  'Role/Task context.\\n\\n',
  'INPUT_LABEL: ', input_var, '\\n\\n',
  'Return ONLY JSON: {{...}}\\n\\n',
  'Optional rules/guidelines.\\n\\n',
  'Return ONLY the JSON object.'
)
```

---

## Why This Matters

When `FROM_JSON()` receives unparseable input:
1. **No error is thrown** ❌
2. **All fields become `None`** ⚠️
3. **Downstream code fails mysteriously** 💥

Good prompts prevent this by ensuring Claude returns clean JSON every time.

---

## Summary Table

| Function | Status | Has Role Context | Uses Newlines | Clear Format | Needs Fix |
|----------|--------|------------------|---------------|--------------|-----------|
| `fraud_classify` | ✅ Good | ✅ Yes | ✅ Yes | ✅ Yes | No |
| `fraud_extract_indicators` | ✅ Fixed | ✅ Yes (now) | ✅ Yes (now) | ✅ Yes (now) | **Was broken** |
| `fraud_generate_explanation` | ✅ Good | ✅ Yes | ✅ Yes | ✅ Yes | No |

All functions now follow best practices! 🎉

