"""Amazon models for MCP server.

Simple Pydantic models that match the AmazonOrders library interface
enough for OrderSplitter to work.
"""

from datetime import date

from pydantic import BaseModel, Field


class AmazonItem(BaseModel):
    """An item from an Amazon order."""

    title: str
    quantity: int = 1
    price: float | None = None
    link: str | None = None


class AmazonOrder(BaseModel):
    """An Amazon order."""

    order_number: str
    order_date: date
    grand_total: float
    items: list[AmazonItem] = Field(default_factory=list)
    shipments: list[str] = Field(default_factory=list)
    payment_method: str | None = None
