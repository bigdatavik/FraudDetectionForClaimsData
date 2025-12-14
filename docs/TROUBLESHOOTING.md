# Troubleshooting Guide

Common issues and solutions for the Fraud Detection Agent.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Configuration Problems](#configuration-problems)
3. [UC Function Errors](#uc-function-errors)
4. [Vector Search Issues](#vector-search-issues)
5. [Genie API Problems](#genie-api-problems)
6. [Agent Errors](#agent-errors)
7. [Streamlit App Issues](#streamlit-app-issues)
8. [Performance Problems](#performance-problems)

---

## Deployment Issues

### Error: Permission Denied

**Symptom**:
```
Error: User does not have CREATE CATALOG permission
```

**Solution**:
```bash
# Have workspace admin grant permissions:
# 1. Go to Admin Settings → Unity Catalog
# 2. Grant "CREATE CATALOG" to your user/group
# 3. Retry deployment
./deploy.sh dev
```

### Error: Warehouse Not Found

**Symptom**:
```
Error: SQL warehouse <id> not found
```

**Solution**:
```bash
# 1. List available warehouses
databricks sql-warehouses list

# 2. Copy correct warehouse ID
# 3. Update config.yaml
vim config.yaml

# 4. Redeploy
./deploy.sh dev
```

### Error: Vector Endpoint Missing

**Symptom**:
```
Error: Vector search endpoint 'xyz' not found
```

**Solution**:
```bash
# Create the endpoint
databricks vector-search create-endpoint \
  --endpoint-name one-env-shared-endpoint-2 \
  --endpoint-type STANDARD

# Wait for ready status (2-3 minutes)
databricks vector-search get-endpoint \
  --endpoint-name one-env-shared-endpoint-2

# Retry deployment
./deploy.sh dev
```

### Deploy Script Hangs

**Symptom**:
- Script stops at "Running setup job..."
- No progress for > 10 minutes

**Solution**:
```bash
# 1. Check job status
databricks jobs list | grep setup

# 2. Get job run details
databricks jobs runs list --job-id <job-id>

# 3. Check logs
databricks jobs runs get-output --run-id <run-id>

# 4. If failed, fix issue and rerun
./deploy.sh dev
```

---

## Configuration Problems

### Configuration File Not Found

**Symptom**:
```
FileNotFoundError: config.yaml not found
```

**Solution**:
```bash
# Create from template
cp config.yaml.template config.yaml

# Edit with your settings
vim config.yaml

# Verify
cat config.yaml
```

### Wrong Environment Loaded

**Symptom**:
- Agent uses wrong catalog/schema
- Unexpected environment in app

**Solution**:
```bash
# Check what environment is active
python -c "from shared.config import get_config; print(get_config().environment)"

# Set explicitly
export FRAUD_ENV=dev

# Or change default in config.yaml
vim config.yaml
# Change: default_environment: dev
```

### Import Error: shared.config

**Symptom**:
```
ModuleNotFoundError: No module named 'shared.config'
```

**Solution**:
```python
# In notebooks, add parent directory to path
import sys
import os
sys.path.append(os.path.abspath('..'))

# Now import works
from shared.config import get_config
```

---

## UC Function Errors

### Function Not Found

**Symptom**:
```
Error: Function 'fraud_classify' does not exist
```

**Solution**:
```sql
-- Check if function exists
SHOW FUNCTIONS IN fraud_detection_dev.claims_analysis;

-- If missing, recreate
-- Run setup notebook: 03_uc_fraud_classify.py

-- Verify
SELECT fraud_detection_dev.claims_analysis.fraud_classify('test claim');
```

### AI_QUERY Timeout

**Symptom**:
```
Error: AI_QUERY timed out after 30s
```

**Solution**:
```python
# Option 1: Retry with backoff (already implemented)
# Option 2: Increase timeout in function definition
# Edit setup/03_uc_fraud_classify.py:

AI_QUERY(
    '{cfg.llm_endpoint}',
    prompt,
    timeout => 60  # Increase from 30 to 60
)
```

### JSON Parse Error

**Symptom**:
```
Error: Invalid JSON response from AI_QUERY
```

**Solution**:
```python
# In UC function Python code, add error handling:
try:
    result_dict = json.loads(response['predictions'][0]['candidates'][0]['text'])
except (json.JSONDecodeError, KeyError) as e:
    # Return default safe value
    return {
        'is_fraud': False,
        'fraud_probability': 0.0,
        'fraud_type': 'unknown',
        'confidence': 'low',
        'key_indicators': []
    }
```

### Permission Denied on Function

**Symptom**:
```
Error: User does not have EXECUTE permission on function
```

**Solution**:
```sql
-- Grant execute permission
GRANT EXECUTE ON FUNCTION fraud_detection_dev.claims_analysis.fraud_classify 
TO `your-user@company.com`;

-- Or to service principal
GRANT EXECUTE ON FUNCTION fraud_detection_dev.claims_analysis.fraud_classify 
TO `service-principal-uuid`;
```

---

## Vector Search Issues

### Index Not Ready

**Symptom**:
```
Error: Vector index is not ready
Status: PROVISIONING
```

**Solution**:
```python
# Check index status
from databricks.vector_search.client import VectorSearchClient
vsc = VectorSearchClient()
index = vsc.get_index("fraud_detection_dev.claims_analysis.fraud_cases_index")
print(index.describe())

# Wait for status: ONLINE_TRIGGERED_UPDATE or ONLINE
# Usually takes 5-10 minutes after creation

# Force sync if stuck
index.sync()
```

### Empty Search Results

**Symptom**:
- Vector search returns 0 results
- Even for known documents

**Solution**:
```python
# 1. Check if index has data
index = vsc.get_index("fraud_detection_dev.claims_analysis.fraud_cases_index")
stats = index.describe()
print(f"Num rows: {stats.get('num_rows', 0)}")

# 2. If 0, source table is empty - run setup notebook
# setup/06_create_knowledge_base.py

# 3. Sync index
index.sync()

# 4. Retry search
```

### Vector Search Quota Exceeded

**Symptom**:
```
Error: Vector search quota exceeded
```

**Solution**:
```bash
# Contact Databricks support to increase quota
# Or reduce index size:
# - Limit number of documents
# - Use smaller embedding model
# - Share endpoint across projects
```

---

## Genie API Problems

### Genie Space Not Found

**Symptom**:
```
Error: Genie space not found
```

**Solution**:
```sql
-- Check config table
SELECT * FROM fraud_detection_dev.claims_analysis.config_table
WHERE config_key = 'genie_space_id';

-- If empty, recreate Genie Space
-- Run setup notebook: 08_create_genie_space.py

-- Verify
SELECT * FROM fraud_detection_dev.claims_analysis.config_table;
```

### Genie Query Timeout

**Symptom**:
```
Error: Genie query timed out
```

**Solution**:
```python
# Increase timeout in agent code
# In app/utils/fraud_agent.py:

def query_genie(self, question: str) -> str:
    # ...
    for _ in range(30):  # Increase from 15 to 30
        time.sleep(2)
        # ...
```

### Genie Returns Error

**Symptom**:
```
{"error": "Query failed"}
```

**Solution**:
```python
# Debug Genie response
msg = w.genie.get_message(space_id, conversation_id, message_id)
print(f"Status: {msg.status}")
print(f"Content: {msg.content}")
print(f"Error: {msg.error if hasattr(msg, 'error') else 'None'}")

# Common fixes:
# 1. Simplify question
# 2. Check table permissions
# 3. Verify warehouse running
```

---

## Agent Errors

### Agent Loops Infinitely

**Symptom**:
- Agent makes same tool call repeatedly
- Never reaches final answer

**Solution**:
```python
# Add max iterations limit (already in LangGraph)
agent = create_react_agent(
    llm,
    tools,
    messages_modifier=system_message,
    # LangGraph has default max_iterations=15
)

# Or improve system message:
system_message = SystemMessage(content="""
...
IMPORTANT: After using tools, provide FINAL ANSWER.
Do not repeat the same tool calls.
""")
```

### Tool Call Fails

**Symptom**:
```
Error in tool execution: <tool_name>
```

**Solution**:
```python
# Add error handling to tool wrapper
def classify_claim_wrapper(claim_text: str) -> str:
    try:
        result = call_uc_function("fraud_classify", {"claim_text": claim_text})
        return json.dumps(result, indent=2)
    except Exception as e:
        # Return error in JSON format
        return json.dumps({
            "error": str(e),
            "fallback": "Unable to classify claim. Manual review required."
        })
```

### Agent Gives Incomplete Answer

**Symptom**:
- Agent stops mid-analysis
- No final recommendation

**Solution**:
```python
# Improve system message to require complete answers
system_message = SystemMessage(content="""
...
Your final response MUST include:
1. Fraud determination (FRAUD / LEGITIMATE)
2. Probability score
3. Key evidence
4. Recommendation (APPROVE / DENY / INVESTIGATE)
""")
```

---

## Streamlit App Issues

### App Won't Start

**Symptom**:
```
Error: App failed to start
```

**Solution**:
```bash
# Check app status
databricks apps get fraud-detection-dev

# View logs
databricks apps logs fraud-detection-dev

# Common fixes:
# 1. Missing dependencies
pip install -r app/requirements.txt

# 2. Import errors
# Check shared.config is accessible

# 3. Redeploy
databricks apps delete fraud-detection-dev
./deploy.sh dev
```

### Page Not Loading

**Symptom**:
- Home page loads
- Other pages show error

**Solution**:
```python
# Check page file structure
ls -la app/pages/

# Files must be named: 1_name.py, 2_name.py, etc.
# Not: name.py

# Fix naming:
mv app/pages/claim_analysis.py app/pages/1_claim_analysis.py
```

### Authentication Error

**Symptom**:
```
Error: Unable to authenticate to Databricks
```

**Solution**:
```python
# In Streamlit app, use Config() pattern (not WorkspaceClient())
from databricks.sdk.core import Config

@st.cache_resource
def get_databricks_config():
    return Config()

db_cfg = get_databricks_config()
# Now use db_cfg for authentication
```

### Slow App Performance

**Symptom**:
- Page takes >5 seconds to load
- Agent calls timeout

**Solution**:
```python
# Add caching
@st.cache_resource
def get_fraud_agent(cfg):
    return FraudAgent(cfg)

@st.cache_data(ttl=3600)
def get_fraud_statistics(cfg):
    return execute_sql(cfg, "SELECT ...")

# Use cached instances
agent = get_fraud_agent(cfg)
stats = get_fraud_statistics(cfg)
```

---

## Performance Problems

### UC Function Slow (>5s)

**Cause**:
- Large prompts
- Cold start

**Solution**:
```python
# 1. Reduce prompt size
# Truncate claim text if >1000 chars
claim_text = claim_text[:1000]

# 2. Use streaming (if supported)
# 3. Pre-warm function by calling once on deploy
```

### Vector Search Slow (>1s)

**Cause**:
- Large index
- Complex query

**Solution**:
```python
# 1. Reduce num_results
results = vsc.get_index(...).similarity_search(
    query_text=query,
    num_results=3  # Reduce from 10 to 3
)

# 2. Use filters
results = vsc.get_index(...).similarity_search(
    query_text=query,
    filters={"doc_type": "case"}  # Filter before search
)
```

### Agent Takes >10s

**Cause**:
- Too many tool calls
- Slow LLM endpoint

**Solution**:
```python
# 1. Optimize system message to use fewer tools
system_message = SystemMessage(content="""
For SIMPLE claims: Use classify_claim ONLY
For COMPLEX claims: Use max 2-3 tools
""")

# 2. Use faster LLM (if available)
llm_endpoint = "databricks-llama-3-1-70b"  # Faster than Claude

# 3. Add timeout
result = agent.invoke(
    {"messages": [...]},
    config={"timeout": 10}  # 10 second timeout
)
```

---

## Getting Help

### Debug Mode

```bash
# Enable debug logging
export DATABRICKS_DEBUG=1
export FRAUD_DEBUG=1

# Run with verbose output
./deploy.sh dev 2>&1 | tee deploy.log
```

### Collect Diagnostic Info

```bash
# System info
databricks --version
python --version

# Configuration
cat config.yaml

# Resources
databricks catalogs list
databricks sql-warehouses list
databricks apps list

# Logs
databricks apps logs fraud-detection-dev > app.log
databricks jobs runs list --job-id <job-id> > job.log
```

### Contact Support

If issue persists:

1. Gather diagnostic info above
2. Check existing GitHub issues
3. Open new issue with:
   - Error message
   - Steps to reproduce
   - Configuration (sanitized)
   - Logs
   - Environment details

---

**Still stuck?** Open an issue on GitHub with full details!


