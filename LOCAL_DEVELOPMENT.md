# Local Development Configuration

## Running the MCP Server Locally

There are several ways to run the Pocketsmith MCP server from your local directory for development and testing.

## Option 1: Using uv run (Recommended for Development)

### Claude Desktop Config

**File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pocketsmith": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/danny/dev/repos/pocketsmith-mcp",
        "run",
        "pocketsmith-mcp"
      ],
      "env": {
        "POCKETSMITH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Claude Code Config

**File:** `~/.claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pocketsmith": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/danny/dev/repos/pocketsmith-mcp",
        "run",
        "pocketsmith-mcp"
      ],
      "env": {
        "POCKETSMITH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Benefits:**
- ✅ No installation needed
- ✅ Uses your local source code
- ✅ Changes reflected immediately
- ✅ Isolated environment with uv

---

## Option 2: Using Python Module Directly

### Claude Desktop Config

```json
{
  "mcpServers": {
    "pocketsmith": {
      "command": "python",
      "args": [
        "-m",
        "pocketsmith_mcp.server"
      ],
      "cwd": "/Users/danny/dev/repos/pocketsmith-mcp",
      "env": {
        "PYTHONPATH": "/Users/danny/dev/repos/pocketsmith-mcp/src",
        "POCKETSMITH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Benefits:**
- ✅ Direct control over Python interpreter
- ✅ Uses your local source code
- ✅ Good for debugging

---

## Option 3: Editable Install (Best for Regular Testing)

### Step 1: Install in Editable Mode

```bash
cd /Users/danny/dev/repos/pocketsmith-mcp
pip install -e .
# or with uv:
uv pip install -e .
```

### Step 2: Claude Desktop Config

```json
{
  "mcpServers": {
    "pocketsmith": {
      "command": "pocketsmith-mcp",
      "env": {
        "POCKETSMITH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Benefits:**
- ✅ Works like installed package
- ✅ Code changes reflected immediately (no reinstall needed)
- ✅ Simpler configuration
- ✅ Tests production-like behavior

---

## Option 4: Using uv pip in Virtual Environment

### Claude Desktop Config

```json
{
  "mcpServers": {
    "pocketsmith": {
      "command": "/Users/danny/dev/repos/pocketsmith-mcp/.venv/bin/python",
      "args": [
        "-m",
        "pocketsmith_mcp.server"
      ],
      "env": {
        "POCKETSMITH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Benefits:**
- ✅ Uses specific virtual environment
- ✅ Complete control over dependencies
- ✅ Isolated from system Python

---

## Testing Your Configuration

### 1. Restart Claude Desktop/Code

After changing the config file, restart Claude Desktop or Claude Code for changes to take effect.

### 2. Verify Connection

In Claude, try these commands:
- "What tools do you have access to for Pocketsmith?"
- "Can you check the Pocketsmith connection status?"

You should see all 23 Pocketsmith MCP tools available.

### 3. Test a Simple Tool

Try: "What are my Pocketsmith account balances?"

---

## Debugging

### Check Logs

**Claude Desktop logs:**
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Look for pocketsmith server startup and errors
```

**Claude Code logs:**
```bash
# Check the Claude Code output panel
# Or check ~/.claude/logs/
```

### Common Issues

#### "Command not found: pocketsmith-mcp"
- Solution: Use Option 1 (uv run) or install in editable mode first

#### "Module not found: pocketsmith_mcp"
- Solution: Check PYTHONPATH includes `/Users/danny/dev/repos/pocketsmith-mcp/src`

#### "API key not found"
- Solution: Verify POCKETSMITH_API_KEY is set in the env section

#### Changes not reflected
- Solution: Restart Claude Desktop/Code after code changes
- For Option 2/3: Changes are automatic, just restart Claude

---

## Development Workflow

### Recommended Setup

1. **Use Option 1 (uv run)** for active development
   - Changes reflected immediately
   - No installation needed
   - Clean environment

2. **Make code changes** in your editor

3. **Restart Claude** to pick up changes

4. **Test** the new functionality

5. **Run tests** to verify:
   ```bash
   pytest -v
   ```

6. **Commit** when ready:
   ```bash
   git add .
   git commit -m "Add feature X"
   git push
   ```

---

## Quick Reference

### Current Directory Structure
```
/Users/danny/dev/repos/pocketsmith-mcp/
├── src/pocketsmith_mcp/
│   ├── server.py      # MCP server entry point
│   ├── client.py      # API client
│   └── config.py      # Configuration
├── tests/
├── pyproject.toml
└── README.md
```

### Environment Variables

Required:
- `POCKETSMITH_API_KEY` - Your Pocketsmith API key

Optional:
- `POCKETSMITH_BASE_URL` - Custom API URL (default: https://api.pocketsmith.com/v2)

### Testing Commands

```bash
# Run all tests
pytest -v

# Test with coverage
pytest --cov=src/pocketsmith_mcp

# Test server starts
python -m pocketsmith_mcp.server

# Verify tools list
python -c "import asyncio; from pocketsmith_mcp.server import list_tools; asyncio.run(list_tools())"
```

---

## Production vs Development

**Development (Local):**
- Use `uv run` or editable install
- Point to local directory
- Set POCKETSMITH_API_KEY in config

**Production (Published):**
- Use `uvx pocketsmith-mcp`
- Install from PyPI
- Set POCKETSMITH_API_KEY in config

Both use the same config format, just different `command` values!
