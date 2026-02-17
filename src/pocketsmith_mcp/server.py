"""Pocketsmith MCP server."""

import json
from datetime import date
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from pocketsmith_mcp.client import (
    Account,
    Category,
    Event,
    PocketsmithClient,
    PocketsmithError,
    Transaction,
    TransactionAccount,
)

# Create the MCP server
server = Server("pocketsmith")

# Lazy-initialized client
_client: PocketsmithClient | None = None


def get_client() -> PocketsmithClient:
    """Get or create the Pocketsmith client."""
    global _client
    if _client is None:
        _client = PocketsmithClient()
    return _client


def transaction_to_dict(t: Transaction) -> dict[str, Any]:
    """Convert a transaction to a dictionary for JSON output."""
    return {
        "id": t.id,
        "date": t.date.isoformat(),
        "payee": t.payee,
        "original_payee": t.original_payee,
        "amount": t.amount,
        "type": t.type,
        "category": t.category.title if t.category else None,
        "category_id": t.category.id if t.category else None,
        "note": t.note,
        "memo": t.memo,
        "labels": t.labels,
        "needs_review": t.needs_review,
        "status": t.status,
        "account": t.transaction_account.name if t.transaction_account else None,
        "is_transfer": t.is_transfer,
    }


def category_to_dict(c: Category, include_children: bool = True) -> dict[str, Any]:
    """Convert a category to a dictionary for JSON output."""
    result = {
        "id": c.id,
        "title": c.title,
        "colour": c.colour,
        "parent_id": c.parent_id,
        "is_transfer": c.is_transfer,
        "is_bill": c.is_bill,
    }
    if include_children and c.children:
        result["children"] = [category_to_dict(child, include_children=True) for child in c.children]
    return result


def flatten_categories(categories: list[Category]) -> list[dict[str, Any]]:
    """Flatten category tree into a list with full paths."""
    result = []

    def walk(cats: list[Category], parent_path: str = ""):
        for c in cats:
            path = f"{parent_path}/{c.title}" if parent_path else c.title
            result.append({
                "id": c.id,
                "title": c.title,
                "full_path": path,
                "parent_id": c.parent_id,
                "is_transfer": c.is_transfer,
                "is_bill": c.is_bill,
            })
            if c.children:
                walk(c.children, path)

    walk(categories)
    return result


def account_to_dict(a: Account) -> dict[str, Any]:
    """Convert an account to a dictionary for JSON output."""
    return {
        "id": a.id,
        "title": a.title,
        "type": a.type,
        "currency_code": a.currency_code,
        "is_net_worth": a.is_net_worth,
        "current_balance": a.current_balance,
        "current_balance_in_base_currency": a.current_balance_in_base_currency,
        "current_balance_date": a.current_balance_date,
        "safe_balance": a.safe_balance,
        "safe_balance_in_base_currency": a.safe_balance_in_base_currency,
        "primary_account": a.primary_transaction_account.name if a.primary_transaction_account else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def event_to_dict(e: Event) -> dict[str, Any]:
    """Convert an event to a dictionary for JSON output."""
    return {
        "id": e.id,
        "date": e.date.isoformat(),
        "amount": e.amount,
        "currency_code": e.currency_code,
        "category": e.category.title if e.category else None,
        "category_id": e.category.id if e.category else None,
        "note": e.note,
        "repeat_type": e.repeat_type,
        "repeat_interval": e.repeat_interval,
        "series_id": e.series_id,
        "infinite_series": e.infinite_series,
        "scenario": e.scenario.title if e.scenario else None,
    }


def transaction_account_to_dict(ta: TransactionAccount) -> dict[str, Any]:
    """Convert a transaction account to a dictionary for JSON output."""
    return {
        "id": ta.id,
        "name": ta.name,
        "number": ta.number,
        "type": ta.type,
        "currency_code": ta.currency_code,
        "current_balance": ta.current_balance,
        "current_balance_date": ta.current_balance_date,
        "safe_balance": ta.safe_balance,
        "starting_balance": ta.starting_balance,
        "starting_balance_date": ta.starting_balance_date,
        "institution": ta.institution.title if ta.institution else None,
        "is_net_worth": ta.is_net_worth,
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="pocketsmith_list_transactions",
            description="List transactions from Pocketsmith with optional filters. Returns transactions as JSON.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Filter transactions on or after this date (YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Filter transactions on or before this date (YYYY-MM-DD)",
                    },
                    "needs_review": {
                        "type": "boolean",
                        "description": "Filter to transactions that need review",
                    },
                    "uncategorised": {
                        "type": "boolean",
                        "description": "Filter to uncategorised transactions",
                    },
                    "search": {
                        "type": "string",
                        "description": "Search string to match against payee, category, notes, etc.",
                    },
                    "transaction_type": {
                        "type": "string",
                        "enum": ["debit", "credit"],
                        "description": "Filter by transaction type",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transactions to return (default 100)",
                    },
                },
            },
        ),
        Tool(
            name="pocketsmith_get_transaction",
            description="Get details of a specific transaction by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "The transaction ID",
                    },
                },
                "required": ["transaction_id"],
            },
        ),
        Tool(
            name="pocketsmith_update_transaction",
            description="Update a transaction's category, payee, note, labels, or review status",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "The transaction ID to update",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "New category ID to assign",
                    },
                    "payee": {
                        "type": "string",
                        "description": "New payee name",
                    },
                    "note": {
                        "type": "string",
                        "description": "New note/memo for the transaction",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New labels to assign",
                    },
                    "needs_review": {
                        "type": "boolean",
                        "description": "Set whether transaction needs review",
                    },
                },
                "required": ["transaction_id"],
            },
        ),
        Tool(
            name="pocketsmith_list_categories",
            description="List all categories. Returns a flat list with full category paths for easy lookup.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="pocketsmith_search_transactions",
            description="Search transactions by keyword (payee, category, notes). Shortcut for list_transactions with search parameter.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to match against transaction fields",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transactions to return (default 50)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="pocketsmith_categorize_transaction",
            description="Categorize a transaction by setting its category. This is a convenience wrapper around update_transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "The transaction ID to categorize",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "The category ID to assign",
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note explaining the categorization",
                    },
                    "mark_reviewed": {
                        "type": "boolean",
                        "description": "Whether to mark the transaction as reviewed (default true)",
                    },
                },
                "required": ["transaction_id", "category_id"],
            },
        ),
        Tool(
            name="pocketsmith_create_category_rule",
            description="Create a rule to automatically categorize future transactions matching a payee pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_id": {
                        "type": "integer",
                        "description": "The category ID to assign when rule matches",
                    },
                    "payee_matches": {
                        "type": "string",
                        "description": "Keyword pattern to match in payee field",
                    },
                    "apply_to_uncategorised": {
                        "type": "boolean",
                        "description": "Apply this rule to existing uncategorised transactions",
                    },
                    "apply_to_all": {
                        "type": "boolean",
                        "description": "Apply this rule to ALL existing transactions (re-categorizes)",
                    },
                },
                "required": ["category_id", "payee_matches"],
            },
        ),
        Tool(
            name="pocketsmith_get_status",
            description="Get connection status and authenticated user info",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Tier 1 tools
        Tool(
            name="pocketsmith_list_accounts",
            description="List all accounts with balances and details",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="pocketsmith_get_account",
            description="Get details of a specific account by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "integer",
                        "description": "The account ID",
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="pocketsmith_get_budget_summary",
            description="Get budget summary for a period and date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["weeks", "months", "years"],
                        "description": "The period for the budget summary (default: months)",
                    },
                    "interval": {
                        "type": "integer",
                        "description": "The interval for the period (default: 1)",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for the budget summary (YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for the budget summary (YYYY-MM-DD)",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Tool(
            name="pocketsmith_list_budget",
            description="List per-category budget analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "roll_up": {
                        "type": "boolean",
                        "description": "Whether to roll up child categories into parent categories",
                    },
                },
            },
        ),
        Tool(
            name="pocketsmith_get_trend_analysis",
            description="Get trend analysis across categories and scenarios",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["weeks", "months", "years"],
                        "description": "The period for trend analysis (default: months)",
                    },
                    "interval": {
                        "type": "integer",
                        "description": "The interval for the period (default: 1)",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for trend analysis (YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for trend analysis (YYYY-MM-DD)",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Category IDs to filter by",
                    },
                    "scenarios": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Scenario IDs to filter by",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Tool(
            name="pocketsmith_create_transaction",
            description="Create a new transaction",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_account_id": {
                        "type": "integer",
                        "description": "The transaction account ID",
                    },
                    "payee": {
                        "type": "string",
                        "description": "The payee name",
                    },
                    "amount": {
                        "type": "number",
                        "description": "The transaction amount (negative for debit, positive for credit)",
                    },
                    "date": {
                        "type": "string",
                        "description": "The transaction date (YYYY-MM-DD)",
                    },
                    "is_transfer": {
                        "type": "boolean",
                        "description": "Whether this is a transfer between accounts",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to assign to the transaction",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "Category ID to assign",
                    },
                    "note": {
                        "type": "string",
                        "description": "Note for the transaction",
                    },
                    "memo": {
                        "type": "string",
                        "description": "Memo for the transaction",
                    },
                    "needs_review": {
                        "type": "boolean",
                        "description": "Whether the transaction needs review",
                    },
                },
                "required": ["transaction_account_id", "payee", "amount", "date"],
            },
        ),
        Tool(
            name="pocketsmith_list_labels",
            description="List all labels used in transactions",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Tier 2 tools
        Tool(
            name="pocketsmith_list_transactions_by_account",
            description="List transactions for a specific account with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "integer",
                        "description": "The account ID to filter by",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Filter transactions on or after this date (YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Filter transactions on or before this date (YYYY-MM-DD)",
                    },
                    "needs_review": {
                        "type": "boolean",
                        "description": "Filter to transactions that need review",
                    },
                    "uncategorised": {
                        "type": "boolean",
                        "description": "Filter to uncategorised transactions",
                    },
                    "search": {
                        "type": "string",
                        "description": "Search string to match against transaction fields",
                    },
                    "transaction_type": {
                        "type": "string",
                        "enum": ["debit", "credit"],
                        "description": "Filter by transaction type",
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="pocketsmith_list_transactions_by_category",
            description="List transactions for one or more categories",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Category IDs to filter by",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Filter transactions on or after this date (YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Filter transactions on or before this date (YYYY-MM-DD)",
                    },
                    "needs_review": {
                        "type": "boolean",
                        "description": "Filter to transactions that need review",
                    },
                    "uncategorised": {
                        "type": "boolean",
                        "description": "Filter to uncategorised transactions",
                    },
                    "search": {
                        "type": "string",
                        "description": "Search string to match against transaction fields",
                    },
                    "transaction_type": {
                        "type": "string",
                        "enum": ["debit", "credit"],
                        "description": "Filter by transaction type",
                    },
                },
                "required": ["category_ids"],
            },
        ),
        Tool(
            name="pocketsmith_create_category",
            description="Create a new category",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The category title",
                    },
                    "colour": {
                        "type": "string",
                        "description": "The category color in hex format (e.g., #FF0000)",
                    },
                    "parent_id": {
                        "type": "integer",
                        "description": "Parent category ID for creating a subcategory",
                    },
                    "is_transfer": {
                        "type": "boolean",
                        "description": "Whether this category represents a transfer",
                    },
                    "is_bill": {
                        "type": "boolean",
                        "description": "Whether this category represents a bill",
                    },
                    "roll_up": {
                        "type": "boolean",
                        "description": "Whether to roll up child categories",
                    },
                    "refund_behaviour": {
                        "type": "string",
                        "description": "How refunds should be handled",
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="pocketsmith_list_events",
            description="List events (recurring transactions) for a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date for events (YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for events (YYYY-MM-DD)",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Tool(
            name="pocketsmith_create_event",
            description="Create a new event (recurring transaction)",
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario_id": {
                        "type": "integer",
                        "description": "The scenario ID (get from account details)",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "The category ID to assign",
                    },
                    "date": {
                        "type": "string",
                        "description": "The event date (YYYY-MM-DD)",
                    },
                    "amount": {
                        "type": "number",
                        "description": "The event amount (negative for expenses, positive for income)",
                    },
                    "repeat_type": {
                        "type": "string",
                        "enum": ["once", "daily", "weekly", "fortnightly", "monthly", "yearly", "each weekday"],
                        "description": "How often the event repeats",
                    },
                    "repeat_interval": {
                        "type": "integer",
                        "description": "The repeat interval (default: 1)",
                    },
                    "note": {
                        "type": "string",
                        "description": "Note for the event",
                    },
                },
                "required": ["scenario_id", "category_id", "date", "amount", "repeat_type"],
            },
        ),
        Tool(
            name="pocketsmith_delete_transaction",
            description="Delete a transaction by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "The transaction ID to delete",
                    },
                },
                "required": ["transaction_id"],
            },
        ),
        Tool(
            name="pocketsmith_list_transaction_accounts",
            description="List all transaction accounts with balances and details",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="pocketsmith_list_category_rules",
            description="List all category rules (automatic categorization rules)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        client = get_client()

        if name == "pocketsmith_list_transactions":
            start_date = None
            end_date = None
            if arguments.get("start_date"):
                start_date = date.fromisoformat(arguments["start_date"])
            if arguments.get("end_date"):
                end_date = date.fromisoformat(arguments["end_date"])

            transactions = client.list_all_transactions(
                start_date=start_date,
                end_date=end_date,
                needs_review=arguments.get("needs_review"),
                uncategorised=arguments.get("uncategorised"),
                search=arguments.get("search"),
                transaction_type=arguments.get("transaction_type"),
            )

            limit = arguments.get("limit", 100)
            if len(transactions) > limit:
                transactions = transactions[:limit]

            result = [transaction_to_dict(t) for t in transactions]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_get_transaction":
            transaction = client.get_transaction(arguments["transaction_id"])
            result = transaction_to_dict(transaction)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_update_transaction":
            transaction = client.update_transaction(
                transaction_id=arguments["transaction_id"],
                category_id=arguments.get("category_id"),
                payee=arguments.get("payee"),
                note=arguments.get("note"),
                labels=arguments.get("labels"),
                needs_review=arguments.get("needs_review"),
            )
            result = transaction_to_dict(transaction)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_list_categories":
            categories = client.list_categories()
            result = flatten_categories(categories)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_search_transactions":
            transactions = client.search_transactions(arguments["query"])
            limit = arguments.get("limit", 50)
            if len(transactions) > limit:
                transactions = transactions[:limit]
            result = [transaction_to_dict(t) for t in transactions]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_categorize_transaction":
            mark_reviewed = arguments.get("mark_reviewed", True)
            transaction = client.update_transaction(
                transaction_id=arguments["transaction_id"],
                category_id=arguments["category_id"],
                note=arguments.get("note"),
                needs_review=False if mark_reviewed else None,
            )
            result = transaction_to_dict(transaction)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_create_category_rule":
            rule = client.create_category_rule(
                category_id=arguments["category_id"],
                payee_matches=arguments["payee_matches"],
                apply_to_uncategorised=arguments.get("apply_to_uncategorised", False),
                apply_to_all=arguments.get("apply_to_all", False),
            )
            result = {
                "id": rule.id,
                "payee_matches": rule.payee_matches,
                "category": rule.category.title,
                "category_id": rule.category.id,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_get_status":
            user = client.get_me()
            result = {
                "connected": True,
                "user": {
                    "id": user.id,
                    "login": user.login,
                    "name": user.name,
                    "email": user.email,
                    "currency": user.base_currency_code,
                    "timezone": user.time_zone,
                },
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # Tier 1 tool handlers
        elif name == "pocketsmith_list_accounts":
            accounts = client.list_accounts()
            result = [account_to_dict(a) for a in accounts]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_get_account":
            account = client.get_account(arguments["account_id"])
            result = account_to_dict(account)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_get_budget_summary":
            start_date = date.fromisoformat(arguments["start_date"])
            end_date = date.fromisoformat(arguments["end_date"])
            period = arguments.get("period", "months")
            interval = arguments.get("interval", 1)

            result = client.get_budget_summary(
                period=period,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_list_budget":
            result = client.list_budget(roll_up=arguments.get("roll_up"))
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_get_trend_analysis":
            start_date = date.fromisoformat(arguments["start_date"])
            end_date = date.fromisoformat(arguments["end_date"])
            period = arguments.get("period", "months")
            interval = arguments.get("interval", 1)

            result = client.get_trend_analysis(
                period=period,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                categories=arguments.get("categories"),
                scenarios=arguments.get("scenarios"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_create_transaction":
            tx_date = date.fromisoformat(arguments["date"])

            transaction = client.create_transaction(
                transaction_account_id=arguments["transaction_account_id"],
                payee=arguments["payee"],
                amount=arguments["amount"],
                date=tx_date,
                is_transfer=arguments.get("is_transfer"),
                labels=arguments.get("labels"),
                category_id=arguments.get("category_id"),
                note=arguments.get("note"),
                memo=arguments.get("memo"),
                needs_review=arguments.get("needs_review"),
            )
            result = transaction_to_dict(transaction)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_list_labels":
            labels = client.list_labels()
            return [TextContent(type="text", text=json.dumps(labels, indent=2))]

        # Tier 2 tool handlers
        elif name == "pocketsmith_list_transactions_by_account":
            start_date = None
            end_date = None
            if arguments.get("start_date"):
                start_date = date.fromisoformat(arguments["start_date"])
            if arguments.get("end_date"):
                end_date = date.fromisoformat(arguments["end_date"])

            transactions = client.list_transactions_by_account(
                account_id=arguments["account_id"],
                start_date=start_date,
                end_date=end_date,
                needs_review=arguments.get("needs_review"),
                uncategorised=arguments.get("uncategorised"),
                search=arguments.get("search"),
                transaction_type=arguments.get("transaction_type"),
            )
            result = [transaction_to_dict(t) for t in transactions]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_list_transactions_by_category":
            start_date = None
            end_date = None
            if arguments.get("start_date"):
                start_date = date.fromisoformat(arguments["start_date"])
            if arguments.get("end_date"):
                end_date = date.fromisoformat(arguments["end_date"])

            transactions = client.list_transactions_by_category(
                category_ids=arguments["category_ids"],
                start_date=start_date,
                end_date=end_date,
                needs_review=arguments.get("needs_review"),
                uncategorised=arguments.get("uncategorised"),
                search=arguments.get("search"),
                transaction_type=arguments.get("transaction_type"),
            )
            result = [transaction_to_dict(t) for t in transactions]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_create_category":
            category = client.create_category(
                title=arguments["title"],
                colour=arguments.get("colour"),
                parent_id=arguments.get("parent_id"),
                is_transfer=arguments.get("is_transfer"),
                is_bill=arguments.get("is_bill"),
                roll_up=arguments.get("roll_up"),
                refund_behaviour=arguments.get("refund_behaviour"),
            )
            result = category_to_dict(category, include_children=False)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_list_events":
            start_date = date.fromisoformat(arguments["start_date"])
            end_date = date.fromisoformat(arguments["end_date"])

            events = client.list_events(
                start_date=start_date,
                end_date=end_date,
            )
            result = [event_to_dict(e) for e in events]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_create_event":
            event_date = date.fromisoformat(arguments["date"])

            event = client.create_event(
                scenario_id=arguments["scenario_id"],
                category_id=arguments["category_id"],
                date=event_date,
                amount=arguments["amount"],
                repeat_type=arguments["repeat_type"],
                repeat_interval=arguments.get("repeat_interval", 1),
                note=arguments.get("note"),
            )
            result = event_to_dict(event)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_delete_transaction":
            client.delete_transaction(arguments["transaction_id"])
            result = {
                "success": True,
                "transaction_id": arguments["transaction_id"],
                "message": "Transaction deleted successfully",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_list_transaction_accounts":
            accounts = client.list_transaction_accounts()
            result = [transaction_account_to_dict(ta) for ta in accounts]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pocketsmith_list_category_rules":
            rules = client.list_category_rules()
            result = [
                {
                    "id": r.id,
                    "payee_matches": r.payee_matches,
                    "category": r.category.title,
                    "category_id": r.category.id,
                }
                for r in rules
            ]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except PocketsmithError as e:
        error_result = {"error": str(e), "status_code": e.status_code}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    except Exception as e:
        error_result = {"error": str(e)}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
