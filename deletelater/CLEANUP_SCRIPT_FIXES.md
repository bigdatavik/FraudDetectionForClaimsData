# Cleanup Script Fixes - December 13, 2024

## Issues Found

1. **jq parsing error**: Script tried to use `jq` which wasn't available
2. **Wrong bundle path**: Script didn't use `/Workspace/` prefix for bundle cleanup
3. **Incorrect config parsing**: Used `grep` instead of proper YAML parsing
4. **Missing user detection**: Didn't dynamically get the Databricks user email
5. **Notebook execution complexity**: Tried to run cleanup notebook which added unnecessary complexity

## Fixes Applied

### 1. Config Loading (Lines 26-41)
**Before:** Used `grep` to parse YAML  
**After:** Uses Python with `yaml.safe_load()` for proper parsing

```bash
eval $(python3 -c "
import yaml
try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    env = config['environments']['$ENVIRONMENT']
    print(f\"PROFILE='{env['profile']}'\")
    print(f\"CATALOG='{env['catalog']}'\")
    print(f\"APP_NAME='{env['app_name']}'\")
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
")
```

### 2. User Email Detection (Lines 49-62)
**Before:** Read from config file (static)  
**After:** Dynamically retrieves from Databricks CLI

```bash
USER_EMAIL=$(databricks current-user me --profile ${PROFILE} --output json 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin)['userName'])")
```

### 3. App Deletion (Lines 93-98)
**Before:** `${APP_NAME}-${ENVIRONMENT}`  
**After:** `${APP_NAME}` (already includes environment from config.yaml)

### 4. Catalog Deletion (Lines 100-118)
**Before:** Tried to run cleanup notebook with complex job submission  
**After:** Simple `databricks catalogs delete` command

```bash
databricks catalogs delete "${CATALOG}" --force --profile ${PROFILE}
```

**Benefits:**
- ✅ Much faster (no cluster spinup)
- ✅ Simpler (no notebook import/run)
- ✅ CASCADE deletion (removes all schemas, tables, functions, volumes)
- ✅ Cleaner error handling

### 5. Bundle Path Cleanup (Lines 128-135)
**Before:** `/Users/${USER_EMAIL}/.bundle/...`  
**After:** `/Workspace/Users/${USER_EMAIL}/.bundle/...`

Fixed the path to use the correct `/Workspace/` prefix.

### 6. Job Detection (Lines 137-167)
**Before:** Used `jq` to parse JSON (not available)  
**After:** Uses Python to parse job list

```bash
JOB_IDS=$(python3 -c "
from databricks.sdk import WorkspaceClient
try:
    w = WorkspaceClient(profile='$PROFILE')
    jobs = w.jobs.list()
    for job in jobs:
        if job.settings and job.settings.name == 'fraud_detection_setup_${ENVIRONMENT}':
            print(job.job_id)
except Exception as e:
    pass
")
```

Wait, this still uses databricks-sdk which isn't installed. Let me fix this too.

## Current Status

✅ **Working:**
- Config loading from YAML
- User detection via CLI
- App deletion
- Catalog deletion (CASCADE)
- Bundle path cleanup
- Local .databricks/ cleanup

⚠️ **Needs Fix:**
- Job detection (uses databricks-sdk)

## Testing Results

```bash
./cleanup_all.sh dev --skip-confirmation
```

**Output:**
- ✅ App: Already deleted
- ✅ Catalog: Deleted successfully (fraud_detection_dev)
- ✅ Local state: Cleaned
- ✅ Remote files: Already deleted  
- ⚠️ Job detection: Needs databricks-sdk

## Recommendation

Either:
1. Install `databricks-sdk` in system Python: `pip3 install databricks-sdk`
2. OR: Use Databricks CLI for job listing (better for portability)

## Next Steps

- [ ] Fix job detection to use CLI instead of SDK
- [ ] Test complete cleanup cycle
- [ ] Test fresh deployment after cleanup
