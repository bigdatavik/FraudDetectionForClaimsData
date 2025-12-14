# Databricks notebook source
# MAGIC %md
# MAGIC # Chunk Fraud Knowledge Base for Vector Search
# MAGIC
# MAGIC Reads documents from volume, chunks them optimally, and creates table with Change Data Feed enabled.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Configuration

# COMMAND ----------

import sys
import os
sys.path.append(os.path.abspath('..'))
from shared.config import get_config

cfg = get_config()

VOLUME_PATH = f"/Volumes/{cfg.catalog}/{cfg.schema}/fraud_knowledge_docs"
FULL_TABLE_NAME = cfg.knowledge_base_table

print(f"Table: {FULL_TABLE_NAME}")
print(f"Volume: {VOLUME_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Drop and Recreate Table with CDF

# COMMAND ----------

# Drop and recreate for clean slate
print(f"🔄 Dropping and recreating table for clean slate")
try:
    spark.sql(f"DROP TABLE IF EXISTS {FULL_TABLE_NAME}")
    print(f"✅ Dropped existing table: {FULL_TABLE_NAME}")
except Exception as e:
    print(f"ℹ️  No existing table to drop: {e}")

# Create table with proper schema for chunked documents and CDF enabled
spark.sql(f"""
    CREATE TABLE {FULL_TABLE_NAME} (
        doc_id STRING,
        doc_type STRING,
        title STRING,
        content STRING,
        keywords ARRAY<STRING>,
        chunk_index INT,
        total_chunks INT,
        char_count INT,
        created_at TIMESTAMP,
        file_name STRING
    )
    USING DELTA
    TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"✅ Table created with Change Data Feed enabled: {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chunking Logic

# COMMAND ----------

from datetime import datetime
import re

def extract_keywords(text, max_keywords=10):
    """Extract keywords from text"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
                  'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 
                  'these', 'those', 'not', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
                  'fraud', 'claim', 'claims', 'detection', 'pattern', 'patterns'}
    
    # Extract words (4+ letters)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and get top keywords
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
    return [word for word, freq in keywords]

def split_into_sections(content):
    """Split document into logical sections"""
    sections = []
    current_section = ""
    current_title = ""
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this is a section header (all caps, short line, or numbered)
        is_header = (
            (stripped.isupper() and len(stripped) < 80 and len(stripped) > 5) or
            (re.match(r'^\d+\.', stripped)) or
            (re.match(r'^[A-Z][^.!?]*:$', stripped))
        )
        
        if is_header and current_section:
            # Save previous section
            sections.append({'title': current_title, 'content': current_section.strip()})
            current_section = line + '\n'
            current_title = stripped
        else:
            current_section += line + '\n'
    
    # Add final section
    if current_section:
        sections.append({'title': current_title, 'content': current_section.strip()})
    
    return sections

def chunk_document(file_path, min_chunk_size=800, max_chunk_size=1500):
    """Read and chunk a document from volume"""
    try:
        # Read file content
        content = dbutils.fs.head(file_path, 1000000)  # Read up to 1MB
        
        # Extract metadata from content
        lines = content.split('\n')
        doc_id = ""
        doc_type = ""
        title = ""
        main_content = []
        
        for i, line in enumerate(lines):
            if line.startswith("Document ID:"):
                doc_id = line.replace("Document ID:", "").strip()
            elif line.startswith("Type:"):
                doc_type = line.replace("Type:", "").strip()
            elif line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif i > 4:  # Skip metadata lines
                main_content.append(line)
        
        content_text = '\n'.join(main_content).strip()
        file_name = file_path.split('/')[-1]
        
        # Split into sections
        sections = split_into_sections(content_text)
        
        chunks = []
        for section in sections:
            section_content = section['content']
            
            # If section is small enough, keep as single chunk
            if len(section_content) <= max_chunk_size:
                chunks.append(section_content)
            else:
                # Split large sections by paragraphs
                paragraphs = section_content.split('\n\n')
                current_chunk = ""
                
                for para in paragraphs:
                    if len(current_chunk) + len(para) <= max_chunk_size:
                        current_chunk += para + '\n\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = para + '\n\n'
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
        
        # Create chunk records
        total_chunks = len(chunks)
        chunk_records = []
        
        for idx, chunk_content in enumerate(chunks):
            keywords = extract_keywords(chunk_content)
            
            chunk_records.append({
                'doc_id': doc_id,
                'doc_type': doc_type,
                'title': title,
                'content': chunk_content,
                'keywords': keywords,
                'chunk_index': idx,
                'total_chunks': total_chunks,
                'char_count': len(chunk_content),
                'created_at': datetime.now(),
                'file_name': file_name
            })
        
        return chunk_records
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

print("✅ Chunking functions loaded")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Process All Documents

# COMMAND ----------

# List all files in volume
files = dbutils.fs.ls(VOLUME_PATH)
print(f"Found {len(files)} files in volume")

all_chunks = []
for file_info in files:
    if file_info.path.endswith('.txt'):
        print(f"Processing: {file_info.name}")
        chunks = chunk_document(file_info.path)
        all_chunks.extend(chunks)
        print(f"  → Created {len(chunks)} chunks")

print(f"\n✅ Total chunks created: {len(all_chunks)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Insert Chunks into Table

# COMMAND ----------

from pyspark.sql.types import *

# Define schema
chunk_schema = StructType([
    StructField("doc_id", StringType(), False),
    StructField("doc_type", StringType(), False),
    StructField("title", StringType(), False),
    StructField("content", StringType(), False),
    StructField("keywords", ArrayType(StringType()), False),
    StructField("chunk_index", IntegerType(), False),
    StructField("total_chunks", IntegerType(), False),
    StructField("char_count", IntegerType(), False),
    StructField("created_at", TimestampType(), False),
    StructField("file_name", StringType(), False)
])

# Create DataFrame and write to table
if all_chunks:
    chunks_df = spark.createDataFrame(all_chunks, schema=chunk_schema)
    chunks_df.write.mode("append").saveAsTable(FULL_TABLE_NAME)
    print(f"✅ Inserted {len(all_chunks)} chunks into {FULL_TABLE_NAME}")
else:
    print("⚠️  No chunks to insert")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Table

# COMMAND ----------

print("=" * 80)
print("KNOWLEDGE BASE TABLE STATISTICS")
print("=" * 80)

stats = spark.sql(f"""
SELECT 
    COUNT(*) as total_chunks,
    COUNT(DISTINCT doc_id) as unique_docs,
    AVG(char_count) as avg_chunk_size,
    MIN(char_count) as min_chunk_size,
    MAX(char_count) as max_chunk_size
FROM {FULL_TABLE_NAME}
""").collect()[0]

print(f"Total Chunks:    {stats['total_chunks']}")
print(f"Unique Docs:     {stats['unique_docs']}")
print(f"Avg Chunk Size:  {stats['avg_chunk_size']:.0f} chars")
print(f"Min Chunk Size:  {stats['min_chunk_size']} chars")
print(f"Max Chunk Size:  {stats['max_chunk_size']} chars")
print("=" * 80)

# Show sample chunks
print("\nSample chunks:")
display(spark.sql(f"""
SELECT doc_id, title, chunk_index, total_chunks, char_count, LEFT(content, 100) as content_preview
FROM {FULL_TABLE_NAME}
LIMIT 5
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("=" * 80)
print("KNOWLEDGE BASE TABLE CREATED WITH CDF!")
print("=" * 80)
print(f"✅ Table: {FULL_TABLE_NAME}")
print(f"✅ Change Data Feed: ENABLED")
print(f"✅ Total Chunks: {len(all_chunks)}")
print("=" * 80)
print("\n📝 Next step: Run 07_create_vector_index.py to create vector search index")
print("=" * 80)


