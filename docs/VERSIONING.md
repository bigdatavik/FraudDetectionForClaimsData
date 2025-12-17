# Automatic Notebook Versioning

## 🚀 Quick Command Reference

**Most Common Commands:**

```bash
# Bump version for new feature (use this when adding features!)
python update_notebook_version.py --bump-version

# Just update date (manual, but deployment does this automatically)
python update_notebook_version.py

# Deploy (automatically updates date)
./deploy_with_config.sh dev
```

**That's it!** For details, read below.

---

## Overview

The fraud detection project includes an automatic versioning system that updates notebook version numbers and dates during deployment.

## How It Works

### Automatic Updates During Deployment

When you run `./deploy_with_config.sh`, the deployment process automatically:

1. **Updates the date** to the latest git commit date (or current date if no git)
2. **Keeps or increments version number** based on flags
3. **Updates version fields** in the notebook metadata

### Files Updated

- `notebooks/01_fraud_agent.py` - Main agent demo notebook

### What Gets Updated

1. **Header:** `✨✨✨ VERSION X.X - CREATED [DATE] ✨✨✨`
2. **Last Updated:** `📅 Last Updated: [DATE]`
3. **Version:** `🔧 Version: X.X - WITH ARCHITECTURE DIAGRAMS`

## Manual Usage

### Update Date Only (Keep Same Version)

```bash
python update_notebook_version.py
```

This updates the date to current date but keeps the version number the same.

### Update Date to Git Commit Date

```bash
python update_notebook_version.py --use-git
```

Uses the date of the last git commit (used automatically in deployment).

### Bump Version Number

```bash
python update_notebook_version.py --bump-version
```

Increments the minor version (e.g., 2.1 → 2.2) and updates the date.

### Bump Version + Use Git Date

```bash
python update_notebook_version.py --bump-version --use-git
```

Combines both: increments version AND uses git commit date.

### Update Different Notebook

```bash
python update_notebook_version.py --notebook notebooks/another_notebook.py
```

## Integration with Deployment

The versioning script is automatically called in `deploy_with_config.sh`:

```bash
# Step 1: Update notebook version and date
python update_notebook_version.py --use-git
```

This ensures that every deployment has the correct date from the last git commit.

## Version Numbering Convention

- **Major.Minor** format (e.g., 2.1, 2.2, 3.0)
- **Minor bump (X.Y → X.Y+1):** Feature additions, updates
- **Major bump (X.Y → X+1.0):** Significant changes, architecture updates

### When to Bump Version

**Auto-increment (--bump-version):**
- New features added to notebook
- Significant code changes
- Architecture updates
- New tool integrations

**Keep same version (default):**
- Bug fixes
- Documentation updates
- Minor tweaks
- Configuration changes

## Examples

### Scenario 1: Regular Deployment (Date Update Only)

```bash
./deploy_with_config.sh dev
```

**Result:** Date updates to last git commit, version stays the same

**Before:** `VERSION 2.1 - CREATED December 14, 2024`  
**After:** `VERSION 2.1 - CREATED December 17, 2024`

### Scenario 2: New Feature Deployment (Version Bump)

```bash
# First, manually bump version
python update_notebook_version.py --bump-version --use-git

# Then deploy
./deploy_with_config.sh dev
```

**Result:** Version increments, date updates

**Before:** `VERSION 2.1 - CREATED December 14, 2024`  
**After:** `VERSION 2.2 - CREATED December 17, 2024`

### Scenario 3: Quick Testing (Current Date)

```bash
python update_notebook_version.py
```

**Result:** Uses current system date instead of git date

**Before:** `VERSION 2.1 - CREATED December 14, 2024`  
**After:** `VERSION 2.1 - CREATED [TODAY'S DATE]`

## Troubleshooting

### Script Fails During Deployment

The deployment continues even if versioning fails (warning only):

```
⚠️  WARNING: Failed to update notebook version (continuing anyway)
```

This is intentional to not block deployments due to versioning issues.

### Git Date Not Working

If `--use-git` doesn't work:
- Ensure you're in a git repository
- Ensure git is installed and accessible
- Falls back to current date automatically

### Version Pattern Not Found

Error: `Could not find version pattern in notebook`

**Solution:** Manually restore the version header format:
```python
# MAGIC # ✨✨✨ VERSION 2.1 - CREATED December 14, 2024 ✨✨✨
```

## Best Practices

1. **Let deployment handle dates:** Don't manually update dates, use `--use-git`
2. **Bump version for features:** Use `--bump-version` when adding new capabilities
3. **Commit before deploy:** Ensures git date reflects actual code changes
4. **Document version changes:** Update CHANGELOG.md for major version bumps

## Future Enhancements

Potential improvements:
- [ ] Semantic versioning (MAJOR.MINOR.PATCH)
- [ ] Git commit hash in version metadata
- [ ] Changelog auto-generation from git commits
- [ ] Version tagging in git
- [ ] Multi-notebook version sync

