# Architecture Documentation

## System Overview

The Fraud Detection Agent is a multi-layered AI system built on Databricks that combines intelligent agents, serverless AI functions, and enterprise data infrastructure.

## Core Components

### 1. LangGraph ReAct Agent

**Purpose**: Intelligent orchestration and decision-making

**Architecture**:
```
┌─────────────────────────────────┐
│   LangGraph ReAct Agent Core    │
│                                  │
│  ┌────────────────────────────┐ │
│  │   Reasoning Loop           │ │
│  │                            │ │
│  │  1. Reason (analyze claim) │ │
│  │  2. Act (call tool)        │ │
│  │  3. Observe (get result)   │ │
│  │  4. Repeat if needed       │ │
│  └────────────────────────────┘ │
│                                  │
│  LLM: Claude Sonnet 4           │
│  Pattern: ReAct                  │
│  Max iterations: 10              │
└─────────────────────────────────┘
```

**Tool Selection Strategy**:
- **Simple claims** (low complexity) → `classify_claim` only
- **Suspicious claims** (red flags detected) → `classify` + `extract_fraud_indicators`
- **Complex patterns** (multiple flags) → Add `search_fraud_cases`
- **Trend analysis** (statistical queries) → Add `query_fraud_trends`

### 2. Unity Catalog AI Functions

**Purpose**: Serverless, governed AI inference

**Functions Created**:

#### fraud_classify
```sql
CREATE OR REPLACE FUNCTION fraud_classify(claim_text STRING)
RETURNS STRUCT<
  is_fraud: BOOLEAN,
  fraud_probability: DOUBLE,
  fraud_type: STRING,
  confidence: STRING,
  key_indicators: ARRAY<STRING>
>
LANGUAGE PYTHON
AS $$
  # Uses AI_QUERY with Claude Sonnet 4
  # Returns structured classification result
$$
```

#### fraud_extract_indicators
```sql
CREATE OR REPLACE FUNCTION fraud_extract_indicators(claim_text STRING)
RETURNS STRUCT<
  red_flags: ARRAY<STRING>,
  suspicious_patterns: ARRAY<STRING>,
  affected_entities: ARRAY<STRING>,
  risk_score: INT
>
LANGUAGE PYTHON
AS $$
  # Extracts detailed fraud indicators
  # Returns structured extraction result
$$
```

#### fraud_generate_explanation
```sql
CREATE OR REPLACE FUNCTION fraud_generate_explanation(
  claim_text STRING,
  fraud_classification STRING
)
RETURNS STRING
LANGUAGE PYTHON
AS $$
  # Generates human-readable explanation
  # Suitable for investigators and auditors
$$
```

**Benefits**:
- ✅ Serverless (auto-scaling)
- ✅ Governed by Unity Catalog
- ✅ Versioned and audited
- ✅ Reusable across notebooks, apps, SQL queries
- ✅ Cost-efficient (pay per call)

### 3. Vector Search

**Purpose**: Semantic search for similar fraud cases

**Architecture**:
```
┌─────────────────────────────────────┐
│      Delta Table                    │
│  (fraud_knowledge_base)             │
│                                     │
│  - doc_id                           │
│  - doc_type (case/pattern/guide)    │
│  - title                            │
│  - content                          │
│  - chunk                            │
└──────────────┬──────────────────────┘
               │
               │ Sync (TRIGGERED)
               ▼
┌─────────────────────────────────────┐
│    Vector Search Index              │
│  (fraud_cases_index)                │
│                                     │
│  Embeddings: databricks-gte-large   │
│  Endpoint: Managed                  │
│  Distance: Cosine similarity        │
└──────────────┬──────────────────────┘
               │
               │ Query (<100ms)
               ▼
         Search Results
```

**Content Types**:
1. **Historical Cases** - Past fraud investigations
2. **Fraud Patterns** - Known schemes and tactics
3. **Investigation Guides** - Best practices

### 4. Genie API

**Purpose**: Natural language data queries

**Created Resources**:
- **Genie Space** - Created programmatically via API
- **Attached Tables** - Claims, statistics tables
- **SQL Generation** - Converts questions to SQL

**Example Flow**:
```
User: "What is the fraud rate this month?"
  ↓
Genie: SELECT AVG(CASE WHEN is_fraud...) FROM claims WHERE month = ...
  ↓
Execute SQL on warehouse
  ↓
Return results to agent
```

## Data Architecture

### Medallion Architecture

```
┌──────────────────────────────────────────┐
│           Bronze Layer                    │
│                                          │
│  claims_raw (synthetic generation)       │
│  - Raw claim text                        │
│  - Minimal validation                    │
└────────────────┬─────────────────────────┘
                 │
                 │ Transform & Classify
                 ▼
┌──────────────────────────────────────────┐
│           Silver Layer                    │
│                                          │
│  claims_fraud (processed)                │
│  - Classified claims                     │
│  - Fraud indicators extracted            │
│  - Enriched metadata                     │
└────────────────┬─────────────────────────┘
                 │
                 │ Aggregate & Curate
                 ▼
┌──────────────────────────────────────────┐
│            Gold Layer                     │
│                                          │
│  fraud_statistics (aggregated)           │
│  - KPIs and metrics                      │
│  - Fraud trends                          │
│  - Pattern analysis                      │
└──────────────────────────────────────────┘
```

### Table Schemas

**claims_fraud** (main table):
```sql
CREATE TABLE claims_fraud (
  claim_id STRING PRIMARY KEY,
  claim_text STRING,
  claim_amount DOUBLE,
  claim_type STRING,  -- auto, medical, property
  is_fraud BOOLEAN,
  fraud_type STRING,
  fraud_probability DOUBLE,
  timestamp TIMESTAMP,
  processed_at TIMESTAMP
)
```

**fraud_knowledge_base** (vector search source):
```sql
CREATE TABLE fraud_knowledge_base (
  doc_id STRING PRIMARY KEY,
  doc_type STRING,  -- case, pattern, guide
  title STRING,
  content STRING,
  chunk STRING,  -- For vector index
  metadata MAP<STRING, STRING>
)
```

**config_table** (system configuration):
```sql
CREATE TABLE config_table (
  config_key STRING PRIMARY KEY,
  config_value STRING,
  updated_at TIMESTAMP
)
-- Stores: genie_space_id, vector_index_status, etc.
```

## Agent Decision Flow

```
┌─────────────────────┐
│   Claim Received    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Agent Reasoning   │
│  "What do I know?"  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Tool 1: classify_claim         │
│  Result: HIGH RISK (0.87)       │
└──────────┬──────────────────────┘
           │
           │ Risk > 0.7?
           ▼ YES
┌─────────────────────────────────┐
│  Tool 2: extract_indicators     │
│  Result: 5 red flags found      │
└──────────┬──────────────────────┘
           │
           │ Red flags > 3?
           ▼ YES
┌─────────────────────────────────┐
│  Tool 3: search_fraud_cases     │
│  Result: 3 similar cases        │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   Final Assessment              │
│   - DENY claim                  │
│   - Probability: 0.87           │
│   - Evidence: [list]            │
│   - Similar cases: [links]      │
└─────────────────────────────────┘
```

## Security & Governance

### Unity Catalog Integration

**Governance Features**:
- ✅ **Row-Level Security** - Filter claims by user access
- ✅ **Column Masking** - Hide sensitive PII
- ✅ **Audit Logs** - Track all function calls
- ✅ **Lineage** - Trace data flow
- ✅ **Access Control** - Grants per catalog/schema

**Service Principal Permissions**:
```sql
-- Catalog access
GRANT USE CATALOG ON fraud_detection_dev TO `service-principal-id`;

-- Schema access
GRANT USE SCHEMA, SELECT, MODIFY ON fraud_detection_dev.claims_analysis 
TO `service-principal-id`;

-- Warehouse access
databricks permissions update sql/warehouses/<warehouse-id> 
  --service-principal <sp-id> --permission-level CAN_USE
```

## Deployment Architecture

### Databricks Asset Bundles

**Structure**:
```yaml
bundle:
  name: fraud-detection
  
resources:
  jobs:
    setup_job:
      name: fraud-detection-setup
      tasks:
        - task_key: create_catalog
          notebook_task:
            notebook_path: setup/01_create_catalog_schema
        # ... 8 setup notebooks
  
  apps:
    fraud_app:
      name: fraud-detection-app
      source_code_path: app/
```

**Deployment Flow**:
```
config.yaml
    ↓
deploy.sh parses config
    ↓
Generates databricks.yml dynamically
    ↓
databricks bundle validate
    ↓
databricks bundle deploy
    ↓
Run setup job (8 notebooks)
    ↓
Deploy Streamlit app
    ↓
Grant permissions
    ↓
✅ Ready!
```

## Performance Characteristics

### Latency

| Component | Latency | Notes |
|-----------|---------|-------|
| UC classify | 1-2s | Claude Sonnet 4 call |
| UC extract | 1-2s | Claude Sonnet 4 call |
| Vector Search | <100ms | Managed index |
| Genie query | 2-4s | SQL generation + exec |
| Full agent | 3-8s | Depends on tools used |

### Scalability

**Vertical Scaling**:
- UC functions: Auto-scale per endpoint
- Vector Search: Managed scaling
- SQL Warehouse: Auto-scale workers

**Horizontal Scaling**:
- Batch processing: Spark UDFs across partitions
- Multi-cluster warehouses for concurrent users
- Vector index: Distributed storage

### Cost Optimization

**Strategies**:
1. **Cache agent instances** - Reuse LLM connections
2. **Batch API calls** - Group UC function calls
3. **Serverless compute** - Pay only for execution time
4. **Smart tool selection** - Agent uses minimum tools needed
5. **Pre-computed statistics** - Cache frequent queries

## Monitoring & Observability

**Metrics to Track**:
- Agent response time
- Tool usage distribution
- Classification accuracy
- False positive rate
- System errors

**Logging**:
```python
# Every agent call logs:
{
  "claim_id": "...",
  "tools_used": ["classify", "extract"],
  "total_time": 4.2,
  "result": "FRAUD",
  "confidence": 0.87
}
```

## Extension Points

**How to Add**:

### New Tool
1. Create function in `fraud_agent.py`
2. Add Pydantic schema
3. Create Tool() instance
4. Add to tools list
5. Update agent system message

### New UC Function
1. Create setup notebook `0X_uc_new_function.py`
2. Define SQL function with LANGUAGE PYTHON
3. Add to deploy.sh setup tasks
4. Wrap in agent tool

### New Data Source
1. Create Delta table
2. Add to vector index (if searchable)
3. Expose via Genie Space
4. Create agent tool wrapper

## Best Practices

### Agent Design
- ✅ Keep tools focused and atomic
- ✅ Provide clear tool descriptions
- ✅ Use Pydantic for type safety
- ✅ Handle errors gracefully
- ✅ Log all tool invocations

### UC Functions
- ✅ Use LANGUAGE PYTHON for complex logic
- ✅ Return structured types (STRUCT)
- ✅ Version functions (v1, v2)
- ✅ Test with sample data
- ✅ Document parameters

### Configuration
- ✅ All settings in config.yaml
- ✅ Environment-specific values
- ✅ Use shared.config module everywhere
- ✅ No hardcoded values
- ✅ Validate on startup

---

**For more details, see**:
- [Deployment Guide](DEPLOYMENT.md)
- [Configuration Reference](CONFIGURATION.md)
- [Troubleshooting](TROUBLESHOOTING.md)


