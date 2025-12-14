# Databricks notebook source
# MAGIC %md
# MAGIC # CLEANUP - Remove All Fraud Detection Resources
# MAGIC
# MAGIC **WARNING:** This will delete:
# MAGIC - Catalog and Schema (from config.yaml)
# MAGIC - Vector Search Index
# MAGIC - All tables (claims, fraud_cases_kb)
# MAGIC - All volumes
# MAGIC - All UC functions (fraud_classify, fraud_extract_indicators, fraud_generate_explanation)
# MAGIC - Genie Space
# MAGIC
# MAGIC All configuration loaded from config.yaml via shared.config module.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config, print_config

cfg = get_config()

print("🗑️  FRAUD DETECTION CLEANUP SCRIPT")
print("=" * 70)
print(f"Will delete:")
print(f"  - Catalog: {cfg.catalog}")
print(f"  - Schema: {cfg.schema}")
print(f"  - Vector Index: {cfg.catalog}.{cfg.schema}.fraud_cases_index")
print(f"  - Genie Space: {cfg.genie_display_name}")
print("=" * 70)
print("\n⚠️  WARNING: This is IRREVERSIBLE!")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Drop Vector Search Index

# COMMAND ----------

from databricks.sdk import WorkspaceClient

print("\n🔍 Dropping vector search index...")
try:
    w = WorkspaceClient()
    index_name = f"{cfg.catalog}.{cfg.schema}.fraud_cases_index"
    
    print(f"   Deleting: {index_name}")
    w.vector_search_indexes.delete_index(index_name=index_name)
    print(f"   ✅ Deleted vector search index: {index_name}")
except Exception as e:
    print(f"   ⚠️  Index deletion: {e}")
    print(f"   (This is OK if index doesn't exist)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Delete Genie Space

# COMMAND ----------

print("\n🧞 Dropping Genie Space...")
try:
    from databricks.sdk import WorkspaceClient
    
    w = WorkspaceClient()
    
    # List all Genie spaces and find ours
    print(f"   Looking for Genie Space: '{cfg.genie_display_name}'")
    spaces = w.api_client.do('GET', '/api/2.0/genie/spaces')
    our_space_id = None
    
    if spaces and 'spaces' in spaces:
        for space in spaces['spaces']:
            # The API uses 'title' not 'display_name'
            space_name = space.get('title', '')
            if space_name == cfg.genie_display_name:
                our_space_id = space.get('space_id')
                break
    
    if our_space_id:
        print(f"   Found space: {cfg.genie_display_name} (ID: {our_space_id})")
        w.api_client.do('DELETE', f'/api/2.0/genie/spaces/{our_space_id}')
        print(f"   ✅ Trashed Genie Space: {cfg.genie_display_name}")
    else:
        print(f"   ⚠️  Genie Space not found: {cfg.genie_display_name}")
        print(f"   (This is OK if space doesn't exist)")
except Exception as e:
    print(f"   ⚠️  Genie Space deletion: {e}")
    print(f"   (This is OK if space doesn't exist)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Drop Schema (cascades to tables, volumes, functions)

# COMMAND ----------

print("\n📚 Dropping schema with CASCADE...")
try:
    spark.sql(f"DROP SCHEMA IF EXISTS {cfg.catalog}.{cfg.schema} CASCADE")
    print(f"✅ Dropped schema: {cfg.catalog}.{cfg.schema}")
    print("   ✅ All tables removed (claims, fraud_cases_kb)")
    print("   ✅ All volumes removed")
    print("   ✅ All functions removed (fraud_classify, fraud_extract_indicators, fraud_generate_explanation)")
except Exception as e:
    print(f"❌ Error dropping schema: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Drop Catalog (optional - only if you want to remove entire catalog)

# COMMAND ----------

# Uncomment the following if you want to drop the ENTIRE CATALOG:
# print("\n🗄️  Dropping catalog with CASCADE...")
# try:
#     spark.sql(f"DROP CATALOG IF EXISTS {cfg.catalog} CASCADE")
#     print(f"✅ Dropped catalog: {cfg.catalog}")
# except Exception as e:
#     print(f"❌ Error dropping catalog: {e}")

print("\n⚠️  Catalog NOT dropped (only schema was dropped)")
print(f"   To drop entire catalog, uncomment code in this cell")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify Cleanup

# COMMAND ----------

print("\n✅ CLEANUP COMPLETE!")
print("=" * 70)
print("Verifying removal...")

# Check schema
try:
    schemas = spark.sql(f"SHOW SCHEMAS IN {cfg.catalog} LIKE '{cfg.schema}'").collect()
    if len(schemas) == 0:
        print(f"✅ Schema '{cfg.schema}' removed from catalog '{cfg.catalog}'")
    else:
        print(f"⚠️  Schema '{cfg.schema}' still exists")
except Exception as e:
    print(f"✅ Schema '{cfg.schema}' removed (or catalog doesn't exist)")

print("\n🎯 Ready for fresh deployment with healthcare payer data!")
print(f"\n📋 Next steps:")
print(f"   1. Run: ./deploy.sh dev")
print(f"   2. Or manually run setup notebooks 01-09")

