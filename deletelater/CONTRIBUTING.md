# Contributing to Fraud Detection Agent

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs

1. Check if the bug already exists in Issues
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Databricks version, Python version)
   - Error logs if applicable

### Suggesting Features

1. Open an issue with the "enhancement" label
2. Describe the feature and use case
3. Explain why it would be valuable
4. Consider implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation
   - Test in dev environment

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add batch processing optimization"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

```bash
# Clone repository
git clone <repository>
cd FraudDetectionForClaimsData

# Copy and configure
cp config.yaml.template config.yaml
# Edit config.yaml with your settings

# Deploy to dev
./deploy.sh dev

# Test changes
# Run notebooks and app
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions focused and small

### Notebooks
- Clear markdown sections
- Reproducible cells
- Print status messages
- Handle errors gracefully

### Configuration
- All settings in `config.yaml`
- Use `shared.config` module
- No hardcoded values
- Document new settings

## Testing

Before submitting PR:

1. ✅ Test in dev environment
2. ✅ Run all setup notebooks
3. ✅ Test agent with various claims
4. ✅ Verify Streamlit app works
5. ✅ Check documentation is updated
6. ✅ Ensure no hardcoded values

## Documentation

Update documentation when:
- Adding new features
- Changing configuration
- Modifying architecture
- Adding dependencies

## Commit Messages

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance

Examples:
```
feat: add fraud explanation UC function
fix: handle empty vector search results
docs: update deployment guide
refactor: simplify agent tool creation
```

## Review Process

1. Maintainers review PRs within 2-3 days
2. Address feedback and update PR
3. Once approved, PR will be merged
4. Your contribution will be credited

## Questions?

- Open a Discussion for questions
- Tag maintainers in PRs for urgency
- Check existing Issues and Discussions first

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn
- Focus on the problem, not the person

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing! 🚀


