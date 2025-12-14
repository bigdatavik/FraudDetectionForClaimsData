# Databricks notebook source
# MAGIC %md
# MAGIC # Batch Analyze All Claims
# MAGIC
# MAGIC Runs the 3 UC fraud detection functions on all claims and stores results.
# MAGIC This populates the fraud_analysis table for Genie queries.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

from datetime import datetime
from pyspark.sql.functions import col, current_timestamp

cfg = get_config()
print(f"Analyzing claims from: {cfg.claims_table}")
print(f"Storing results in: {cfg.catalog}.{cfg.schema}.fraud_analysis")

# TESTING: Set to a small number for testing, or None to process all claims
TEST_LIMIT = 10  # Change to None to process all claims
print(f"\n⚠️  TEST MODE: Processing only {TEST_LIMIT} claims" if TEST_LIMIT else "Processing ALL claims")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Claims to Analyze

# COMMAND ----------

# Load all claims (or filter for new/unanalyzed claims)
claims_df = spark.table(cfg.claims_table)

# Apply test limit if set
if TEST_LIMIT:
    claims_df = claims_df.limit(TEST_LIMIT)
    print(f"⚠️  TEST MODE: Limited to {TEST_LIMIT} claims for testing")

total_claims = claims_df.count()
print(f"📊 Found {total_claims} claims to analyze")

# Show sample
print("\nSample claims:")
display(claims_df.limit(3))

# Create temp view for subsequent queries
claims_df.createOrReplaceTempView("claims_to_process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Batch Process Claims Using UC Functions

# COMMAND ----------

# Register UDFs that call the UC functions
# This allows us to process in batch rather than row-by-row

print("Running batch fraud analysis...")
print("This will call all 3 UC functions for each claim...")
print("Note: Some claims may be skipped if they trigger content filters")

# Process claims with error handling using TRY/CATCH
# Call all 3 UC functions using SQL with try_* functions for error handling
analyzed_df = spark.sql(f"""
SELECT 
    claim_id,
    CURRENT_TIMESTAMP() as analysis_timestamp,
    claim_text,
    
    -- Call fraud_classify with error handling
    TRY_CAST(
        {cfg.catalog}.{cfg.schema}.fraud_classify(claim_text) 
        AS STRUCT<is_fraudulent:BOOLEAN, fraud_probability:DOUBLE, fraud_type:STRING, confidence:DOUBLE>
    ) as classification,
    
    -- Call fraud_extract_indicators with error handling
    TRY_CAST(
        {cfg.catalog}.{cfg.schema}.fraud_extract_indicators(claim_text)
        AS STRUCT<red_flags:ARRAY<STRING>, suspicious_patterns:ARRAY<STRING>, risk_score:DOUBLE, affected_entities:ARRAY<STRING>>
    ) as indicators
    
FROM claims_to_process
""")

# Now we need to call fraud_generate_explanation with the classification results
# First, persist the intermediate results
analyzed_df.createOrReplaceTempView("temp_analysis")

# Call explanation function with classification results - skip rows with NULL classification
final_df = spark.sql(f"""
SELECT 
    t.claim_id,
    t.analysis_timestamp,
    
    -- Extract classification fields (with NULL handling)
    COALESCE(t.classification.is_fraudulent, FALSE) as is_fraudulent,
    COALESCE(t.classification.fraud_probability, 0.0) as fraud_probability,
    COALESCE(t.classification.fraud_type, 'Unknown') as fraud_type,
    COALESCE(t.classification.confidence, 0.0) as classification_confidence,
    
    -- Extract indicator fields (with NULL handling)
    COALESCE(t.indicators.red_flags, ARRAY()) as red_flags,
    COALESCE(t.indicators.suspicious_patterns, ARRAY()) as suspicious_patterns,
    COALESCE(t.indicators.risk_score, 0.0) as risk_score,
    COALESCE(t.indicators.affected_entities, ARRAY()) as affected_entities,
    
    -- Call explanation function with error handling (only if classification succeeded)
    CASE 
        WHEN t.classification IS NOT NULL THEN
            TRY_CAST(
                {cfg.catalog}.{cfg.schema}.fraud_generate_explanation(
                    t.claim_text,
                    t.classification.is_fraudulent,
                    t.classification.fraud_type
                ) AS STRUCT<explanation:STRING, evidence:ARRAY<STRING>, recommendations:ARRAY<STRING>>
            )
        ELSE NULL
    END as explanation_result
    
FROM temp_analysis t
""")

# Extract explanation fields
# First create temp view from final_df
final_df.createOrReplaceTempView("temp_final")

final_with_explanation = spark.sql(f"""
SELECT 
    claim_id,
    analysis_timestamp,
    is_fraudulent,
    fraud_probability,
    fraud_type,
    classification_confidence,
    red_flags,
    suspicious_patterns,
    risk_score,
    affected_entities,
    COALESCE(explanation_result.explanation, 'No explanation available') as explanation,
    COALESCE(explanation_result.evidence, ARRAY()) as evidence,
    COALESCE(explanation_result.recommendations, ARRAY()) as recommendations
FROM temp_final
""")

# IMPORTANT: Cache the result to avoid re-computing expensive LLM calls
print("Caching results to avoid re-computation...")
final_with_explanation.cache()

# Count successful vs failed analyses
success_count = final_with_explanation.filter("explanation != 'No explanation available'").count()
print(f"✅ Successfully analyzed {success_count} out of {total_claims} claims")
if success_count < total_claims:
    print(f"⚠️  {total_claims - success_count} claims were skipped due to content filtering or errors")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Show Sample Results

# COMMAND ----------

print("=" * 80)
print("SAMPLE FRAUD ANALYSIS RESULTS")
print("=" * 80)
display(final_with_explanation.limit(3))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Results to Table

# COMMAND ----------

# Write results to fraud_analysis table
final_with_explanation.write.mode("overwrite").saveAsTable(
    f"{cfg.catalog}.{cfg.schema}.fraud_analysis"
)

# Unpersist cache after write
final_with_explanation.unpersist()

print(f"✅ Saved {total_claims} fraud analysis results to table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Results

# COMMAND ----------

print("=" * 80)
print("FRAUD ANALYSIS STATISTICS")
print("=" * 80)

stats = spark.sql(f"""
SELECT 
    COUNT(*) as total_analyzed,
    SUM(CASE WHEN is_fraudulent THEN 1 ELSE 0 END) as fraud_cases,
    ROUND(AVG(CASE WHEN is_fraudulent THEN 1 ELSE 0 END) * 100, 2) as fraud_rate_pct,
    AVG(risk_score) as avg_risk_score,
    MIN(analysis_timestamp) as analysis_start,
    MAX(analysis_timestamp) as analysis_end
FROM {cfg.catalog}.{cfg.schema}.fraud_analysis
""").collect()[0]

print(f"Total Analyzed:  {stats['total_analyzed']}")
print(f"Fraud Cases:     {stats['fraud_cases']}")
print(f"Fraud Rate:      {stats['fraud_rate_pct']}%")
print(f"Avg Risk Score:  {stats['avg_risk_score']:.2f}")
print("=" * 80)

# Show fraud type breakdown
print("\nFraud Types:")
display(spark.sql(f"""
SELECT fraud_type, COUNT(*) as count
FROM {cfg.catalog}.{cfg.schema}.fraud_analysis
WHERE is_fraudulent = TRUE
GROUP BY fraud_type
ORDER BY count DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Unified View

# COMMAND ----------

print("Testing unified view (claims + fraud analysis)...")
display(spark.sql(f"""
SELECT 
    claim_id,
    claim_type,
    claim_amount,
    ground_truth_is_fraud,
    ai_detected_fraud,
    fraud_probability,
    risk_score,
    ai_detected_fraud_type
FROM {cfg.catalog}.{cfg.schema}.fraud_claims_complete
WHERE ai_detected_fraud = TRUE
LIMIT 5
"""))

# COMMAND ----------

print("=" * 80)
print("BATCH ANALYSIS COMPLETE!")
print("=" * 80)
print(f"✅ Analyzed: {total_claims} claims")
print(f"✅ Results stored in: {cfg.catalog}.{cfg.schema}.fraud_analysis")
print(f"✅ Unified view ready: {cfg.catalog}.{cfg.schema}.fraud_claims_complete")
print("=" * 80)
print("\n📝 Next step: Update Genie Space to query fraud_claims_complete view")
print("   Or test queries in Genie: 'Show me all fraudulent claims'")
print("=" * 80)


