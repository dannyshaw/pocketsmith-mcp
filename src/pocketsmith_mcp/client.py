"""Pocketsmith API client."""

from datetime import date, datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from pocketsmith_mcp.config import get_settings


class User(BaseModel):
    """Pocketsmith user model."""

    id: int
    login: str
    name: str | None = None
    email: str
    base_currency_code: str
    time_zone: str


class Category(BaseModel):
    """Pocketsmith category model."""

    id: int
    title: str
    colour: str | None = None
    parent_id: int | None = None
    is_transfer: bool = False
    is_bill: bool = False
    children: list["Category"] = Field(default_factory=list)


class TransactionAccount(BaseModel):
    """Pocketsmith transaction account model."""

    id: int
    name: str
    number: str | None = None
    current_balance: float | None = None
    currency_code: str | None = None


class Transaction(BaseModel):
    """Pocketsmith transaction model."""

    id: int
    payee: str
    original_payee: str | None = None
    amount: float
    date: date
    type: str  # "debit" or "credit"
    is_transfer: bool = False
    category: Category | None = None
    note: str | None = None
    memo: str | None = None
    labels: list[str] = Field(default_factory=list)
    needs_review: bool = False
    status: str | None = None  # "pending" or "posted"
    transaction_account: TransactionAccount | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("is_transfer", mode="before")
    @classmethod
    def coerce_is_transfer(cls, v: Any) -> bool:
        """Coerce is_transfer to boolean - API may return string or other types."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        if v is None:
            return False
        return bool(v)


class CategoryRule(BaseModel):
    """Pocketsmith category rule model."""

    id: int
    payee_matches: str
    category: Category


class PocketsmithError(Exception):
    """Pocketsmith API error."""

    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{status_code}] {message}" if status_code else message)


class PocketsmithClient:
    """Client for interacting with the Pocketsmith API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        """Initialize the client."""
        settings = get_settings()
        self._api_key = api_key or settings.pocketsmith_api_key.get_secret_value()
        self._base_url = base_url or settings.pocketsmith_base_url
        self._user_id: int | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "X-Developer-Key": self._api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request."""
        url = f"{self._base_url}{endpoint}"

        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        with httpx.Client(timeout=30.0) as client:
            response = client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=json,
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("error", response.text)
            except Exception:
                message = response.text
            raise PocketsmithError(message, response.status_code)

        if response.status_code == 204:
            return None

        return response.json()

    def get_me(self) -> User:
        """Get the authenticated user."""
        data = self._request("GET", "/me")
        return User.model_validate(data)

    def get_user_id(self) -> int:
        """Get the authenticated user's ID (cached)."""
        if self._user_id is None:
            user = self.get_me()
            self._user_id = user.id
        return self._user_id

    def list_categories(self, user_id: int | None = None) -> list[Category]:
        """List all categories for a user."""
        user_id = user_id or self.get_user_id()
        data = self._request("GET", f"/users/{user_id}/categories")
        return [Category.model_validate(c) for c in data]

    def get_category(self, category_id: int) -> Category:
        """Get a specific category."""
        data = self._request("GET", f"/categories/{category_id}")
        return Category.model_validate(data)

    def list_transactions(
        self,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        needs_review: bool | None = None,
        uncategorised: bool | None = None,
        search: str | None = None,
        transaction_type: str | None = None,
        page: int = 1,
    ) -> list[Transaction]:
        """List transactions for a user."""
        user_id = user_id or self.get_user_id()

        params = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "needs_review": 1 if needs_review else None,
            "uncategorised": 1 if uncategorised else None,
            "search": search,
            "type": transaction_type,
            "page": page,
        }

        try:
            data = self._request("GET", f"/users/{user_id}/transactions", params=params)
            return [Transaction.model_validate(t) for t in data]
        except PocketsmithError as e:
            # API returns 400 "page out of bounds" when no results
            if e.status_code == 400 and "page" in e.message.lower():
                return []
            raise

    def list_all_transactions(
        self,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        needs_review: bool | None = None,
        uncategorised: bool | None = None,
        search: str | None = None,
        transaction_type: str | None = None,
        max_pages: int = 100,
    ) -> list[Transaction]:
        """List all transactions, handling pagination."""
        all_transactions: list[Transaction] = []
        page = 1

        while page <= max_pages:
            transactions = self.list_transactions(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                needs_review=needs_review,
                uncategorised=uncategorised,
                search=search,
                transaction_type=transaction_type,
                page=page,
            )

            if not transactions:
                break

            all_transactions.extend(transactions)
            page += 1

        return all_transactions

    def get_transaction(self, transaction_id: int) -> Transaction:
        """Get a specific transaction."""
        data = self._request("GET", f"/transactions/{transaction_id}")
        return Transaction.model_validate(data)

    def update_transaction(
        self,
        transaction_id: int,
        category_id: int | None = None,
        payee: str | None = None,
        note: str | None = None,
        labels: list[str] | None = None,
        needs_review: bool | None = None,
        amount: float | None = None,
        splits: list[dict[str, Any]] | None = None,
        split: list[dict[str, Any]] | None = None,
    ) -> Transaction:
        """Update a transaction."""
        body: dict[str, Any] = {}

        if category_id is not None:
            body["category_id"] = category_id
        if payee is not None:
            body["payee"] = payee
        if note is not None:
            body["note"] = note
        if labels is not None:
            body["labels"] = ",".join(labels)
        if needs_review is not None:
            body["needs_review"] = needs_review
        if amount is not None:
            body["amount"] = amount
        if splits is not None:
            body["splits"] = splits
        if split is not None:
            body["splits"] = split

        data = self._request("PUT", f"/transactions/{transaction_id}", json=body)
        return Transaction.model_validate(data)

    def list_category_rules(self, user_id: int | None = None) -> list[CategoryRule]:
        """List all category rules for a user."""
        user_id = user_id or self.get_user_id()
        data = self._request("GET", f"/users/{user_id}/category_rules")
        return [CategoryRule.model_validate(r) for r in data]

    def create_category_rule(
        self,
        category_id: int,
        payee_matches: str,
        apply_to_uncategorised: bool = False,
        apply_to_all: bool = False,
    ) -> CategoryRule:
        """Create a category rule."""
        body = {
            "payee_matches": payee_matches,
            "apply_to_uncategorised": apply_to_uncategorised,
            "apply_to_all": apply_to_all,
        }

        data = self._request("POST", f"/categories/{category_id}/category_rules", json=body)
        return CategoryRule.model_validate(data)

    # Convenience methods for common date ranges

    def list_transactions_last_week(self, **kwargs) -> list[Transaction]:
        """List transactions from the last 7 days."""
        end = date.today()
        start = end - timedelta(days=7)
        return self.list_all_transactions(start_date=start, end_date=end, **kwargs)

    def list_transactions_last_month(self, **kwargs) -> list[Transaction]:
        """List transactions from the last 30 days."""
        end = date.today()
        start = end - timedelta(days=30)
        return self.list_all_transactions(start_date=start, end_date=end, **kwargs)

    def list_transactions_needs_review(self, **kwargs) -> list[Transaction]:
        """List transactions that need review."""
        return self.list_all_transactions(needs_review=True, **kwargs)

    def list_uncategorised_transactions(self, **kwargs) -> list[Transaction]:
        """List uncategorised transactions."""
        return self.list_all_transactions(uncategorised=True, **kwargs)

    def search_transactions(self, query: str, **kwargs) -> list[Transaction]:
        """Search transactions by keyword."""
        return self.list_all_transactions(search=query, **kwargs)
