# Pocketsmith MCP Server

A standalone [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for interacting with the [Pocketsmith](https://pocketsmith.com) personal finance API.

## Features

- **Transaction Management**: List, search, view, and update transactions
- **Category Management**: List categories and create auto-categorization rules
- **Amazon Order Splitting**: Automatically categorize Amazon purchases by product type
- **Full API Coverage**: Access to users, transactions, categories, and category rules

## Installation

### Using uv (recommended)

```bash
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

## Configuration

Set your Pocketsmith API key as an environment variable:

```bash
export POCKETSMITH_API_KEY=your_api_key_here
```

You can also optionally set a custom base URL:

```bash
export POCKETSMITH_BASE_URL=https://api.pocketsmith.com/v2
```

### Getting an API Key

1. Log in to [Pocketsmith](https://pocketsmith.com)
2. Go to Settings > API & Developers
3. Generate a new API key

## Usage

### Running the Server Directly

```bash
pocketsmith-mcp
```

### Usage with Claude Desktop

Add to your Claude Desktop MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

### Usage with Claude Code

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

### Transaction Management

| Tool | Description |
|------|-------------|
| `pocketsmith_list_transactions` | List transactions with optional filters (date range, needs review, uncategorized, search, type) |
| `pocketsmith_get_transaction` | Get details of a specific transaction by ID |
| `pocketsmith_update_transaction` | Update a transaction's category, payee, note, labels, or review status |
| `pocketsmith_search_transactions` | Search transactions by keyword (payee, category, notes) |
| `pocketsmith_categorize_transaction` | Categorize a transaction by setting its category |

### Category Management

| Tool | Description |
|------|-------------|
| `pocketsmith_list_categories` | List all categories (returns flat list with full paths) |
| `pocketsmith_create_category_rule` | Create a rule to automatically categorize future transactions |

### Amazon Order Integration

| Tool | Description |
|------|-------------|
| `pocketsmith_split_amazon_order` | Preview how an Amazon order would be split into categorized items |
| `pocketsmith_add_split_note` | Add Amazon split details as a note to an existing transaction |
| `pocketsmith_split_transaction` | Split an Amazon transaction into multiple categorized transactions |

### Connection

| Tool | Description |
|------|-------------|
| `pocketsmith_get_status` | Get connection status and authenticated user info |

## Development

### Setup

```bash
# Install dependencies
uv sync

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/pocketsmith_mcp --cov-report=html

# Lint
ruff check .

# Format
ruff format .

# Type check
mypy src
```

### Project Structure

```
pocketsmith-mcp/
├── src/pocketsmith_mcp/
│   ├── __init__.py          # Package initialization
│   ├── amazon_models.py     # Amazon order Pydantic models
│   ├── amazon_split.py      # Amazon order splitting logic
│   ├── client.py            # Pocketsmith API client
│   ├── config.py            # Configuration settings
│   └── server.py            # MCP server implementation
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_client.py       # Client tests
│   └── test_amazon_split.py # Amazon split tests
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_client.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/pocketsmith_mcp --cov-report=term-missing
```

## Amazon Order Categorization

The MCP server includes intelligent categorization for Amazon orders based on product names. It uses a keyword-mapping system to assign categories and confidence scores.

### Supported Categories

- **Kids Activities**: Toys, games, puzzles, LEGO, dolls
- **Gym Membership**: Protein, supplements, workout gear, yoga equipment
- **Personal Care**: Vitamins, supplements, personal care items
- **Medical**: Medicine, first aid, health supplies
- **Electronic Devices**: Headphones, chargers, cables, USB, adapters
- **Household**: Containers, cleaners, storage, kitchen items
- **Home Improvement**: Lighting, switches, power outlets, shelves
- **Clothing**: Shoes, shirts, accessories
- **Media**: Books, Kindle, audio content
- **Automotive**: Car accessories, tires
- **Camping**: Tents, sleeping bags, outdoor gear
- **Recreation**: Drones, RC toys, hobbies
- **Groceries**: Food items, spices, beverages

### Category Mapping

The `PRODUCT_CATEGORY_MAPPING` in `amazon_split.py` defines keyword-to-category mappings with confidence weights. You can customize this for your own category IDs by modifying the mapping.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
