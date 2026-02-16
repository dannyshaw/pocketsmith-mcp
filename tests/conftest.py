"""Test fixtures and configuration for pocketsmith-mcp tests."""

import os
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from httpx import Response


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
