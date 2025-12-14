# Databricks notebook source
# MAGIC %md
# MAGIC # Create Fraud Cases Knowledge Base
# MAGIC
# MAGIC Creates embedded knowledge base documents about fraud patterns.
# MAGIC All configuration from config.yaml.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

cfg = get_config()
print(f"Volume path: {cfg.volume_path}")
print(f"Knowledge base table: {cfg.knowledge_base_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Knowledge Base Documents

# COMMAND ----------

# Embedded knowledge base about fraud patterns
fraud_knowledge = [
    {
        "doc_id": "FRAUD-BILLING-001",
        "doc_type": "Pattern Guide",
        "title": "Billing Fraud Patterns",
        "content": """
BILLING FRAUD - IDENTIFICATION GUIDE

Common Patterns:
1. DUPLICATE BILLING
   - Same service billed multiple times
   - Check for identical dates, amounts, procedure codes
   - Red flag: Multiple charges within 24 hours

2. INFLATED CHARGES  
   - Services billed at rates significantly above market
   - Unbundling: Billing components separately vs package rate
   - Red flag: Amount >200% of typical rate

3. PHANTOM BILLING
   - Billing for services never performed
   - Non-existent equipment or supplies
   - Red flag: Services impossible to provide (wrong specialty, equipment)

Detection Indicators:
- Provider bills unusually high volumes
- Unusual procedure code combinations
- Services don't match diagnosis
- Provider location doesn't match service type
"""
    },
    {
        "doc_id": "FRAUD-IDENTITY-001",
        "doc_type": "Pattern Guide",
        "title": "Identity Fraud Patterns",
        "content": """
IDENTITY FRAUD - IDENTIFICATION GUIDE

Common Patterns:
1. STOLEN IDENTITY
   - Claimant information doesn't match policy holder
   - SSN/ID mismatches
   - Red flag: Recently changed contact information

2. FAKE CLAIMANT
   - Fabricated person filing claims
   - No employment or credit history
   - Red flag: Unable to verify identity through multiple sources

3. IDENTITY SHARING
   - Multiple people using same insurance card
   - Claims from different locations simultaneously
   - Red flag: Pattern of care doesn't match single individual

Detection Indicators:
- Inconsistent demographic information
- Multiple claims from different locations
- Claimant unreachable or provides false contact info
- Signature inconsistencies
"""
    },
    {
        "doc_id": "FRAUD-PROVIDER-001",
        "doc_type": "Pattern Guide",
        "title": "Provider Fraud Patterns",
        "content": """
PROVIDER FRAUD - IDENTIFICATION GUIDE

Common Patterns:
1. PHANTOM PROVIDER
   - Provider doesn't exist or is unlicensed
   - Fake credentials or closed practice
   - Red flag: Provider information can't be verified

2. KICKBACK SCHEMES
   - Provider receiving payments for referrals
   - Unusual referral patterns
   - Red flag: High volume of referrals to specific providers

3. UNNECESSARY SERVICES
   - Over-treatment or excessive procedures
   - Services not medically necessary
   - Red flag: Volume significantly above peer providers

Detection Indicators:
- Provider can't be verified in databases
- Unusual billing patterns compared to peers
- High percentage of claims from this provider flagged
- Provider address is residential or doesn't exist
"""
    },
    {
        "doc_id": "FRAUD-EXAGGERATION-001",
        "doc_type": "Pattern Guide",
        "title": "Exaggeration Fraud Patterns",
        "content": """
EXAGGERATION FRAUD - IDENTIFICATION GUIDE

Common Patterns:
1. INFLATED DAMAGE
   - Claiming more damage than actually occurred
   - Pre-existing damage claimed as new
   - Red flag: Damage doesn't match incident description

2. EXAGGERATED INJURY
   - Minor injury claimed as serious
   - Prolonged treatment beyond typical recovery
   - Red flag: Treatment timeline far exceeds medical norms

3. FALSE SEVERITY
   - Claiming higher severity level for bigger payout
   - Inconsistent injury descriptions
   - Red flag: Medical records don't support claimed severity

Detection Indicators:
- Treatment duration excessive for diagnosis
- Multiple providers with different diagnoses
- Claimant's activities don't match claimed injury
- Photos/evidence don't support claim amount
"""
    },
    {
        "doc_id": "FRAUD-STAGED-001",
        "doc_type": "Pattern Guide",
        "title": "Staged Incident Patterns",
        "content": """
STAGED INCIDENTS - IDENTIFICATION GUIDE

Common Patterns:
1. STAGED ACCIDENTS
   - Deliberately caused accidents for insurance claims
   - Multiple parties involved in scheme
   - Red flag: Inconsistent witness statements

2. PRE-EXISTING DAMAGE
   - Damage existed before reported incident
   - Incident fabricated to cover old damage
   - Red flag: Damage inconsistent with reported cause

3. FALSE INCIDENT REPORTS
   - Incident never occurred
   - Fabricated police reports or documentation
   - Red flag: No corroborating evidence

Detection Indicators:
- Claimants know each other (social media, addresses)
- Incident details inconsistent across statements
- Police report conflicts with claim details
- Timing suspicious (new policy, financial stress)
- Same repair shop/medical provider across multiple claimants
"""
    },
    {
        "doc_id": "FRAUD-INVESTIGATION-001",
        "doc_type": "Investigation Guide",
        "title": "Fraud Investigation Best Practices",
        "content": """
FRAUD INVESTIGATION - BEST PRACTICES

Step 1: Initial Red Flag Assessment
- Review claim against historical patterns
- Check claimant history (previous claims, timing)
- Verify provider credentials and history
- Look for multiple concurrent claims

Step 2: Data Analysis
- Compare amounts to typical claims
- Check diagnosis codes vs procedures
- Review provider billing patterns
- Analyze geographic patterns

Step 3: Documentation Review
- Request supporting documentation
- Verify medical records
- Check photos/evidence authenticity
- Review police reports if applicable

Step 4: External Verification
- Confirm provider licensure
- Check claimant employment/residence
- Verify incident details with external sources
- Review social media activity

Step 5: Decision Making
- Document all findings
- Weigh evidence objectively
- Consider false positive cost
- Make recommendation: Approve, Deny, or Investigate Further

Escalation Criteria:
- Amount > $50,000
- Multiple red flags present
- Provider with history of fraud
- Organized fraud ring suspected
"""
    },
    {
        "doc_id": "FRAUD-LEGAL-001",
        "doc_type": "Legal Guide",
        "title": "Legal Considerations in Fraud Detection",
        "content": """
LEGAL CONSIDERATIONS - FRAUD DETECTION

Fair Claims Handling:
- Must investigate claims in good faith
- Cannot deny solely based on AI/automated decision
- Must provide clear reason for denial
- Allow claimant to provide additional information

Privacy Compliance:
- HIPAA compliance for medical information
- Proper handling of personal data
- Secure storage of investigation files
- Limited disclosure of fraud findings

Evidence Standards:
- Document all investigation steps
- Maintain chain of custody for evidence
- Use only legally obtained information
- Prepare for potential litigation

Communication Guidelines:
- Never accuse claimant of fraud without proof
- Use neutral language ("requires further review")
- Provide clear explanation of decision
- Document all communications

Reporting Requirements:
- Report suspected fraud to authorities as required
- Comply with state insurance regulations
- Coordinate with law enforcement when appropriate
- Maintain confidentiality during investigations
"""
    }
]

print(f"✅ Created {len(fraud_knowledge)} knowledge base documents")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Volume (if not exists)

# COMMAND ----------

# Create volume for knowledge base documents
try:
    spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {cfg.catalog}.{cfg.schema}.fraud_knowledge_docs
    COMMENT 'Knowledge base documents for fraud detection vector search'
    """)
    print(f"✅ Volume created: {cfg.catalog}.{cfg.schema}.fraud_knowledge_docs")
except Exception as e:
    print(f"Volume creation: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Documents to Volume

# COMMAND ----------

volume_path = f"/Volumes/{cfg.catalog}/{cfg.schema}/fraud_knowledge_docs"

# Write each document as a text file
for doc in fraud_knowledge:
    file_name = f"{doc['doc_id']}.txt"
    file_path = f"{volume_path}/{file_name}"
    
    # Format document content with metadata
    full_content = f"""Document ID: {doc['doc_id']}
Type: {doc['doc_type']}
Title: {doc['title']}

{doc['content']}
"""
    
    # Write to volume
    dbutils.fs.put(file_path, full_content, overwrite=True)
    print(f"✅ Written: {file_name}")

print(f"\n✅ All {len(fraud_knowledge)} documents written to volume")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("=" * 80)
print("KNOWLEDGE BASE DOCUMENTS CREATED!")
print("=" * 80)
print(f"✅ Volume: {volume_path}")
print(f"✅ Documents: {len(fraud_knowledge)}")
print("=" * 80)
print("\n📝 Next step: Run 06a_chunk_knowledge_base.py to create table with CDF")
print("=" * 80)


