# Configuration Reference

Complete reference for all configuration options in `config.yaml`.

## File Structure

```yaml
default_environment: <env_name>

environments:
  <env_name>:
    # Environment-specific settings
    
common:
  # Shared settings across all environments
```

## Top-Level Settings

### default_environment

**Type**: `string`  
**Required**: Yes  
**Default**: `dev`

The environment to use when no `FRAUD_ENV` environment variable is set.

```yaml
default_environment: dev
```

## Environment Settings

Each environment (dev/staging/prod) can have these settings:

### workspace_host

**Type**: `string`  
**Required**: Yes

Your Databricks workspace URL.

```yaml
workspace_host: "https://eastus2.azuredatabricks.net"
```

**How to find**: Copy from browser address bar when in your workspace.

### profile

**Type**: `string`  
**Required**: No  
**Default**: `DEFAULT`

Databricks CLI profile name to use for authentication.

```yaml
profile: "DEFAULT"
```

**How to configure**: Run `databricks configure --profile STAGING`

### catalog

**Type**: `string`  
**Required**: Yes

Unity Catalog name for this environment.

```yaml
catalog: "fraud_detection_dev"
```

**Naming convention**: `<project>_<environment>`

### schema

**Type**: `string`  
**Required**: Yes

Schema name within the catalog.

```yaml
schema: "claims_analysis"
```

**Note**: Same schema name can be used across environments (different catalogs).

### warehouse_id

**Type**: `string`  
**Required**: Yes

SQL Warehouse ID for executing queries.

```yaml
warehouse_id: "148ccb90800933a1"
```

**How to find**:
1. Go to SQL → Warehouses in Databricks
2. Click your warehouse
3. Copy ID from URL or details page

### vector_endpoint

**Type**: `string`  
**Required**: Yes

Vector Search endpoint name.

```yaml
vector_endpoint: "one-env-shared-endpoint-2"
```

**How to create**:
```bash
databricks vector-search create-endpoint \
  --endpoint-name your-endpoint \
  --endpoint-type STANDARD
```

### llm_endpoint

**Type**: `string`  
**Required**: Yes

LLM endpoint for AI functions and agent.

```yaml
llm_endpoint: "databricks-claude-sonnet-4"
```

**Options**:
- `databricks-claude-sonnet-4` (recommended)
- `databricks-meta-llama-3-1-405b-instruct`
- Any custom model serving endpoint

### app_name

**Type**: `string`  
**Required**: Yes

Streamlit app name (must be unique in workspace).

```yaml
app_name: "fraud-detection-dev"
```

**Rules**:
- Lowercase only
- Use hyphens (not underscores)
- Must be unique per workspace
- Max 64 characters

## Common Settings

Settings shared across all environments:

### spark_version

**Type**: `string`  
**Required**: Yes  
**Default**: `16.4.x-scala2.12`

Databricks Runtime version for job clusters.

```yaml
spark_version: "16.4.x-scala2.12"
```

**Recommendation**: Use latest LTS runtime for production.

### node_type

**Type**: `string`  
**Required**: Yes

VM type for job clusters.

```yaml
node_type: "Standard_DS3_v2"
```

**Options** (Azure):
- `Standard_DS3_v2` - 4 cores, 14GB (dev)
- `Standard_DS4_v2` - 8 cores, 28GB (prod)
- `Standard_DS5_v2` - 16 cores, 56GB (large)

### num_workers

**Type**: `integer`  
**Required**: Yes

Number of worker nodes for job clusters.

```yaml
num_workers: 2
```

**Recommendation**:
- Dev: 1-2 workers
- Staging: 2-4 workers
- Prod: 4+ workers or autoscaling

### num_claims

**Type**: `integer`  
**Required**: Yes

Number of synthetic claims to generate.

```yaml
num_claims: 1000
```

**Note**: Only used in setup. Real data would replace this.

### fraud_rate

**Type**: `float`  
**Required**: Yes

Percentage of claims that are fraudulent (0-1).

```yaml
fraud_rate: 0.08  # 8%
```

**Realistic range**: 0.05 - 0.15 (5-15%)

### genie_space_display_name

**Type**: `string`  
**Required**: Yes

Display name for Genie Space.

```yaml
genie_space_display_name: "Fraud Detection Analytics"
```

### genie_space_description

**Type**: `string`  
**Required**: Yes

Description of Genie Space purpose.

```yaml
genie_space_description: "Query fraud claims data and trends"
```

### embedding_model

**Type**: `string`  
**Required**: Yes

Embedding model for Vector Search.

```yaml
embedding_model: "databricks-gte-large-en"
```

**Options**:
- `databricks-gte-large-en` (recommended)
- `databricks-bge-large-en`
- Custom embedding endpoints

### sync_type

**Type**: `string`  
**Required**: Yes

Vector index sync strategy.

```yaml
sync_type: "TRIGGERED"
```

**Options**:
- `TRIGGERED` - Manual sync
- `CONTINUOUS` - Auto sync on data changes

## Computed Properties

These are computed by `shared/config.py`:

### volume

Derived from catalog and schema:
```python
cfg.volume = "fraud_knowledge_docs"  # Fixed name for knowledge base documents
```

### volume_path

Full path to volume:
```python
cfg.volume_path = f"/Volumes/{catalog}/{schema}/fraud_knowledge_docs"
# Example: /Volumes/fraud_detection_dev/claims_analysis/fraud_knowledge_docs
```

### claims_table

Full table name:
```python
cfg.claims_table = f"{catalog}.{schema}.claims_fraud"
```

### knowledge_table

Knowledge base table:
```python
cfg.knowledge_table = f"{catalog}.{schema}.fraud_knowledge_base"
```

### vector_index

Full vector index name:
```python
cfg.vector_index = f"{catalog}.{schema}.fraud_cases_index"
```

### config_table

Configuration storage table:
```python
cfg.config_table = f"{catalog}.{schema}.config_table"
```

## Example Configurations

### Minimal Dev Config

```yaml
default_environment: dev

environments:
  dev:
    workspace_host: "https://your-workspace.azuredatabricks.net"
    catalog: "fraud_dev"
    schema: "claims"
    warehouse_id: "abc123"
    vector_endpoint: "my-endpoint"
    llm_endpoint: "databricks-claude-sonnet-4"
    app_name: "fraud-dev"

common:
  spark_version: "16.4.x-scala2.12"
  node_type: "Standard_DS3_v2"
  num_workers: 2
  num_claims: 100
  fraud_rate: 0.08
  genie_space_display_name: "Fraud Analytics"
  genie_space_description: "Fraud data queries"
  embedding_model: "databricks-gte-large-en"
  sync_type: "TRIGGERED"
```

### Production Config

```yaml
default_environment: prod

environments:
  prod:
    workspace_host: "https://prod-workspace.azuredatabricks.net"
    profile: "PROD"
    catalog: "fraud_detection_prod"
    schema: "claims_analysis"
    warehouse_id: "prod-warehouse-123"
    vector_endpoint: "prod-vector-endpoint"
    llm_endpoint: "databricks-claude-sonnet-4"
    app_name: "fraud-detection-prod"

common:
  spark_version: "16.4.x-scala2.12"
  node_type: "Standard_DS5_v2"
  num_workers: 8
  num_claims: 100000  # For testing
  fraud_rate: 0.08
  genie_space_display_name: "Fraud Detection Analytics - Production"
  genie_space_description: "Production fraud claims analytics"
  embedding_model: "databricks-gte-large-en"
  sync_type: "CONTINUOUS"
```

## Environment Variables

Override settings via environment variables:

```bash
# Select environment
export FRAUD_ENV=staging

# Override specific settings (optional)
export FRAUD_CATALOG=custom_catalog
export FRAUD_WAREHOUSE=custom_warehouse

# Run deployment
./deploy.sh staging
```

## Validation

The `shared/config.py` module validates configuration on load:

```python
from shared.config import get_config

cfg = get_config()
# Raises error if:
# - Missing required fields
# - Invalid warehouse_id
# - Catalog name invalid
# - LLM endpoint not available
```

## Security Best Practices

### DO NOT commit config.yaml

```bash
# .gitignore includes:
config.yaml

# Only commit:
config.yaml.template
```

### Use Service Principal

For production, configure with service principal:

```yaml
environments:
  prod:
    # ... other settings ...
    service_principal_id: "12345678-1234-1234-1234-123456789012"
```

### Rotate Secrets

```bash
# Update Databricks token regularly
databricks configure --profile PROD

# Update config.yaml if needed
```

## Troubleshooting

### Configuration not loading

```python
# Debug configuration loading
from shared.config import get_config
cfg = get_config(debug=True)
```

### Wrong environment selected

```bash
# Explicitly set environment
export FRAUD_ENV=dev
python -c "from shared.config import get_config; print(get_config().environment)"
```

### Missing configuration values

```python
# Check what's loaded
from shared.config import get_config, print_config
cfg = get_config()
print_config(cfg)
```

---

**See also**:
- [Deployment Guide](DEPLOYMENT.md)
- [Architecture](ARCHITECTURE.md)


