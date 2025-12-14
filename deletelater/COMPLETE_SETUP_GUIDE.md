# Complete Fraud Detection System - Setup Guide

## 📋 Complete Setup Sequence

Run these notebooks in order:

### Phase 1: Foundation
1. ✅ `01_create_catalog_schema.py` - Creates Unity Catalog structure
2. ✅ `02_generate_sample_data.py` - Creates 1000 sample fraud claims

### Phase 2: UC AI Functions (Real-time Analysis)
3. ✅ `03_uc_fraud_classify.py` - Classifies if claim is fraudulent
4. ✅ `04_uc_fraud_extract.py` - Extracts fraud indicators and red flags
5. ✅ `05_uc_fraud_explain.py` - Generates human-readable explanation

### Phase 3: Knowledge Base (Investigation Guidance)
6. ✅ `06_create_knowledge_base.py` - Creates fraud pattern documents in volume
7. ✅ `06a_chunk_knowledge_base.py` - Chunks documents and creates table with CDF
8. ✅ `07_create_vector_index.py` - Creates vector search index

### Phase 4: Fraud Analysis Results (NEW!)
8. 🆕 `08_create_fraud_analysis_table.py` - Creates table to store batch analysis results
9. 🆕 `09_batch_analyze_claims.py` - Runs UC functions on ALL claims, populates fraud_analysis

### Phase 5: Business Intelligence
10. ✅ `10_create_genie_space.py` - Creates Genie space for natural language analytics

---

## 🔄 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. RAW CLAIMS DATA                                          │
├─────────────────────────────────────────────────────────────┤
│ Table: claims_data                                          │
│ - 1000 sample fraud claims                                  │
│ - claim_id, claim_text, claim_amount, etc.                  │
│ - NO fraud detection results yet                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. BATCH ANALYSIS (Run notebook 10)                        │
├─────────────────────────────────────────────────────────────┤
│ For each claim:                                             │
│  ├─ fraud_classify() → is_fraudulent, probability           │
│  ├─ fraud_extract_indicators() → red_flags, risk_score      │
│  └─ fraud_generate_explanation() → explanation, evidence    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. FRAUD ANALYSIS RESULTS                                   │
├─────────────────────────────────────────────────────────────┤
│ Table: fraud_analysis                                       │
│ - claim_id, is_fraudulent, fraud_probability                │
│ - red_flags, risk_score, suspicious_patterns                │
│ - explanation, evidence, recommendations                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. UNIFIED VIEW (Auto-created by notebook 09)              │
├─────────────────────────────────────────────────────────────┤
│ View: fraud_claims_complete                                 │
│ = claims_data LEFT JOIN fraud_analysis                      │
│ - All claim details + fraud analysis results                │
│ - THIS is what Genie queries!                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 What Each Component Does

### **UC Functions** (Notebooks 3-5)
- **Purpose**: Real-time fraud detection on individual claims
- **When used**: 
  - Streamlit app analyzing a single claim
  - Real-time API calls
  - Batch processing (notebook 10)
- **Example**: `fraud_classify('Patient billed for...')` → `{is_fraudulent: true, probability: 0.85}`

### **Knowledge Base** (Notebooks 6-8)
- **Purpose**: Provide investigation guidance and fraud patterns
- **Content**: 4 documents about billing fraud, investigation procedures, legal considerations
- **When used**: Vector search to answer "How do I investigate upcoding fraud?"
- **Used by**: Streamlit app to show relevant investigation procedures

### **Fraud Analysis Table** (Notebooks 9-10)
- **Purpose**: Store pre-computed fraud analysis results for all claims
- **Why needed**: Genie can't call UC functions, so we pre-compute and store results
- **Populated by**: Batch job that runs UC functions on all claims
- **Used by**: Genie for trend analysis, Streamlit for displaying results

### **Genie Space** (Notebook 11)
- **Purpose**: Natural language business intelligence on fraud data
- **Queries**: `fraud_claims_complete` view (claims + analysis)
- **Example questions**:
  - "Show me all fraudulent claims over $50k"
  - "What's the fraud rate by provider?"
  - "Compare fraud trends this month vs last month"
  - "Which claim types have the highest fraud rate?"

---

## 📊 Three Ways to Use the System

### 1. **Real-Time Individual Claim Analysis** (Streamlit)
```
User loads claim #12345
  ↓
App calls UC Functions in real-time:
  ├─ fraud_classify(claim_text)
  ├─ fraud_extract_indicators(claim_text)  
  └─ fraud_generate_explanation(...)
  ↓
App searches Knowledge Base:
  └─ Vector search for investigation guidance
  ↓
Display: Fraud assessment + investigation steps
```

### 2. **Trend Analysis & Reporting** (Genie)
```
User asks: "Show me high-risk claims from last week"
  ↓
Genie generates SQL:
  SELECT * FROM fraud_claims_complete
  WHERE risk_score > 0.7 
  AND claim_date >= DATE_SUB(CURRENT_DATE(), 7)
  ↓
Returns: Table + visualizations
  ↓
User follow-up: "Group by provider"
  ↓
Genie maintains context and updates query
```

### 3. **Batch Re-Analysis** (When UC Functions Updated)
```
You improve fraud detection logic
  ↓
Update UC functions (notebooks 3-5)
  ↓
Re-run notebook 10 (batch analyze)
  ↓
fraud_analysis table updated with new results
  ↓
Genie queries now use latest analysis
```

---

## 🎨 Tables & Relationships

```
claims_data                     fraud_analysis
├─ claim_id (PK)               ├─ claim_id (FK)
├─ claim_text                  ├─ is_fraudulent
├─ claim_amount                ├─ fraud_probability
├─ claim_type                  ├─ red_flags []
├─ provider_id                 ├─ risk_score
└─ claim_date                  └─ explanation
         │                              │
         └──────────┬───────────────────┘
                    │
                    ▼
        fraud_claims_complete (VIEW)
        ├─ All columns from claims_data
        └─ All columns from fraud_analysis
                    │
                    ▼
              Genie Space
          (Natural Language Queries)
```

---

## 📋 Next Steps

1. **Run Notebook 08**: Creates fraud_analysis table and unified view
2. **Run Notebook 09**: Analyzes all 1000 claims, populates results
3. **Run Notebook 10**: Creates Genie space pointing to fraud_claims_complete view 
   - Open Genie space
   - Ask: "Show me all fraudulent claims"
   - Ask: "What is the fraud rate by claim type?"
   - Ask: "Which providers have the most fraud?"
4. **Build Streamlit App**: 
   - Page 1: Single claim analysis (calls UC functions)
   - Page 2: Trend dashboard (embeds Genie)
   - Page 3: Investigation guidance (vector search)

---

## 🎯 Key Insight

**The Missing Link Was the Batch Analysis!**

- ✅ UC Functions exist but need to be RUN on all claims
- ✅ Results must be STORED for Genie to query
- ✅ Unified view makes querying easy
- ✅ Now Genie can answer "show me fraud claims"

**Before**: Genie could only query raw claims (no fraud info)
**After**: Genie queries fraud_claims_complete (claims + AI analysis)

---

## 📝 Configuration

All tables created under:
- **Catalog**: `fraud_detection_dev`
- **Schema**: `claims_analysis`

Tables:
- `claims_data` - Raw claims (1000 rows)
- `fraud_analysis` - AI analysis results (1000 rows after batch)
- `knowledge_base` - Fraud investigation guides (chunked)

Views:
- `fraud_claims_complete` - Unified view (what Genie uses)

Indexes:
- `fraud_cases_index` - Vector search on knowledge_base

---

Ready to run notebooks 08, 09, and 10! 🚀

