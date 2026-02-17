"""Test fixtures and configuration for pocketsmith-mcp tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_api_key() -> str:
    """Mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_settings(mock_api_key: str) -> MagicMock:
    """Mock settings with test API key."""
    settings = MagicMock()
    settings.pocketsmith_api_key.get_secret_value.return_value = mock_api_key
    settings.pocketsmith_base_url = "https://api.test.pocketsmith.com/v2"
    return settings


@pytest.fixture
def mock_settings_env(mock_api_key: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment variables for testing."""
    monkeypatch.setenv("POCKETSMITH_API_KEY", mock_api_key)
    monkeypatch.setenv("POCKETSMITH_BASE_URL", "https://api.test.pocketsmith.com/v2")


@pytest.fixture
def mock_httpx_client() -> Generator[MagicMock, None, None]:
    """Mock httpx.Client for API calls."""
    with patch("pocketsmith_mcp.client.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data from API."""
    return {
        "id": 12345,
        "login": "testuser",
        "name": "Test User",
        "email": "test@example.com",
        "base_currency_code": "USD",
        "time_zone": "America/New_York",
    }


@pytest.fixture
def sample_category_data() -> list[dict]:
    """Sample category data from API."""
    return [
        {
            "id": 101,
            "title": "Groceries",
            "colour": "#FF0000",
            "parent_id": None,
            "is_transfer": False,
            "is_bill": False,
            "children": [
                {
                    "id": 102,
                    "title": "Weekly Shopping",
                    "colour": "#FF5555",
                    "parent_id": 101,
                    "is_transfer": False,
                    "is_bill": False,
                    "children": [],
                }
            ],
        },
        {
            "id": 201,
            "title": "Income",
            "colour": "#00FF00",
            "parent_id": None,
            "is_transfer": False,
            "is_bill": False,
            "children": [],
        },
    ]


@pytest.fixture
def sample_transaction_data() -> list[dict]:
    """Sample transaction data from API."""
    return [
        {
            "id": 1001,
            "payee": "Amazon.com",
            "original_payee": "Amazon.com*",
            "amount": -150.00,
            "date": "2025-01-15",
            "type": "debit",
            "is_transfer": "false",
            "category": {
                "id": 301,
                "title": "Household",
                "colour": "#0000FF",
                "parent_id": None,
                "is_transfer": False,
                "is_bill": False,
                "children": [],
            },
            "note": None,
            "memo": None,
            "labels": [],
            "needs_review": True,
            "status": "posted",
            "transaction_account": {
                "id": 401,
                "name": "Checking",
                "number": "1234",
                "current_balance": 5000.00,
                "currency_code": "USD",
            },
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
        },
        {
            "id": 1002,
            "payee": "Salary",
            "original_payee": None,
            "amount": 3000.00,
            "date": "2025-01-14",
            "type": "credit",
            "is_transfer": False,
            "category": {
                "id": 201,
                "title": "Income",
                "colour": "#00FF00",
                "parent_id": None,
                "is_transfer": False,
                "is_bill": False,
                "children": [],
            },
            "note": None,
            "memo": "Monthly salary",
            "labels": ["monthly"],
            "needs_review": False,
            "status": "posted",
            "transaction_account": {
                "id": 401,
                "name": "Checking",
                "number": "1234",
                "current_balance": 5000.00,
                "currency_code": "USD",
            },
            "created_at": "2025-01-14T09:00:00Z",
            "updated_at": "2025-01-14T09:00:00Z",
        },
    ]


@pytest.fixture
def sample_category_rules_data() -> list[dict]:
    """Sample category rules data from API."""
    return [
        {
            "id": 1,
            "payee_matches": "amazon",
            "category": {
                "id": 301,
                "title": "Household",
                "colour": "#0000FF",
                "parent_id": None,
                "is_transfer": False,
                "is_bill": False,
                "children": [],
            },
        },
        {
            "id": 2,
            "payee_matches": "starbucks",
            "category": {
                "id": 102,
                "title": "Weekly Shopping",
                "colour": "#FF5555",
                "parent_id": 101,
                "is_transfer": False,
                "is_bill": False,
                "children": [],
            },
        },
    ]


@pytest.fixture
def sample_account_data() -> list[dict]:
    """Sample account data from API."""
    return [
        {
            "id": 501,
            "title": "Checking Account",
            "currency_code": "USD",
            "type": "bank",
            "is_net_worth": True,
            "current_balance": 5000.00,
            "current_balance_in_base_currency": 5000.00,
            "current_balance_date": "2025-01-15",
            "safe_balance": 4500.00,
            "safe_balance_in_base_currency": 4500.00,
            "primary_transaction_account": {
                "id": 601,
                "name": "Checking",
                "number": "1234",
                "current_balance": 5000.00,
                "currency_code": "USD",
            },
            "transaction_accounts": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2025-01-15T00:00:00Z",
        },
        {
            "id": 502,
            "title": "Credit Card",
            "currency_code": "USD",
            "type": "credits",
            "is_net_worth": True,
            "current_balance": -1500.00,
            "current_balance_in_base_currency": -1500.00,
            "current_balance_date": "2025-01-15",
            "safe_balance": -1500.00,
            "safe_balance_in_base_currency": -1500.00,
            "primary_transaction_account": {
                "id": 602,
                "name": "Credit Card",
                "number": "5678",
                "current_balance": -1500.00,
                "currency_code": "USD",
            },
            "transaction_accounts": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2025-01-15T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_event_data() -> list[dict]:
    """Sample event data from API."""
    return [
        {
            "id": "123-1704067200",
            "category": {
                "id": 101,
                "title": "Utilities",
                "colour": "#FF0000",
                "parent_id": None,
                "is_transfer": False,
                "is_bill": True,
                "children": [],
            },
            "scenario": {
                "id": 1,
                "title": "Primary",
                "description": None,
            },
            "amount": -150.00,
            "amount_in_base_currency": -150.00,
            "currency_code": "USD",
            "date": "2025-01-01",
            "colour": "#FF0000",
            "note": "Monthly electricity bill",
            "repeat_type": "monthly",
            "repeat_interval": 1,
            "series_id": 123,
            "series_start_id": None,
            "infinite_series": True,
        },
        {
            "id": "124-1704672000",
            "category": {
                "id": 102,
                "title": "Rent",
                "colour": "#00FF00",
                "parent_id": None,
                "is_transfer": False,
                "is_bill": True,
                "children": [],
            },
            "scenario": {
                "id": 1,
                "title": "Primary",
                "description": None,
            },
            "amount": -2000.00,
            "amount_in_base_currency": -2000.00,
            "currency_code": "USD",
            "date": "2025-01-08",
            "colour": "#00FF00",
            "note": "Monthly rent payment",
            "repeat_type": "monthly",
            "repeat_interval": 1,
            "series_id": 124,
            "series_start_id": None,
            "infinite_series": True,
        },
    ]


@pytest.fixture
def sample_transaction_account_data() -> list[dict]:
    """Sample transaction account data from API."""
    return [
        {
            "id": 601,
            "name": "Checking",
            "number": "1234",
            "current_balance": 5000.00,
            "current_balance_date": "2025-01-15",
            "currency_code": "USD",
            "type": "bank",
            "is_net_worth": True,
            "starting_balance": 0.00,
            "starting_balance_date": "2024-01-01",
            "safe_balance": 4500.00,
            "institution": {
                "id": 1,
                "title": "Test Bank",
                "currency_code": "USD",
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2025-01-15T00:00:00Z",
        },
        {
            "id": 602,
            "name": "Credit Card",
            "number": "5678",
            "current_balance": -1500.00,
            "current_balance_date": "2025-01-15",
            "currency_code": "USD",
            "type": "credits",
            "is_net_worth": True,
            "starting_balance": 0.00,
            "starting_balance_date": "2024-01-01",
            "safe_balance": -1500.00,
            "institution": {
                "id": 2,
                "title": "Test Credit Union",
                "currency_code": "USD",
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2025-01-15T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_label_data() -> list[str]:
    """Sample label data from API."""
    return ["travel", "business", "personal", "tax-deductible"]


@pytest.fixture
def sample_budget_summary_data() -> dict:
    """Sample budget summary data from API."""
    return {
        "period": "months",
        "interval": 1,
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "total_actual_amount": -3500.00,
        "total_forecast_amount": -3200.00,
        "total_current_amount": -3500.00,
    }


@pytest.fixture
def sample_budget_data() -> list[dict]:
    """Sample budget data from API."""
    return [
        {
            "category": {
                "id": 101,
                "title": "Groceries",
            },
            "actual": -500.00,
            "forecast": -450.00,
        },
        {
            "category": {
                "id": 102,
                "title": "Utilities",
            },
            "actual": -150.00,
            "forecast": -150.00,
        },
    ]
