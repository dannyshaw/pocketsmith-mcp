# Pocketsmith MCP Server

An MCP (Model Context Protocol) server for interacting with the Pocketsmith personal finance API.

## Installation

```bash
uv pip install -e packages/pocketsmith-mcp
```

## Configuration

Set your Pocketsmith API key as an environment variable:

```bash
export POCKETSMITH_API_KEY=your_api_key_here
```

## Usage with Claude Code

Add to your Claude Code MCP settings (`~/.claude/claude_desktop_config.json`):

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

## Available Tools

- `pocketsmith_list_transactions` - List transactions with optional filters
- `pocketsmith_get_transaction` - Get a specific transaction by ID
- `pocketsmith_update_transaction` - Update transaction details
- `pocketsmith_list_categories` - List all categories
- `pocketsmith_search_transactions` - Search transactions by keyword
- `pocketsmith_categorize_transaction` - Categorize a transaction
- `pocketsmith_create_category_rule` - Create automatic categorization rule
- `pocketsmith_get_status` - Get connection status
