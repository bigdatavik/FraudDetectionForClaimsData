# Sample Data Files

This folder contains sample CSV files for testing the Fraud Detection application.

## Files

### `sample_claims.csv`
A collection of 10 healthcare claims for testing batch processing functionality.

**Format:**
- `claim_id`: Unique identifier (e.g., CLM-2024-001)
- `claim_text`: Detailed claim description
- `claim_amount`: Dollar amount of the claim
- `claim_type`: Type of claim (Medical-Outpatient, Dental, Prescription, Lab Services, etc.)

**Contents:**
| # | Claim ID | Type | Amount | Expected Result |
|---|----------|------|--------|-----------------|
| 1 | CLM-2024-001 | Medical-Outpatient | $185 | Legitimate |
| 2 | CLM-2024-002 | Medical-Outpatient | $47,500 | **FRAUD** (Upcoding) |
| 3 | CLM-2024-003 | Dental | $0 | Legitimate |
| 4 | CLM-2024-004 | Medical-Outpatient | $12,000 | **FRAUD** (Phantom Billing) |
| 5 | CLM-2024-005 | Prescription | $120 | Legitimate |
| 6 | CLM-2024-006 | Prescription | $8,500 | **FRAUD** (Prescription Fraud) |
| 7 | CLM-2024-007 | Medical-Outpatient | $2,400 | Legitimate |
| 8 | CLM-2024-008 | Lab Services | $15,000 | **FRAUD** (Unbundling) |
| 9 | CLM-2024-009 | Medical-Inpatient | $18,500 | Legitimate |
| 10 | CLM-2024-010 | DME | $12,500 | **FRAUD** (Equipment Fraud) |

**Expected Metrics:**
- Total Claims: 10
- Fraudulent: 5 (50%)
- Legitimate: 5 (50%)
- Total Amount: $136,305

## How to Use

### In Streamlit App (Batch Processing Page)
1. Navigate to **Batch Processing** page
2. Click **Upload File** tab
3. Upload `sample_claims.csv`
4. Select analysis depth (Quick/Standard/Deep)
5. Click **Start Batch Analysis**

### In Jupyter Notebooks
```python
import pandas as pd

# Load sample data
df = pd.read_csv('sample_data/sample_claims.csv')

# Process with UC functions
for idx, row in df.iterrows():
    result = spark.sql(f"""
        SELECT fraud_classify('{row['claim_text']}') as classification
    """).collect()[0]
    print(f"{row['claim_id']}: {result}")
```

## Creating Your Own Sample Data

To create additional sample files, ensure your CSV has at minimum:
- `claim_id` - Required
- `claim_text` - Required
- `claim_amount` - Optional but recommended
- `claim_type` - Optional but recommended

Additional columns will be preserved but not used in analysis.

