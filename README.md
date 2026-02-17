# Pocketsmith MCP Server

A comprehensive [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for the [Pocketsmith](https://pocketsmith.com) personal finance API. Transform your AI assistant into a powerful financial management tool with access to accounts, budgets, transactions, and more.

[![PyPI version](https://badge.fury.io/py/pocketsmith-mcp.svg)](https://badge.fury.io/py/pocketsmith-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### 💰 Account Management
- View all account balances (checking, savings, credit cards, investments)
- Get detailed account information with transaction history
- Track net worth across multiple accounts

### 📊 Budget & Analysis
- Get budget summaries for any time period
- Analyze per-category spending vs. budgets
- View spending trends across categories
- Compare actual vs. forecasted amounts

### 💳 Transaction Management
- List, search, and filter transactions
- Create new transactions (log cash purchases, manual entries)
- Update transaction details (categorize, add notes, set labels)
- Delete duplicate or incorrect transactions
- Filter by account, category, date range, or review status

### 📁 Category Management
- List all categories with hierarchical structure
- Create new categories and subcategories
- Set up automatic categorization rules
- Organize spending into custom categories

### 🔄 Recurring Transactions
- View upcoming bills and recurring expenses
- Create recurring events (rent, subscriptions, paychecks)
- Forecast future cash flow
- Manage budget scenarios

### 🏷️ Labels & Organization
- List and manage transaction labels
- Tag transactions for easy filtering
- Track tax-deductible expenses, business spending, etc.

## 📦 Installation

### Quick Start with uvx (Recommended)

The fastest way to try it out:

```bash
uvx pocketsmith-mcp
```

### Install via pip

```bash
pip install pocketsmith-mcp
```

### Install from source

```bash
git clone https://github.com/dannyshaw/pocketsmith-mcp.git
cd pocketsmith-mcp
pip install -e .
```

## 🔑 Configuration

### Get Your API Key

1. Log in to [Pocketsmith](https://pocketsmith.com)
2. Go to **Settings → API & Developers**
3. Click **Generate New API Key**
4. Copy your API key

⚠️ **Security:** Treat your API key like a password. It has full access to your financial data.

### Set Environment Variable

```bash
export POCKETSMITH_API_KEY=your_api_key_here
```

Or create a `.env` file:

```bash
echo "POCKETSMITH_API_KEY=your_api_key_here" > .env
```

## 🚀 Usage

### With Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "pocketsmith": {
      "command": "uvx",
      "args": ["pocketsmith-mcp"],
      "env": {
        "POCKETSMITH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### With Claude Code

Add to `~/.claude/claude_desktop_config.json`:

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

### Standalone

Run the server directly:

```bash
pocketsmith-mcp
```

## 💬 Example Conversations

Once configured, you can ask your AI assistant:

### Account & Budget Queries
- *"What are my account balances?"*
- *"Show me my credit card balance"*
- *"Am I over budget this month?"*
- *"What's my spending trend for groceries over the last 3 months?"*

### Transaction Management
- *"List transactions from my checking account this week"*
- *"Log a $50 cash purchase at the grocery store"*
- *"Categorize that Amazon transaction as Household"*
- *"Delete transaction #12345"*

### Bills & Recurring Expenses
- *"What bills are coming up this month?"*
- *"Create a recurring monthly rent payment of $2000"*
- *"Show me all my subscriptions"*

### Categories & Organization
- *"Create a new category called 'Pet Expenses'"*
- *"Show me all transactions in the Dining Out category"*
- *"Set up a rule to auto-categorize Starbucks as Coffee"*

## 🛠️ Available Tools (23 total)

### Account Tools
| Tool | Description |
|------|-------------|
| `pocketsmith_list_accounts` | List all accounts with balances |
| `pocketsmith_get_account` | Get detailed account information |
| `pocketsmith_list_transaction_accounts` | List transaction accounts with details |

### Budget & Analysis Tools
| Tool | Description |
|------|-------------|
| `pocketsmith_get_budget_summary` | Get budget summary for a date range |
| `pocketsmith_list_budget` | Per-category budget analysis |
| `pocketsmith_get_trend_analysis` | Spending trends across categories |

### Transaction Tools
| Tool | Description |
|------|-------------|
| `pocketsmith_list_transactions` | List transactions with filters |
| `pocketsmith_list_transactions_by_account` | Filter transactions by account |
| `pocketsmith_list_transactions_by_category` | Filter transactions by category |
| `pocketsmith_get_transaction` | Get transaction details |
| `pocketsmith_create_transaction` | Create new transaction |
| `pocketsmith_update_transaction` | Update transaction details |
| `pocketsmith_delete_transaction` | Delete a transaction |
| `pocketsmith_search_transactions` | Search by keyword |
| `pocketsmith_categorize_transaction` | Quick categorization |

### Category Tools
| Tool | Description |
|------|-------------|
| `pocketsmith_list_categories` | List all categories |
| `pocketsmith_create_category` | Create new category |
| `pocketsmith_list_category_rules` | List auto-categorization rules |
| `pocketsmith_create_category_rule` | Create categorization rule |

### Event Tools (Recurring Transactions)
| Tool | Description |
|------|-------------|
| `pocketsmith_list_events` | List recurring transactions |
| `pocketsmith_create_event` | Create recurring transaction |

### Other Tools
| Tool | Description |
|------|-------------|
| `pocketsmith_list_labels` | List all transaction labels |
| `pocketsmith_get_status` | Check connection status |

## 🔒 Security

### This Server Can
- ✅ Read all your financial data (transactions, accounts, balances)
- ✅ Create, update, and delete transactions
- ✅ Modify categories and create rules
- ✅ Access budget and forecast data

### Security Best Practices
- ✅ Store API keys in environment variables (never in code)
- ✅ Use different API keys for development vs. production
- ✅ Rotate API keys periodically
- ✅ Only use with trusted AI assistants on secure machines
- ❌ Never commit API keys to version control
- ❌ Never share API keys publicly

See [SECURITY.md](SECURITY.md) for detailed security information.

## 📊 API Coverage

**20 out of 44 Pocketsmith API endpoints (45%)**

Focused on the most useful endpoints for personal finance management:
- ✅ User & account management
- ✅ Transaction CRUD operations
- ✅ Budget & trend analysis
- ✅ Category management
- ✅ Recurring events/bills
- ✅ Labels & organization

## 🧪 Development

### Setup

```bash
# Clone repository
git clone https://github.com/dannyshaw/pocketsmith-mcp.git
cd pocketsmith-mcp

# Install dependencies
uv sync

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/pocketsmith_mcp

# Lint and format
ruff check .
ruff format .

# Type check
mypy src
```

### Testing

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_client.py -v

# Run with coverage report
pytest --cov=src/pocketsmith_mcp --cov-report=html
```

### Project Structure

```
pocketsmith-mcp/
├── src/pocketsmith_mcp/
│   ├── __init__.py      # Package initialization
│   ├── client.py        # Pocketsmith API client
│   ├── config.py        # Configuration settings
│   └── server.py        # MCP server implementation
├── tests/
│   ├── conftest.py      # Test fixtures
│   └── test_client.py   # Client tests
├── pyproject.toml       # Project configuration
├── README.md            # This file
└── SECURITY.md          # Security documentation
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io)
- Powered by the [Pocketsmith API](https://developers.pocketsmith.com)
- Designed for use with [Claude](https://claude.ai)

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/dannyshaw/pocketsmith-mcp/issues)
- **Security:** See [SECURITY.md](SECURITY.md)
- **Discussions:** [GitHub Discussions](https://github.com/dannyshaw/pocketsmith-mcp/discussions)

## 🗺️ Roadmap

Future enhancements:
- [ ] Attachment management
- [ ] Institution connections management
- [ ] Budget calendar export
- [ ] Spending analytics and insights
- [ ] Multi-currency support enhancements
- [ ] Batch transaction operations

---

Made with ❤️ for personal finance management
