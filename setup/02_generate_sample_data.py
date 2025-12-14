# Databricks notebook source
# MAGIC %md
# MAGIC # Generate Sample Claims Data
# MAGIC
# MAGIC Generates realistic synthetic HEALTHCARE claims data for payers (Humana, UHG, Aetna).
# MAGIC All configuration from config.yaml via shared.config module.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config, print_config

cfg = get_config()
print_config(cfg)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Claims Data

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import *
import random
from datetime import datetime, timedelta

# Healthcare fraud patterns for payers
FRAUD_PATTERNS = {
    "Upcoding": ["CPT code inflated", "billed higher complexity", "unwarranted level 5 visit"],
    "Unbundling": ["separated bundled procedures", "multiple line items for bundled service"],
    "Phantom": ["service never rendered", "patient denies receiving service"],
    "Duplicate": ["duplicate billing", "same claim resubmitted", "double billing"],
    "Unnecessary": ["medically unnecessary procedure", "excessive testing", "overutilization"],
    "Kickback": ["illegal referral arrangement", "financial incentive for referral"],
    "Identity": ["stolen patient ID", "deceased patient billed", "identity theft"],
    "Prescription": ["pill mill pattern", "fake prescription", "controlled substance abuse"]
}

CLAIM_TYPES = ["Medical-Inpatient", "Medical-Outpatient", "Prescription", "DME", "Home Health"]

# Generate sample claims
def generate_claim(claim_id, is_fraud=False):
    """Generate a single realistic claim"""
    
    # Random claim type
    claim_type = random.choice(CLAIM_TYPES)
    
    # Healthcare payer amounts
    if "Inpatient" in claim_type:
        base_amount = random.randint(5000, 50000)
    elif "Outpatient" in claim_type:
        base_amount = random.randint(500, 5000)
    elif "Prescription" in claim_type:
        base_amount = random.randint(50, 2000)
    elif "DME" in claim_type:  # Durable Medical Equipment
        base_amount = random.randint(200, 10000)
    else:  # Home Health
        base_amount = random.randint(1000, 15000)
    
    # Fraud multiplier
    if is_fraud:
        fraud_type = random.choice(list(FRAUD_PATTERNS.keys()))
        # Fraudulent claims tend to be higher
        amount = int(base_amount * random.uniform(1.5, 3.0))
        
        # Generate fraud indicators
        indicators = random.sample(FRAUD_PATTERNS[fraud_type], 
                                   k=min(random.randint(2, 4), len(FRAUD_PATTERNS[fraud_type])))
        
        # Healthcare payer fraud-specific text patterns
        suspicious_phrases = [
            "diagnosis code mismatch with procedure",
            "out-of-network provider high cost",
            "multiple claims same day different facilities",
            "unusual procedure combination",
            "provider flagged in LEIE database",
            "geographic anomaly patient-provider",
            "NPI number suspicious activity"
        ]
        
        description = f"{claim_type} claim for ${amount:,}. " + \
                     random.choice(suspicious_phrases) + ". " + \
                     "Indicators: " + ", ".join(indicators)
    else:
        fraud_type = "None"
        amount = base_amount
        indicators = []
        
        # Legitimate healthcare claim descriptions
        legit_descriptions = {
            "Medical-Inpatient": ["appendectomy", "knee replacement surgery", "cardiac catheterization"],
            "Medical-Outpatient": ["office visit level 3", "diagnostic imaging", "lab work"],
            "Prescription": ["30-day medication supply", "insulin prescription", "generic antibiotic"],
            "DME": ["wheelchair", "CPAP machine", "hospital bed"],
            "Home Health": ["skilled nursing visit", "physical therapy session", "wound care"]
        }
        
        description = f"{claim_type} claim for ${amount:,}. " + \
                     random.choice(legit_descriptions.get(claim_type, ["standard claim"]))
    
    # Generate dates
    days_ago = random.randint(1, 180)
    claim_date = datetime.now() - timedelta(days=days_ago)
    
    return {
        "claim_id": f"CLM-{claim_id:06d}",
        "claim_amount": float(amount),
        "claim_date": claim_date,
        "claim_type": claim_type,
        "claimant_info": {
            "name": f"Claimant {claim_id}",
            "age": random.randint(18, 85),
            "location": random.choice(["CA", "NY", "TX", "FL", "IL"])
        },
        "provider_info": {
            "provider_id": f"PRV-{random.randint(1000, 9999)}",
            "specialty": claim_type,
            "location": random.choice(["CA", "NY", "TX", "FL", "IL"])
        },
        "diagnosis_codes": [f"ICD-{random.randint(100, 999)}" for _ in range(random.randint(1, 3))],
        "treatment_description": description,
        "claim_text": description,
        "is_fraud": is_fraud,
        "fraud_type": fraud_type,
        "fraud_indicators": indicators
    }

print(f"Generating {cfg.num_claims} claims with {cfg.fraud_rate*100:.0f}% fraud rate...")

# Generate claims
claims_data = []
num_fraud = int(cfg.num_claims * cfg.fraud_rate)
num_legit = cfg.num_claims - num_fraud

# Generate fraud claims
for i in range(num_fraud):
    claims_data.append(generate_claim(i + 1, is_fraud=True))

# Generate legitimate claims
for i in range(num_legit):
    claims_data.append(generate_claim(i + num_fraud + 1, is_fraud=False))

# Shuffle
random.shuffle(claims_data)

print(f"✅ Generated {len(claims_data)} claims")
print(f"   Fraud: {num_fraud}")
print(f"   Legitimate: {num_legit}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create DataFrame and Table

# COMMAND ----------

# Define schema
schema = StructType([
    StructField("claim_id", StringType(), False),
    StructField("claim_amount", DoubleType(), False),
    StructField("claim_date", TimestampType(), False),
    StructField("claim_type", StringType(), False),
    StructField("claimant_info", MapType(StringType(), StringType()), True),
    StructField("provider_info", MapType(StringType(), StringType()), True),
    StructField("diagnosis_codes", ArrayType(StringType()), True),
    StructField("treatment_description", StringType(), True),
    StructField("claim_text", StringType(), False),
    StructField("is_fraud", BooleanType(), False),
    StructField("fraud_type", StringType(), True),
    StructField("fraud_indicators", ArrayType(StringType()), True)
])

# Create DataFrame
claims_df = spark.createDataFrame(claims_data, schema=schema)

# Write to Delta table
claims_df.write.mode("overwrite").saveAsTable(cfg.claims_table)

print(f"✅ Created table: {cfg.claims_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Data

# COMMAND ----------

# Show statistics
print("=" * 80)
print("CLAIMS DATA STATISTICS")
print("=" * 80)

stats = spark.sql(f"""
SELECT 
    COUNT(*) as total_claims,
    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_claims,
    SUM(CASE WHEN NOT is_fraud THEN 1 ELSE 0 END) as legit_claims,
    ROUND(AVG(claim_amount), 2) as avg_amount,
    ROUND(AVG(CASE WHEN is_fraud THEN claim_amount END), 2) as avg_fraud_amount,
    ROUND(AVG(CASE WHEN NOT is_fraud THEN claim_amount END), 2) as avg_legit_amount
FROM {cfg.claims_table}
""").collect()[0]

print(f"Total Claims:      {stats['total_claims']}")
print(f"Fraud Claims:      {stats['fraud_claims']}")
print(f"Legit Claims:      {stats['legit_claims']}")
print(f"Fraud Rate:        {stats['fraud_claims']/stats['total_claims']*100:.1f}%")
print(f"Avg Amount:        ${stats['avg_amount']:,.2f}")
print(f"Avg Fraud Amount:  ${stats['avg_fraud_amount']:,.2f}")
print(f"Avg Legit Amount:  ${stats['avg_legit_amount']:,.2f}")
print("=" * 80)

# Show sample claims
print("\nSample fraud claim:")
display(spark.sql(f"""
SELECT claim_id, claim_type, claim_amount, fraud_type, 
       claim_text, fraud_indicators
FROM {cfg.claims_table}
WHERE is_fraud = TRUE
LIMIT 1
"""))

print("\nSample legitimate claim:")
display(spark.sql(f"""
SELECT claim_id, claim_type, claim_amount, fraud_type, claim_text
FROM {cfg.claims_table}
WHERE is_fraud = FALSE
LIMIT 1
"""))

# COMMAND ----------

print("=" * 80)
print("DATA GENERATION COMPLETE!")
print("=" * 80)
print(f"✅ Table created: {cfg.claims_table}")
print(f"✅ Total claims: {cfg.num_claims}")
print(f"✅ Fraud rate: {cfg.fraud_rate*100:.0f}%")
print("=" * 80)

