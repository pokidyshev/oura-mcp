# Publishing to PyPI - Step by Step Guide

## 1. Create PyPI Account

Visit: https://pypi.org/account/register/

- Create a free account
- Verify your email address

## 2. Create API Token

1. Go to: https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: "oura-mcp" (or anything you like)
4. Scope: "Entire account" (or create project-specific after first upload)
5. **Copy the token immediately** (starts with `pypi-`)

## 3. Configure uv with PyPI Token

Run this command (replace YOUR_TOKEN with your actual token):

```bash
# Store PyPI token securely
export UV_PUBLISH_TOKEN="pypi-YOUR_TOKEN_HERE"

# Or create ~/.pypirc file:
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
EOF
```

## 4. Build the Package

```bash
cd /Users/niki/Developer/oura/oura-mcp
uv build
```

This creates:

- `dist/oura_mcp-0.1.0.tar.gz` (source distribution)
- `dist/oura_mcp-0.1.0-py3-none-any.whl` (wheel)

## 5. Publish to PyPI

```bash
# For test.pypi.org (recommended first):
uv publish --publish-url https://test.pypi.org/legacy/

# For real PyPI:
uv publish
```

Or with explicit token:

```bash
uv publish --token pypi-YOUR_TOKEN_HERE
```

## 6. Verify Publication

After publishing, check:

- https://pypi.org/project/oura-mcp/

## 7. Test Installation

```bash
# Test from PyPI
uvx oura-mcp

# Or install globally
uv tool install oura-mcp
```

## Current Status

✅ Repository initialized
✅ Initial commit created (09b8d8d)
✅ Package metadata configured
✅ LICENSE added (MIT)
✅ Documentation complete

⏳ **Next Steps:**

1. Create PyPI account
2. Get API token
3. Run `uv build`
4. Run `uv publish`

## Package Info

- **Name**: oura-mcp
- **Version**: 0.1.0
- **License**: MIT
- **Python**: >=3.10
- **Dependencies**: httpx, mcp[cli], python-dotenv

## Troubleshooting

**Error: Package name already taken**

- Someone else has `oura-mcp` on PyPI
- Try: `oura-mcp-server`, `mcp-oura`, etc.
- Update `name` in `pyproject.toml`

**Error: Invalid credentials**

- Make sure token starts with `pypi-`
- Token must have "upload" permission
- Check token hasn't expired

**Error: File already exists**

- You've already uploaded this version
- Bump version in `pyproject.toml` to 0.1.1, 0.2.0, etc.
- Commit and rebuild

## Important Notes

- **You cannot delete releases** - be sure before publishing!
- **Version numbers are permanent** - can't reuse them
- **Test on test.pypi.org first** (optional but recommended)
- **Package name is case-insensitive** - `oura-mcp` = `Oura-MCP`
