# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-17

### Added

#### Core Features
- Initial release of Pocketsmith MCP server
- Comprehensive API client with 20 out of 44 Pocketsmith endpoints (45% coverage)
- Full Pydantic model validation for all data structures
- MCP server implementation with 23 tools

#### Account Management
- `pocketsmith_list_accounts` - List all accounts with balances
- `pocketsmith_get_account` - Get detailed account information
- `pocketsmith_list_transaction_accounts` - List transaction accounts

#### Budget & Analysis
- `pocketsmith_get_budget_summary` - Budget summary for date ranges
- `pocketsmith_list_budget` - Per-category budget analysis
- `pocketsmith_get_trend_analysis` - Spending trend analysis

#### Transaction Management
- `pocketsmith_list_transactions` - List with flexible filtering
- `pocketsmith_list_transactions_by_account` - Filter by account
- `pocketsmith_list_transactions_by_category` - Filter by category
- `pocketsmith_get_transaction` - Get transaction details
- `pocketsmith_create_transaction` - Create new transactions
- `pocketsmith_update_transaction` - Update existing transactions
- `pocketsmith_delete_transaction` - Delete transactions
- `pocketsmith_search_transactions` - Search by keyword
- `pocketsmith_categorize_transaction` - Quick categorization helper

#### Category Management
- `pocketsmith_list_categories` - List all categories
- `pocketsmith_create_category` - Create new categories
- `pocketsmith_list_category_rules` - List auto-categorization rules
- `pocketsmith_create_category_rule` - Create categorization rules

#### Recurring Transactions
- `pocketsmith_list_events` - List recurring transactions/bills
- `pocketsmith_create_event` - Create recurring transactions

#### Other Features
- `pocketsmith_list_labels` - List transaction labels
- `pocketsmith_get_status` - Connection status and user info

#### Security & Documentation
- Secure API key management using environment variables
- Pydantic SecretStr to prevent accidental logging
- Comprehensive security documentation (SECURITY.md)
- Security assessment completed and passed
- Detailed README with examples and usage
- MIT License

#### Testing & Quality
- 29 comprehensive unit tests (all passing)
- 88% code coverage for client
- Full type hints throughout codebase
- Ruff linting configured
- MyPy type checking configured

#### Developer Experience
- Modern Python packaging with pyproject.toml
- uv/uvx support for instant installation
- Clean separation of concerns (client, server, config)
- Comprehensive error handling
- Pagination support for large result sets

### Technical Details
- Python 3.11+ required
- Dependencies: mcp, httpx, pydantic, pydantic-settings
- MCP protocol version 1.0+
- Async/await support for MCP server

### Known Limitations
- Budget analysis returns raw JSON (no Pydantic models)
- Trend analysis returns raw JSON (no Pydantic models)
- No attachment support yet
- No institution connection management yet

[Unreleased]: https://github.com/dannyshaw/pocketsmith-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dannyshaw/pocketsmith-mcp/releases/tag/v0.1.0
