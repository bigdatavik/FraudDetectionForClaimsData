# 📝 Fraud Detection Project - Command Cheat Sheet

Quick reference for common commands you'll use frequently.

---

## 🚀 Deployment

### Deploy to Dev
```bash
./deploy_with_config.sh dev
```

### Deploy to Prod
```bash
./deploy_with_config.sh prod
```

**What happens automatically:**
- ✅ Updates notebook version/date
- ✅ Generates app.yaml
- ✅ Deploys everything

---

## 📊 Version Management

### Bump Version (When Adding Features)
```bash
python update_notebook_version.py --bump-version
```
**Result:** Version 2.1 → 2.2, date updates

### Just Update Date (Rarely Needed)
```bash
python update_notebook_version.py
```
**Result:** Date updates, version stays same

**Note:** Deployment automatically updates date, so you rarely need this!

---

## 🗑️ Cleanup

### Delete Everything (Dev Environment)
```bash
# Run the cleanup notebook
databricks bundle run setup_job --target dev --notebook-path setup/00_CLEANUP.py
```

### Delete Specific Resources
See `setup/00_CLEANUP.py` for selective cleanup options

---

## 🔧 Configuration

### Edit Config
```bash
vim config.yaml
```

### View Current Config
```bash
cat config.yaml
```

### Environment Names
- `dev` - Development environment
- `staging` - Staging environment (if configured)
- `prod` - Production environment

---

## 📦 Databricks Bundle Commands

### Deploy Only (No Version Update)
```bash
databricks bundle deploy --target dev
```
**Note:** Use `./deploy_with_config.sh` instead for automatic version updates!

### Validate Configuration
```bash
databricks bundle validate --target dev
```

### Run Setup Job
```bash
databricks bundle run setup_job --target dev
```

### Run Specific Notebook
```bash
databricks bundle run setup_job --target dev --notebook-path setup/01_create_catalog_schema.py
```

---

## 🧪 Testing

### Open Streamlit App
1. Deploy first: `./deploy_with_config.sh dev`
2. Get URL from deployment output
3. Open in browser

### Test Vector Search
```bash
# Run vector search test notebook
databricks bundle run setup_job --target dev --notebook-path setup/07_create_vector_index.py
```

### Test Genie
```bash
# Run Genie setup notebook
databricks bundle run setup_job --target dev --notebook-path setup/10_create_genie_space.py
```

---

## 📚 Documentation

- **Full README:** `README.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Deployment Guide:** `docs/DEPLOYMENT.md`
- **Versioning:** `docs/VERSIONING.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **Project Summary:** `docs/PROJECT_SUMMARY.md`

---

## 🆘 Common Issues

### "Module 'shared' not found"
**Fix:** Make sure you're in the project root directory

### "Workspace not found"
**Fix:** Check `config.yaml` - verify `workspace_host` and `profile` are correct

### "Permission denied"
**Fix:** Make scripts executable: `chmod +x deploy_with_config.sh`

### Version showing wrong year
**Fix:** Check your system clock! Should be 2024, not 2025

---

## 💡 Pro Tips

1. **Always use `./deploy_with_config.sh`** - Don't use raw `databricks bundle deploy`
2. **Bump version when adding features** - Use `--bump-version` flag
3. **Check config.yaml first** - Most issues are configuration problems
4. **Read the deployment output** - It tells you what's happening
5. **Bookmark this cheat sheet** - Save time looking up commands!

---

**Need more details?** Check the full documentation in `docs/` or run commands with `--help`:

```bash
python update_notebook_version.py --help
databricks bundle --help
```

