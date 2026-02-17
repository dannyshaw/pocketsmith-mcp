# Deployment Guide - Pocketsmith MCP Server

## Pre-Deployment Checklist

### ✅ Security Review
- [x] No hardcoded secrets or API keys
- [x] `.gitignore` includes `.env` and sensitive files
- [x] Dependencies from trusted sources only
- [x] Input validation implemented
- [x] Error handling implemented
- [x] Security documentation (SECURITY.md) created

### ✅ Code Quality
- [x] All tests passing (29/29)
- [x] Code coverage ≥ 88%
- [x] Type hints throughout
- [x] Linting passes (ruff)
- [x] No critical security vulnerabilities

### ✅ Documentation
- [x] README.md updated with all features
- [x] SECURITY.md created
- [x] LICENSE file present (MIT)
- [x] All 23 tools documented
- [x] Example usage provided

### 📝 TODO Before Publishing
- [ ] Update `pyproject.toml` with your information:
  - [ ] Replace `dannyshaw` with your GitHub username
  - [ ] Replace author name and email
  - [ ] Verify repository URLs
- [ ] Choose a version number (follow SemVer)
- [ ] Create a CHANGELOG.md
- [ ] Test installation locally
- [ ] Create GitHub repository
- [ ] Set up GitHub Actions (optional)

## Publishing to PyPI

### Step 1: Create PyPI Account

1. Go to [PyPI](https://pypi.org/account/register/)
2. Create an account and verify your email
3. Enable 2FA (highly recommended)

### Step 2: Generate API Token

1. Go to [Account Settings → API tokens](https://pypi.org/manage/account/#api-tokens)
2. Click "Add API token"
3. Name: `pocketsmith-mcp-upload`
4. Scope: "Entire account" (or specific project after first upload)
5. **Save the token securely** - you'll only see it once!

### Step 3: Configure uv/pip

Store your PyPI token:

```bash
# Using uv (recommended)
export UV_PUBLISH_TOKEN=pypi-your-token-here

# Or using pip (in ~/.pypirc)
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-your-token-here
EOF
chmod 600 ~/.pypirc
```

### Step 4: Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build with uv
uv build

# Or build with pip
python -m build
```

This creates:
- `dist/pocketsmith_mcp-0.1.0-py3-none-any.whl` (wheel)
- `dist/pocketsmith-mcp-0.1.0.tar.gz` (source)

### Step 5: Test with TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI
uv publish --index-url https://test.pypi.org/legacy/

# Test installation
pip install --index-url https://test.pypi.org/simple/ pocketsmith-mcp

# Test it works
pocketsmith-mcp --help
```

### Step 6: Publish to PyPI

```bash
# Upload to PyPI
uv publish

# Or with twine
twine upload dist/*
```

### Step 7: Verify Publication

1. Visit https://pypi.org/project/pocketsmith-mcp/
2. Check the project page displays correctly
3. Test installation:

```bash
pip install pocketsmith-mcp
pocketsmith-mcp --help
```

## Making it Available via uvx

Once published to PyPI, users can immediately use it with `uvx`:

```bash
# Users can run it directly
uvx pocketsmith-mcp

# Or install it
uv pip install pocketsmith-mcp
```

**No additional steps needed!** `uvx` automatically fetches from PyPI.

## Post-Publication Steps

### 1. Create GitHub Release

```bash
# Tag the release
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Create release on GitHub
gh release create v0.1.0 \
  --title "v0.1.0 - Initial Release" \
  --notes "See CHANGELOG.md for details"
```

### 2. Update Badges in README

Update these URLs in README.md:
- PyPI version badge
- GitHub repository links
- Documentation links

### 3. Announce

- Post to MCP community Discord
- Share on social media
- Submit to MCP server directory (if available)

## Continuous Deployment (Optional)

### GitHub Actions for PyPI Publishing

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install uv
        uses: astral-sh/setup-uv@v2

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
        run: uv publish
```

Add your PyPI token to GitHub Secrets:
1. Go to repository → Settings → Secrets → Actions
2. Add secret: `PYPI_API_TOKEN` = your PyPI token

## Version Management

Follow [Semantic Versioning](https://semver.org/):

- **0.1.0** → Initial release
- **0.1.1** → Bug fixes, patches
- **0.2.0** → New features (backward compatible)
- **1.0.0** → Stable API, production-ready

Update version in:
- `pyproject.toml` → `version = "x.y.z"`
- Create git tag: `git tag vx.y.z`
- Create GitHub release
- Build and publish to PyPI

## Distribution Channels

Your MCP server will be available via:

1. **PyPI** (pip install)
   ```bash
   pip install pocketsmith-mcp
   ```

2. **uvx** (instant run)
   ```bash
   uvx pocketsmith-mcp
   ```

3. **uv** (project install)
   ```bash
   uv add pocketsmith-mcp
   ```

4. **GitHub** (source install)
   ```bash
   pip install git+https://github.com/dannyshaw/pocketsmith-mcp.git
   ```

## Monitoring

After publication:

- Monitor PyPI download stats
- Check GitHub issues for bug reports
- Review security advisories
- Keep dependencies updated

## Updating the Package

When releasing a new version:

```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"

# 4. Tag release
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags

# 5. Build and publish
uv build
uv publish

# 6. Create GitHub release
gh release create v0.2.0 --generate-notes
```

## Troubleshooting

### "Package already exists"
- Version already published
- Increment version number in `pyproject.toml`

### "Invalid authentication"
- Check PyPI token is correct
- Ensure token has proper scope
- Re-generate token if needed

### "File not found" during build
- Ensure `src/pocketsmith_mcp/__init__.py` exists
- Check `pyproject.toml` build configuration

### uvx can't find package
- Package must be on PyPI
- Wait a few minutes for PyPI to index
- Check package name matches exactly

## Security Considerations

### Signing Releases

Consider signing your releases:

```bash
# Generate GPG key
gpg --gen-key

# Sign release
git tag -s v0.1.0 -m "Release v0.1.0"

# Verify signature
git tag -v v0.1.0
```

### Supply Chain Security

- Enable GitHub's Dependabot
- Use `pip-audit` to check for vulnerabilities
- Pin dependency versions for production
- Review dependency updates before merging

## Support & Maintenance

Plan for:
- Responding to issues within 48 hours
- Security patches within 24 hours
- Feature requests reviewed monthly
- Dependency updates quarterly
- Major version every 6-12 months

---

## Quick Reference

```bash
# Local testing
uv sync
pytest -v
uv run pocketsmith-mcp

# Build
uv build

# Test publish
uv publish --index-url https://test.pypi.org/legacy/

# Publish to PyPI
uv publish

# Create release
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --generate-notes
```

Good luck with your release! 🚀
