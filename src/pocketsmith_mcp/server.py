"""Pocketsmith MCP server."""

import json
from datetime import date
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from pocketsmith_mcp.client import (
    Category,
    PocketsmithClient,
    PocketsmithError,
    Transaction,
)

# Import Amazon split utilities and models (local to this package)
from pocketsmith_mcp.amazon_split import (
    OrderItemSplit,
    OrderSplitter,
    PRODUCT_CATEGORY_MAPPING,
)
from pocketsmith_mcp.amazon_models import AmazonOrder, AmazonItem

AMAZON_SPLIT_AVAILABLE = True

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
        Tool(
            name="pocketsmith_split_amazon_order",
            description="Preview how an Amazon order would be split into categorized items",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_data": {
                        "type": "string",
                        "description": "Amazon order CSV data (Website, Order ID, Date, Amount, Product Name)",
                    },
                    "min_split_amount": {
                        "type": "number",
                        "description": "Minimum amount to attempt splitting (default 5.0)",
                    },
                    "max_splits": {
                        "type": "integer",
                        "description": "Maximum number of items to split (default 10)",
                    },
                },
                "required": ["order_data"],
            },
        ),
        Tool(
            name="pocketsmith_add_split_note",
            description="Add Amazon split details as a note to an existing transaction",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "The transaction ID to add note to",
                    },
                    "order_data": {
                        "type": "string",
                        "description": "Amazon order CSV data for this transaction",
                    },
                    "min_split_amount": {
                        "type": "number",
                        "description": "Minimum amount to attempt splitting (default 5.0)",
                    },
                    "max_splits": {
                        "type": "integer",
                        "description": "Maximum number of items to split (default 10)",
                    },
                    "confirm_splits": {
                        "type": "boolean",
                        "description": "Also update transaction category based on split (default false)",
                    },
                },
                "required": ["transaction_id", "order_data"],
            },
        ),
        Tool(
            name="pocketsmith_split_transaction",
            description="Split an Amazon transaction into multiple categorized transactions using PocketSmith's split API. Provide order data as tab-separated values: 'Order ID\\tDate\\tAmount\\tProduct Name'. The original transaction amount will be split into child transactions with proper categories, and the parent transaction will be updated with the remainder amount.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "The transaction ID to split",
                    },
                    "order_data": {
                        "type": "string",
                        "description": "Amazon order CSV data (tab-separated: Order ID, Date, Amount, Product Name). Multiple rows for same order ID are supported.",
                    },
                    "min_split_amount": {
                        "type": "number",
                        "description": "Minimum amount to attempt splitting (default 5.0)",
                    },
                    "max_splits": {
                        "type": "integer",
                        "description": "Maximum number of items to split (default 10)",
                    },
                },
                "required": ["transaction_id", "order_data"],
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

        elif name == "pocketsmith_split_amazon_order":
            if not AMAZON_SPLIT_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({"error": "Amazon split utilities not available"}, indent=2))]

            # Parse CSV order data
            order_data = arguments["order_data"]
            min_split_amount = arguments.get("min_split_amount", 5.0)
            max_splits = arguments.get("max_splits", 10)

            try:
                # Parse CSV rows (simplified - expecting key format from CSV)
                # Format: Website, Order ID, Order Date, Purchase Order Number, Currency,
                #         Unit Price, Unit Price Tax, Shipping Charge, Total Discounts, Total Owed,
                #         Shipment Item Subtotal, Shipment Item Subtotal Tax, ASIN, Product Condition,
                #         Quantity, Payment Instrument Type, Order Status, Shipment Status, Ship Date,
                #         Shipping Option, Shipping Address, Billing Address, Carrier Name & Tracking Number, Product Name

                # AmazonOrder, AmazonItem already imported at module level

                # Create splitter
                splitter = OrderSplitter(
                    min_split_amount=min_split_amount,
                    max_splits=max_splits,
                )

                # Parse order from CSV data
                lines = order_data.strip().split("\n")
                items = []
                order_number = None
                order_date = None
                grand_total = 0.0

                for line in lines:
                    if not line.strip():
                        continue
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) < 18:
                        continue

                    # Extract fields
                    website = parts[0]
                    current_order_number = parts[1]
                    date_str = parts[2]
                    currency = parts[4]
                    unit_price_str = parts[5]
                    quantity_str = parts[13]
                    product_name = parts[18]

                    # Track order number and date
                    if current_order_number and current_order_number != "Not Applicable":
                        order_number = current_order_number
                    if date_str and date_str != "Not Applicable":
                        try:
                            # Parse ISO 8601 format
                            order_date = date.fromisoformat(date_str.replace("Z", "+00:00").split("+")[0])
                        except:
                            pass

                    # Parse quantity
                    try:
                        quantity = int(quantity_str) if quantity_str != "Not Applicable" else 1
                    except:
                        quantity = 1

                    # Parse unit price
                    try:
                        unit_price = float(unit_price_str) if unit_price_str else 0
                    except:
                        unit_price = 0

                    if product_name and product_name != "Product Name":
                        items.append(
                            AmazonItem(
                                title=product_name,
                                quantity=quantity,
                                price=unit_price,
                            )
                        )

                # Calculate grand total from items
                grand_total = sum((i.price or 0) * i.quantity for i in items)

                # Create order
                order = AmazonOrder(
                    order_number=order_number or "Unknown",
                    order_date=order_date or date.today(),
                    grand_total=grand_total,
                    items=items,
                )

                # Check if should split
                should_split = splitter.should_split(order)

                # Get splits
                splits = splitter.split_order(order)

                result = {
                    "order_number": order.order_number,
                    "order_date": order.order_date.isoformat() if order.order_date else None,
                    "grand_total": order.grand_total,
                    "item_count": len(order.items),
                    "should_split": should_split,
                    "splits": [
                        {
                            "title": s.title,
                            "quantity": s.quantity,
                            "amount": s.amount,
                            "category_id": s.category_id,
                            "category_name": s.category_name,
                            "confidence": s.confidence,
                        }
                        for s in splits
                    ],
                }

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

        elif name == "pocketsmith_add_split_note":
            if not AMAZON_SPLIT_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({"error": "Amazon split utilities not available"}, indent=2))]

            transaction_id = arguments["transaction_id"]
            order_data = arguments["order_data"]
            min_split_amount = arguments.get("min_split_amount", 5.0)
            max_splits = arguments.get("max_splits", 10)
            confirm_splits = arguments.get("confirm_splits", False)

            try:
                # Get the transaction
                transaction = client.get_transaction(transaction_id)

                # Parse order data (same as above)
                lines = order_data.strip().split("\n")
                items = []
                order_number = None

                for line in lines:
                    if not line.strip():
                        continue
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) < 18:
                        continue

                    current_order_number = parts[1]
                    quantity_str = parts[13]
                    product_name = parts[18]

                    if current_order_number and current_order_number != "Not Applicable":
                        order_number = current_order_number
                    if product_name and product_name != "Product Name":
                        try:
                            quantity = int(quantity_str) if quantity_str != "Not Applicable" else 1
                        except:
                            quantity = 1
                        unit_price = float(parts[5]) if parts[5] else 0
                        items.append(
                            AmazonItem(title=product_name, quantity=quantity, price=unit_price)
                        )

                # Create splitter
                splitter = OrderSplitter(
                    min_split_amount=min_split_amount,
                    max_splits=max_splits,
                )

                # Create order
                grand_total = sum((i.price or 0) * i.quantity for i in items)
                order = AmazonOrder(
                    order_number=order_number or "Unknown",
                    order_date=transaction.date,
                    grand_total=grand_total,
                    items=items,
                )

                # Get splits
                splits = splitter.split_order(order)

                # Build note with split details
                note_lines = [f"Amazon Order: {order_number}"]
                note_lines.append(f"Total: ${grand_total:.2f}")

                if len(splits) == 1:
                    note_lines.append(f"Category: {splits[0].category_name}")
                else:
                    note_lines.append("Split Items:")
                    for i, split in enumerate(splits, 1):
                        conf_pct = int(split.confidence * 100)
                        note_lines.append(f"  {i}. ${split.amount:.2f} → {split.category_name} ({conf_pct}%)")

                note_text = "\n".join(note_lines)

                # Determine primary category (first/highest confidence)
                primary_split = splits[0]

                # Update transaction
                updated = client.update_transaction(
                    transaction_id=transaction_id,
                    note=note_text,
                    category_id=primary_split.category_id if confirm_splits else None,
                    needs_review=False,
                )

                result = {
                    "transaction_id": transaction_id,
                    "order_number": order_number,
                    "note_added": note_text,
                    "category_updated": confirm_splits,
                    "primary_category": {
                        "id": primary_split.category_id,
                        "name": primary_split.category_name,
                    },
                    "splits": [
                        {
                            "title": s.title,
                            "amount": s.amount,
                            "category": s.category_name,
                            "confidence": s.confidence,
                        }
                        for s in splits
                    ],
                }

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

        elif name == "pocketsmith_split_transaction":
            if not AMAZON_SPLIT_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({"error": "Amazon split utilities not available"}))]

            transaction_id = arguments["transaction_id"]
            order_data = arguments["order_data"]
            min_split_amount = arguments.get("min_split_amount", 5.0)
            max_splits = arguments.get("max_splits", 10)

            try:
                # Get the original transaction
                transaction = client.get_transaction(transaction_id)

                # Import Amazon models
                # AmazonOrder, AmazonItem already imported at module level

                # Parse order data - expecting simplified format with amounts
                # Format: Order ID \t Date \t Amount \t Product Name
                lines = order_data.strip().split("\n")
                items = []
                order_number = None
                order_date = transaction.date

                for line in lines:
                    if not line.strip():
                        continue
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) < 4:
                        continue

                    current_order_number = parts[0]
                    date_str = parts[1]
                    amount_str = parts[2]
                    product_name = parts[3]

                    if current_order_number and current_order_number != "Not Applicable":
                        order_number = current_order_number
                    if product_name and product_name != "Product Name":
                        try:
                            amount = float(amount_str) if amount_str else 0
                        except:
                            amount = 0
                        items.append(
                            AmazonItem(title=product_name, quantity=1, price=amount)
                        )

                # Create splitter
                splitter = OrderSplitter(
                    min_split_amount=min_split_amount,
                    max_splits=max_splits,
                )

                # Create order
                grand_total = sum((i.price or 0) * i.quantity for i in items)
                order = AmazonOrder(
                    order_number=order_number or "Unknown",
                    order_date=order_date,
                    grand_total=grand_total,
                    items=items,
                )

                # Get splits
                splits = splitter.split_order(order)

                if not splits:
                    return [TextContent(type="text", text=json.dumps({
                        "error": "No splits generated for this order",
                        "transaction_id": transaction_id,
                        "order_number": order_number,
                    }, indent=2))]

                # Build the splits array for PocketSmith API
                # Each split needs: amount, category_id, payee, note (optional)
                api_splits = []
                for split in splits:
                    # For debit transactions (expenses), use negative amounts
                    # For credit transactions (income), use positive amounts
                    split_amount = split.amount
                    if transaction.amount < 0:
                        split_amount = -abs(split.amount)

                    split_data = {
                        "amount": split_amount,
                        "category_id": split.category_id,
                        "payee": split.title or transaction.payee,
                        "date": transaction.date.isoformat(),
                        "type": transaction.type,
                    }
                    # Add note with item details
                    note_lines = []
                    if order_number:
                        note_lines.append(f"Amazon Order: {order_number}")
                    note_lines.append(f"Item: {split.title}")
                    if split.category_name:
                        note_lines.append(f"Category: {split.category_name}")
                    split_data["note"] = "\n".join(note_lines)
                    api_splits.append(split_data)

                # Calculate sum of split amounts and original amount
                splits_total = sum(s["amount"] for s in api_splits)
                original_amount = transaction.amount

                # The new amount for parent transaction (remainder) must satisfy:
                # new_amount + sum(splits) == original_amount
                # So: new_amount = original_amount - sum(splits)
                new_parent_amount = original_amount - splits_total

                # Build the update request with splits and new amount for parent
                # Note: PocketSmith API expects splits to be provided in the PUT request
                update_body = {
                    "amount": new_parent_amount,
                    "splits": api_splits,
                }

                # Use the PocketsmithClient's update_transaction method with splits
                try:
                    result = client.update_transaction(
                        transaction_id=transaction_id,
                        amount=new_parent_amount,
                        splits=api_splits,
                    )
                except PocketsmithError as e:
                    return [TextContent(type="text", text=json.dumps({
                        "error": str(e),
                        "status_code": e.status_code,
                        "debug": {
                            "original_amount": original_amount,
                            "splits_total": splits_total,
                            "new_parent_amount": new_parent_amount,
                            "request_body": update_body,
                        }
                    }, indent=2))]

                # Parse result - PocketSmith returns {transaction, split_transactions}
                if "transaction" in result:
                    return_data = {
                        "transaction_id": transaction_id,
                        "order_number": order_number,
                        "splits_created": len(api_splits),
                        "new_parent_amount": new_parent_amount,
                        "updated_transaction": transaction_to_dict(result["transaction"]),
                    }

                    if "split_transactions" in result:
                        return_data["split_transactions"] = [
                            transaction_to_dict(t)
                            for t in result["split_transactions"]
                        ]

                    return [TextContent(type="text", text=json.dumps(return_data, indent=2))]

                # No split transactions returned
                return [TextContent(type="text", text=json.dumps({
                    "transaction_id": transaction_id,
                    "order_number": order_number,
                    "splits_created": len(api_splits),
                    "new_parent_amount": new_parent_amount,
                    "updated_transaction": transaction_to_dict(result),
                }, indent=2))]

            except Exception as e:
                import traceback
                return [TextContent(type="text", text=json.dumps({
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }, indent=2))]

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
