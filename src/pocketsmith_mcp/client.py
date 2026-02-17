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


class Institution(BaseModel):
    """Pocketsmith institution model."""

    id: int
    title: str
    currency_code: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TransactionAccount(BaseModel):
    """Pocketsmith transaction account model."""

    id: int
    name: str
    number: str | None = None
    current_balance: float | None = None
    current_balance_date: str | None = None
    current_balance_in_base_currency: float | None = None
    current_balance_exchange_rate: float | None = None
    currency_code: str | None = None
    type: str | None = None
    is_net_worth: bool = False
    starting_balance: float | None = None
    starting_balance_date: str | None = None
    safe_balance: float | None = None
    safe_balance_in_base_currency: float | None = None
    institution: Institution | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


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


class Scenario(BaseModel):
    """Pocketsmith scenario model."""

    id: int
    title: str
    description: str | None = None
    interest_rate: float | None = None
    interest_rate_repeat_id: int | None = None
    type: str | None = None
    minimum_value: float | None = None
    maximum_value: float | None = None
    achieve_date: str | None = None
    starting_balance: float | None = None
    starting_balance_date: str | None = None
    closing_balance: float | None = None
    closing_balance_date: str | None = None
    current_balance: float | None = None
    current_balance_in_base_currency: float | None = None
    current_balance_exchange_rate: float | None = None
    safe_balance: float | None = None
    safe_balance_in_base_currency: float | None = None


class Account(BaseModel):
    """Pocketsmith account model."""

    id: int
    title: str
    currency_code: str
    type: str
    is_net_worth: bool = False
    current_balance: float | None = None
    current_balance_in_base_currency: float | None = None
    current_balance_date: str | None = None
    safe_balance: float | None = None
    safe_balance_in_base_currency: float | None = None
    primary_transaction_account: TransactionAccount | None = None
    transaction_accounts: list[TransactionAccount] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Event(BaseModel):
    """Pocketsmith event model (recurring transaction)."""

    id: str
    category: Category | None = None
    scenario: Scenario | None = None
    amount: float
    amount_in_base_currency: float | None = None
    currency_code: str | None = None
    date: date
    colour: str | None = None
    note: str | None = None
    repeat_type: str
    repeat_interval: int = 1
    series_id: int
    series_start_id: str | None = None
    infinite_series: bool = False


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

    # Tier 1 methods - Account and budget management

    def list_accounts(self, user_id: int | None = None) -> list[Account]:
        """List all accounts for a user."""
        user_id = user_id or self.get_user_id()
        data = self._request("GET", f"/users/{user_id}/accounts")
        return [Account.model_validate(a) for a in data]

    def get_account(self, account_id: int) -> Account:
        """Get a specific account by ID."""
        data = self._request("GET", f"/accounts/{account_id}")
        return Account.model_validate(data)

    def get_budget_summary(
        self,
        user_id: int | None = None,
        period: str = "months",
        interval: int = 1,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Any:
        """Get budget summary for a period and date range."""
        user_id = user_id or self.get_user_id()
        params = {
            "period": period,
            "interval": interval,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
        return self._request("GET", f"/users/{user_id}/budget_summary", params=params)

    def list_budget(self, user_id: int | None = None, roll_up: bool | None = None) -> Any:
        """List per-category budget analysis."""
        user_id = user_id or self.get_user_id()
        params = {"roll_up": 1 if roll_up else None}
        return self._request("GET", f"/users/{user_id}/budget", params=params)

    def get_trend_analysis(
        self,
        user_id: int | None = None,
        period: str = "months",
        interval: int = 1,
        start_date: date | None = None,
        end_date: date | None = None,
        categories: list[int] | None = None,
        scenarios: list[int] | None = None,
    ) -> Any:
        """Get trend analysis across categories and scenarios."""
        user_id = user_id or self.get_user_id()
        params = {
            "period": period,
            "interval": interval,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "categories": ",".join(str(c) for c in categories) if categories else None,
            "scenarios": ",".join(str(s) for s in scenarios) if scenarios else None,
        }
        return self._request("GET", f"/users/{user_id}/trend_analysis", params=params)

    def create_transaction(
        self,
        transaction_account_id: int,
        payee: str,
        amount: float,
        date: date,
        is_transfer: bool | None = None,
        labels: list[str] | None = None,
        category_id: int | None = None,
        note: str | None = None,
        memo: str | None = None,
        cheque_number: str | None = None,
        needs_review: bool | None = None,
    ) -> Transaction:
        """Create a new transaction."""
        body: dict[str, Any] = {
            "payee": payee,
            "amount": amount,
            "date": date.isoformat(),
        }

        if is_transfer is not None:
            body["is_transfer"] = is_transfer
        if labels is not None:
            body["labels"] = ",".join(labels)
        if category_id is not None:
            body["category_id"] = category_id
        if note is not None:
            body["note"] = note
        if memo is not None:
            body["memo"] = memo
        if cheque_number is not None:
            body["cheque_number"] = cheque_number
        if needs_review is not None:
            body["needs_review"] = needs_review

        data = self._request(
            "POST", f"/transaction_accounts/{transaction_account_id}/transactions", json=body
        )
        return Transaction.model_validate(data)

    def list_labels(self, user_id: int | None = None) -> list[str]:
        """List all labels for a user."""
        user_id = user_id or self.get_user_id()
        data = self._request("GET", f"/users/{user_id}/labels")
        return data if isinstance(data, list) else []

    # Tier 2 methods - Enhanced filtering and management

    def list_transactions_by_account(
        self,
        account_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        needs_review: bool | None = None,
        uncategorised: bool | None = None,
        search: str | None = None,
        transaction_type: str | None = None,
        page: int = 1,
    ) -> list[Transaction]:
        """List transactions for a specific account."""
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
            data = self._request("GET", f"/accounts/{account_id}/transactions", params=params)
            return [Transaction.model_validate(t) for t in data]
        except PocketsmithError as e:
            if e.status_code == 400 and "page" in e.message.lower():
                return []
            raise

    def list_transactions_by_category(
        self,
        category_ids: list[int],
        start_date: date | None = None,
        end_date: date | None = None,
        needs_review: bool | None = None,
        uncategorised: bool | None = None,
        search: str | None = None,
        transaction_type: str | None = None,
        page: int = 1,
    ) -> list[Transaction]:
        """List transactions for one or more categories."""
        params = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "needs_review": 1 if needs_review else None,
            "uncategorised": 1 if uncategorised else None,
            "search": search,
            "type": transaction_type,
            "page": page,
        }

        # Convert category_ids list to comma-separated string
        category_filter = ",".join(str(c) for c in category_ids)
        endpoint = f"/categories/{category_filter}/transactions"

        try:
            data = self._request("GET", endpoint, params=params)
            return [Transaction.model_validate(t) for t in data]
        except PocketsmithError as e:
            if e.status_code == 400 and "page" in e.message.lower():
                return []
            raise

    def create_category(
        self,
        user_id: int | None = None,
        title: str = "",
        colour: str | None = None,
        parent_id: int | None = None,
        is_transfer: bool | None = None,
        is_bill: bool | None = None,
        roll_up: bool | None = None,
        refund_behaviour: str | None = None,
    ) -> Category:
        """Create a new category."""
        user_id = user_id or self.get_user_id()
        body: dict[str, Any] = {"title": title}

        if colour is not None:
            body["colour"] = colour
        if parent_id is not None:
            body["parent_id"] = parent_id
        if is_transfer is not None:
            body["is_transfer"] = is_transfer
        if is_bill is not None:
            body["is_bill"] = is_bill
        if roll_up is not None:
            body["roll_up"] = roll_up
        if refund_behaviour is not None:
            body["refund_behaviour"] = refund_behaviour

        data = self._request("POST", f"/users/{user_id}/categories", json=body)
        return Category.model_validate(data)

    def list_events(
        self,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Event]:
        """List events (recurring transactions) for a date range."""
        user_id = user_id or self.get_user_id()
        params = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
        data = self._request("GET", f"/users/{user_id}/events", params=params)
        return [Event.model_validate(e) for e in data]

    def create_event(
        self,
        scenario_id: int,
        category_id: int,
        date: date,
        amount: float,
        repeat_type: str = "once",
        repeat_interval: int = 1,
        note: str | None = None,
    ) -> Event:
        """Create a new event (recurring transaction)."""
        body: dict[str, Any] = {
            "category_id": category_id,
            "date": date.isoformat(),
            "amount": amount,
            "repeat_type": repeat_type,
            "repeat_interval": repeat_interval,
        }

        if note is not None:
            body["note"] = note

        data = self._request("POST", f"/scenarios/{scenario_id}/events", json=body)
        return Event.model_validate(data)

    def delete_transaction(self, transaction_id: int) -> None:
        """Delete a transaction."""
        self._request("DELETE", f"/transactions/{transaction_id}")

    def list_transaction_accounts(self, user_id: int | None = None) -> list[TransactionAccount]:
        """List all transaction accounts for a user."""
        user_id = user_id or self.get_user_id()
        data = self._request("GET", f"/users/{user_id}/transaction_accounts")
        return [TransactionAccount.model_validate(ta) for ta in data]
