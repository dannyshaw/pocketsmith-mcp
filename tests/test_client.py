"""Tests for the Pocketsmith API client."""

from datetime import date

import pytest
from httpx import HTTPStatusError, Response

from pocketsmith_mcp.client import (
    Category,
    CategoryRule,
    PocketsmithClient,
    PocketsmithError,
    Transaction,
    User,
)


class TestPocketsmithClient:
    """Tests for PocketsmithClient."""

    def test_init_with_explicit_params(self, mock_settings_env: None) -> None:
        """Test client initialization with explicit parameters."""
        client = PocketsmithClient(
            api_key="custom-key", base_url="https://custom.api.com"
        )
        assert client._api_key == "custom-key"
        assert client._base_url == "https://custom.api.com"

    def test_get_headers(self, mock_settings_env: None) -> None:
        """Test request headers are correctly set."""
        client = PocketsmithClient(api_key="test-key")
        headers = client._get_headers()
        assert headers["X-Developer-Key"] == "test-key"
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"

    def test_get_me_success(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
        sample_user_data: dict,
    ) -> None:
        """Test successful user info retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_user_data
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")
        user = client.get_me()

        assert isinstance(user, User)
        assert user.id == 12345
        assert user.login == "testuser"
        assert user.email == "test@example.com"

        mock_httpx_client.request.assert_called_once_with(
            method="GET",
            url="https://api.pocketsmith.com/v2/me",
            headers=client._get_headers(),
            params=None,
            json=None,
        )

    def test_get_me_error(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test error handling in get_me."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.text = '{"error": "Unauthorized"}'
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")

        with pytest.raises(PocketsmithError) as exc_info:
            client.get_me()

        assert exc_info.value.status_code == 401
        assert "Unauthorized" in str(exc_info.value)

    def test_get_user_id_caching(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
        sample_user_data: dict,
    ) -> None:
        """Test that user ID is cached after first call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_user_data
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")

        # First call should make a request
        user_id_1 = client.get_user_id()
        assert mock_httpx_client.request.call_count == 1

        # Second call should use cache
        user_id_2 = client.get_user_id()
        assert mock_httpx_client.request.call_count == 1  # No new request
        assert user_id_1 == user_id_2 == 12345

    def test_list_categories(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
        sample_category_data: list[dict],
    ) -> None:
        """Test listing categories."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_category_data
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")
        client._user_id = 12345  # Skip get_user_id call
        categories = client.list_categories()

        assert len(categories) == 2
        assert all(isinstance(c, Category) for c in categories)

        # Check parent category
        groceries = categories[0]
        assert groceries.id == 101
        assert groceries.title == "Groceries"
        assert len(groceries.children) == 1

        # Check child category
        weekly = groceries.children[0]
        assert weekly.id == 102
        assert weekly.title == "Weekly Shopping"
        assert weekly.parent_id == 101

    def test_list_transactions(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
        sample_transaction_data: list[dict],
    ) -> None:
        """Test listing transactions."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_transaction_data
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")
        client._user_id = 12345
        transactions = client.list_transactions()

        assert len(transactions) == 2
        assert all(isinstance(t, Transaction) for t in transactions)

        # Check first transaction (debit)
        amazon = transactions[0]
        assert amazon.id == 1001
        assert amazon.payee == "Amazon.com"
        assert amazon.amount == -150.00
        assert amazon.type == "debit"
        assert amazon.is_transfer is False
        assert amazon.category is not None
        assert amazon.category.title == "Household"
        assert amazon.needs_review is True

        # Check second transaction (credit)
        salary = transactions[1]
        assert salary.id == 1002
        assert salary.payee == "Salary"
        assert salary.amount == 3000.00
        assert salary.type == "credit"
        assert salary.labels == ["monthly"]
        assert salary.needs_review is False

    def test_list_transactions_with_filters(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
        sample_transaction_data: list[dict],
    ) -> None:
        """Test listing transactions with filters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_transaction_data
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")
        client._user_id = 12345

        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        transactions = client.list_transactions(
            start_date=start_date,
            end_date=end_date,
            needs_review=True,
            transaction_type="debit",
        )

        # Verify the request was made with correct params
        call_args = mock_httpx_client.request.call_args
        params = call_args.kwargs["params"]

        assert params["start_date"] == "2025-01-01"
        assert params["end_date"] == "2025-01-31"
        assert params["needs_review"] == 1
        assert params["type"] == "debit"

    def test_list_all_transactions_pagination(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test that list_all_transactions handles pagination."""
        # First page returns data
        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.json.return_value = [{"id": 1}, {"id": 2}]

        # Second page also returns data
        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.json.return_value = [{"id": 3}]

        # Third page is empty (end of results)
        page3_response = MagicMock()
        page3_response.status_code = 400  # API returns 400 for page out of bounds
        page3_response.json.return_value = {"error": "page out of bounds"}
        page3_response.text = "page out of bounds"

        mock_httpx_client.request.side_effect = [
            page1_response,
            page2_response,
            page3_response,
        ]

        client = PocketsmithClient(api_key="test-key")
        client._user_id = 12345

        transactions = client.list_all_transactions()

        assert len(transactions) == 3
        assert [t.id for t in transactions] == [1, 2, 3]
        assert mock_httpx_client.request.call_count == 3

    def test_update_transaction(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
        sample_transaction_data: list[dict],
    ) -> None:
        """Test updating a transaction."""
        updated_data = sample_transaction_data[0].copy()
        updated_data["category_id"] = 999
        updated_data["note"] = "Updated note"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = updated_data
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")

        updated = client.update_transaction(
            transaction_id=1001,
            category_id=999,
            note="Updated note",
            labels=["test"],
            needs_review=False,
        )

        # Verify request body
        call_args = mock_httpx_client.request.call_args
        body = call_args.kwargs["json"]

        assert body["category_id"] == 999
        assert body["note"] == "Updated note"
        assert body["labels"] == "test"
        assert body["needs_review"] is False

    def test_create_category_rule(
        self,
        mock_settings_env: None,
        mock_httpx_client: MagicMock,
        sample_category_data: list[dict],
    ) -> None:
        """Test creating a category rule."""
        rule_data = {
            "id": 123,
            "payee_matches": "test pattern",
            "category": sample_category_data[0],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = rule_data
        mock_httpx_client.request.return_value = mock_response

        client = PocketsmithClient(api_key="test-key")

        rule = client.create_category_rule(
            category_id=101,
            payee_matches="test pattern",
            apply_to_uncategorised=True,
        )

        assert isinstance(rule, CategoryRule)
        assert rule.id == 123
        assert rule.payee_matches == "test pattern"

        # Verify request
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "POST"
        assert "categories/101/category_rules" in call_args.kwargs["url"]

        body = call_args.kwargs["json"]
        assert body["payee_matches"] == "test pattern"
        assert body["apply_to_uncategorised"] is True


class TestModels:
    """Tests for Pydantic models."""

    def test_user_model(self, sample_user_data: dict) -> None:
        """Test User model validation."""
        user = User.model_validate(sample_user_data)
        assert user.id == 12345
        assert user.login == "testuser"
        assert user.base_currency_code == "USD"

    def test_category_model(self, sample_category_data: list) -> None:
        """Test Category model validation."""
        parent = Category.model_validate(sample_category_data[0])
        assert parent.id == 101
        assert parent.title == "Groceries"
        assert len(parent.children) == 1

        child = parent.children[0]
        assert child.id == 102
        assert child.parent_id == 101

    def test_transaction_model_is_transfer_coercion(
        self,
    ) -> None:
        """Test that is_transfer is coerced to boolean."""
        # String "true" should become True
        tx1 = Transaction(
            id=1,
            payee="Test",
            amount=-10.0,
            date=date.today(),
            type="debit",
            is_transfer="true",  # type: ignore
        )
        assert tx1.is_transfer is True

        # String "false" should become False
        tx2 = Transaction(
            id=2,
            payee="Test",
            amount=-10.0,
            date=date.today(),
            type="debit",
            is_transfer="false",  # type: ignore
        )
        assert tx2.is_transfer is False

        # None should become False
        tx3 = Transaction(
            id=3,
            payee="Test",
            amount=-10.0,
            date=date.today(),
            type="debit",
            is_transfer=None,  # type: ignore
        )
        assert tx3.is_transfer is False

    def test_transaction_model_with_full_data(
        self, sample_transaction_data: list[dict]
    ) -> None:
        """Test Transaction model with full sample data."""
        tx = Transaction.model_validate(sample_transaction_data[0])
        assert tx.id == 1001
        assert tx.payee == "Amazon.com"
        assert tx.category is not None
        assert tx.transaction_account is not None
        assert tx.transaction_account.name == "Checking"
