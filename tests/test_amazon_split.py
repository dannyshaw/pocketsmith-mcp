"""Tests for Amazon order splitting functionality."""

from datetime import date

import pytest

from pocketsmith_mcp.amazon_models import AmazonItem, AmazonOrder
from pocketsmith_mcp.amazon_split import (
    DEFAULT_CATEGORY_ID,
    DEFAULT_CATEGORY_NAME,
    OrderItemSplit,
    OrderSplitter,
    PRODUCT_CATEGORY_MAPPING,
    categorize_item,
)


class TestProductCategoryMapping:
    """Tests for the product category mapping."""

    def test_mapping_has_expected_keys(self) -> None:
        """Test that the mapping has expected categories."""
        # Check some key categories exist
        assert "toy" in PRODUCT_CATEGORY_MAPPING
        assert "protein" in PRODUCT_CATEGORY_MAPPING
        assert "vitamin" in PRODUCT_CATEGORY_MAPPING
        assert "headphone" in PRODUCT_CATEGORY_MAPPING

    def test_mapping_values_are_tuples(self) -> None:
        """Test that all mapping values are proper tuples."""
        for keyword, value in PRODUCT_CATEGORY_MAPPING.items():
            assert isinstance(value, tuple)
            assert len(value) == 3
            cat_id, cat_name, weight = value
            assert isinstance(cat_id, int)
            assert isinstance(cat_name, str)
            assert isinstance(weight, float)
            assert 0.0 <= weight <= 1.0

    def test_kids_category_mapping(self) -> None:
        """Test kids-related category mappings."""
        assert "kids" in PRODUCT_CATEGORY_MAPPING
        assert "toy" in PRODUCT_CATEGORY_MAPPING
        assert "lego" in PRODUCT_CATEGORY_MAPPING

        cat_id, cat_name, weight = PRODUCT_CATEGORY_MAPPING["toy"]
        assert cat_name == "Kids Activities"
        assert weight == 0.8

    def test_gym_category_mapping(self) -> None:
        """Test gym/fitness category mappings."""
        assert "protein" in PRODUCT_CATEGORY_MAPPING
        assert "yoga" in PRODUCT_CATEGORY_MAPPING

        cat_id, cat_name, weight = PRODUCT_CATEGORY_MAPPING["protein"]
        assert cat_name == "Gym Membership"
        assert weight == 0.9

    def test_electronics_category_mapping(self) -> None:
        """Test electronics category mappings."""
        assert "headphone" in PRODUCT_CATEGORY_MAPPING
        assert "usb" in PRODUCT_CATEGORY_MAPPING

        cat_id, cat_name, weight = PRODUCT_CATEGORY_MAPPING["headphone"]
        assert cat_name == "Electronic Devices"
        assert weight == 0.9


class TestOrderItemSplit:
    """Tests for OrderItemSplit dataclass."""

    def test_create_split(self) -> None:
        """Test creating an OrderItemSplit."""
        split = OrderItemSplit(
            title="Test Item",
            quantity=2,
            amount=29.99,
            category_id=123,
            category_name="Test Category",
            confidence=0.85,
        )

        assert split.title == "Test Item"
        assert split.quantity == 2
        assert split.amount == 29.99
        assert split.category_id == 123
        assert split.category_name == "Test Category"
        assert split.confidence == 0.85


class TestOrderSplitter:
    """Tests for OrderSplitter class."""

    def test_init_with_defaults(self) -> None:
        """Test OrderSplitter initialization with defaults."""
        splitter = OrderSplitter()

        assert splitter.default_category_id == DEFAULT_CATEGORY_ID
        assert splitter.default_category_name == DEFAULT_CATEGORY_NAME
        assert splitter.confidence_threshold == 0.5
        assert splitter.min_split_amount == 5.0
        assert splitter.max_splits == 10

    def test_init_with_custom_values(self) -> None:
        """Test OrderSplitter with custom values."""
        splitter = OrderSplitter(
            default_category_id=999,
            default_category_name="Custom Default",
            confidence_threshold=0.7,
            min_split_amount=10.0,
            max_splits=5,
        )

        assert splitter.default_category_id == 999
        assert splitter.default_category_name == "Custom Default"
        assert splitter.confidence_threshold == 0.7
        assert splitter.min_split_amount == 10.0
        assert splitter.max_splits == 5

    def test_categorize_toy_item(self) -> None:
        """Test categorizing a toy item."""
        splitter = OrderSplitter()
        cat_id, cat_name, confidence = splitter.categorize_item("Lego Star Wars Set", 1)

        assert cat_name == "Kids Activities"
        assert confidence >= 0.7  # "lego" has 0.8 weight

    def test_categorize_protein_item(self) -> None:
        """Test categorizing a protein supplement."""
        splitter = OrderSplitter()
        cat_id, cat_name, confidence = splitter.categorize_item(
            "Whey Protein Powder Chocolate", 1
        )

        assert cat_name == "Gym Membership"
        assert confidence >= 0.8  # "protein" has 0.9 weight

    def test_categorize_vitamin_item(self) -> None:
        """Test categorizing a vitamin."""
        splitter = OrderSplitter()
        cat_id, cat_name, confidence = splitter.categorize_item(
            "Vitamin D3 5000IU", 1
        )

        assert cat_name == "Personal Care"
        assert confidence >= 0.7  # "vitamin" has 0.8 weight

    def test_categorize_headphones(self) -> None:
        """Test categorizing headphones."""
        splitter = OrderSplitter()
        cat_id, cat_name, confidence = splitter.categorize_item(
            "Bluetooth Noise Cancelling Headphones", 1
        )

        assert cat_name == "Electronic Devices"
        assert confidence >= 0.5  # Both "bluetooth" and "headphone" match

    def test_categorize_unknown_item(self) -> None:
        """Test categorizing an unknown item uses default."""
        splitter = OrderSplitter()
        cat_id, cat_name, confidence = splitter.categorize_item(
            "Unknown Product XYZ", 1
        )

        assert cat_id == DEFAULT_CATEGORY_ID
        assert cat_name == DEFAULT_CATEGORY_NAME
        assert confidence == 0.0

    def test_split_order_with_single_item(self) -> None:
        """Test splitting an order with a single item."""
        splitter = OrderSplitter()
        order = AmazonOrder(
            order_number="123-4567890-1234567",
            order_date=date.today(),
            grand_total=25.00,
            items=[
                AmazonItem(title="Test Product", quantity=1, price=25.00)
            ],
        )

        splits = splitter.split_order(order)

        assert len(splits) == 1
        assert splits[0].title == "Test Product"
        assert splits[0].quantity == 1
        assert splits[0].amount == 25.00

    def test_split_order_with_multiple_items(self) -> None:
        """Test splitting an order with multiple items."""
        splitter = OrderSplitter()
        order = AmazonOrder(
            order_number="123-4567890-1234567",
            order_date=date.today(),
            grand_total=75.00,
            items=[
                AmazonItem(title="Lego Set", quantity=1, price=30.00),
                AmazonItem(title="Protein Powder", quantity=1, price=45.00),
            ],
        )

        splits = splitter.split_order(order)

        assert len(splits) == 2

        # Items should be sorted by amount (highest first)
        assert splits[0].title == "Protein Powder"
        assert splits[0].amount == 45.00
        assert splits[0].category_name == "Gym Membership"

        assert splits[1].title == "Lego Set"
        assert splits[1].amount == 30.00
        assert splits[1].category_name == "Kids Activities"

    def test_split_empty_order(self) -> None:
        """Test splitting an order with no items."""
        splitter = OrderSplitter()
        order = AmazonOrder(
            order_number="123-4567890-1234567",
            order_date=date.today(),
            grand_total=50.00,
            items=[],
        )

        splits = splitter.split_order(order)

        assert len(splits) == 1
        assert splits[0].title == order.order_number
        assert splits[0].amount == 50.00
        assert splits[0].category_id == DEFAULT_CATEGORY_ID

    def test_should_split_single_item(self) -> None:
        """Test should_split returns False for single item."""
        splitter = OrderSplitter()
        order = AmazonOrder(
            order_number="123-4567890-1234567",
            order_date=date.today(),
            grand_total=25.00,
            items=[
                AmazonItem(title="Test Product", quantity=1, price=25.00)
            ],
        )

        assert splitter.should_split(order) is False

    def test_should_split_below_min_amount(self) -> None:
        """Test should_split returns False for low total."""
        splitter = OrderSplitter(min_split_amount=50.0)
        order = AmazonOrder(
            order_number="123-4567890-1234567",
            order_date=date.today(),
            grand_total=10.00,
            items=[
                AmazonItem(title="Item 1", quantity=1, price=5.00),
                AmazonItem(title="Item 2", quantity=1, price=5.00),
            ],
        )

        assert splitter.should_split(order) is False

    def test_should_split_too_many_items(self) -> None:
        """Test should_split returns False when too many items."""
        splitter = OrderSplitter(max_splits=3)
        items = [
            AmazonItem(title=f"Item {i}", quantity=1, price=10.00)
            for i in range(5)
        ]
        order = AmazonOrder(
            order_number="123-4567890-1234567",
            order_date=date.today(),
            grand_total=50.00,
            items=items,
        )

        assert splitter.should_split(order) is False

    def test_should_split_valid_order(self) -> None:
        """Test should_split returns True for valid order."""
        splitter = OrderSplitter()
        order = AmazonOrder(
            order_number="123-4567890-1234567",
            order_date=date.today(),
            grand_total=50.00,
            items=[
                AmazonItem(title="Item 1", quantity=1, price=25.00),
                AmazonItem(title="Item 2", quantity=1, price=25.00),
            ],
        )

        assert splitter.should_split(order) is True

    def test_get_split_summary(self) -> None:
        """Test getting a human-readable summary of splits."""
        splitter = OrderSplitter()

        splits = [
            OrderItemSplit(
                title="Lego Set",
                quantity=1,
                amount=30.00,
                category_id=18152963,
                category_name="Kids Activities",
                confidence=0.85,
            ),
            OrderItemSplit(
                title="Protein Powder",
                quantity=1,
                amount=45.00,
                category_id=18152162,
                category_name="Gym Membership",
                confidence=0.92,
            ),
        ]

        summary = splitter.get_split_summary(splits)

        assert "$30.00" in summary
        assert "Kids Activities" in summary
        assert "conf:85%" in summary
        assert "$45.00" in summary
        assert "Gym Membership" in summary
        assert "conf:92%" in summary

    def test_multi_match_boosts_confidence(self) -> None:
        """Test that multiple keyword matches increase confidence."""
        splitter = OrderSplitter()

        # "Kids" and "toys" both match Kids Activities
        cat_id, cat_name, confidence = splitter.categorize_item(
            "Kids toys building set", 1
        )

        assert cat_name == "Kids Activities"
        # Should have higher confidence due to multiple matches
        assert confidence > 0.7

    def test_specific_match_has_highest_confidence(self) -> None:
        """Test that more specific matches have higher confidence."""
        splitter = OrderSplitter()

        # "polly pocket" should have very high confidence (0.9)
        cat_id1, cat_name1, conf1 = splitter.categorize_item(
            "Polly Pocket Compact Playset", 1
        )

        # Generic "toy" should have lower confidence (0.8)
        cat_id2, cat_name2, conf2 = splitter.categorize_item(
            "Toy Building Blocks", 1
        )

        # Both should be Kids Activities
        assert cat_name1 == "Kids Activities"
        assert cat_name2 == "Kids Activities"

        # Polly pocket should have higher confidence
        assert conf1 > conf2
