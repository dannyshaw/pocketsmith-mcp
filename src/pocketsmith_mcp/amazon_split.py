"""Amazon order splitting utilities.

This module provides functionality to split Amazon orders into multiple
categorized transactions based on product types.
"""

from dataclasses import dataclass
from typing import Any

from pocketsmith_mcp.amazon_models import AmazonOrder, AmazonItem

# Product category mapping
# Key: product keyword patterns
# Value: (category_id, category_name, confidence_weight)
PRODUCT_CATEGORY_MAPPING: dict[str, tuple[int, str, float]] = {
    # Kids Toys / Kids Activities
    "kids": (18152963, "Kids Activities", 1.0),
    "kids toys": (18152963, "Kids Activities", 1.0),
    "toy": (18152963, "Kids Activities", 0.8),
    "lego": (18152963, "Kids Activities", 0.8),
    "building blocks": (18152963, "Kids Activities", 0.8),
    "puzzle": (18152963, "Kids Activities", 0.7),
    "game": (18152963, "Kids Activities", 0.6),
    "dinosaur": (18152963, "Kids Activities", 0.8),
    "doll": (18152963, "Kids Activities", 0.8),
    "polly pocket": (18152963, "Kids Activities", 0.9),
    "art smock": (18152963, "Kids Activities", 0.8),
    "sticker": (18152963, "Kids Activities", 0.7),
    "fidget": (18152963, "Kids Activities", 0.8),
    "balloon": (18152963, "Kids Activities", 0.7),
    "pinball": (18152963, "Kids Activities", 0.8),
    "student": (18152963, "Kids Activities", 0.7),
    "children": (18152963, "Kids Activities", 0.6),
    "kids bike": (18152963, "Kids Activities", 0.8),
    "bike basket": (18152963, "Kids Activities", 0.7),
    "horn": (18152963, "Kids Activities", 0.7),
    "bike bell": (18152963, "Kids Activities", 0.7),
    "water bottle": (18150899, "Household", 0.5),  # Default to Household
    "bike": (18150893, "Recreation", 0.6),  # Default to Recreation

    # Gym / Fitness / Health
    "protein": (18152162, "Gym Membership", 0.9),
    "shaker": (18152162, "Gym Membership", 0.9),
    "gym": (18152162, "Gym Membership", 0.8),
    "workout": (18152162, "Gym Membership", 0.7),
    "fitness": (18152162, "Gym Membership", 0.8),
    "exercise": (18152162, "Gym Membership", 0.7),
    "yoga": (18152162, "Gym Membership", 0.8),
    "yoga pants": (18152162, "Gym Membership", 0.9),
    "skipping rope": (18152162, "Gym Membership", 0.9),
    "jump rope": (18152162, "Gym Membership", 0.9),
    "push up bars": (18152162, "Gym Membership", 0.9),
    "pushup": (18152162, "Gym Membership", 0.9),
    "dumbbell": (18152162, "Gym Membership", 0.8),

    # Supplements / Health / Personal Care
    "vitamin": (18150896, "Personal Care", 0.8),
    "b12": (18150896, "Personal Care", 0.8),
    "magnesium": (18150896, "Personal Care", 0.8),
    "creatine": (18150896, "Personal Care", 0.8),
    "supplement": (18150896, "Personal Care", 0.8),
    "capsule": (18150896, "Personal Care", 0.8),
    "tablet": (18150896, "Personal Care", 0.7),
    "probiotic": (18150896, "Personal Care", 0.7),
    "probiotics": (18150896, "Personal Care", 0.7),
    "medicine": (18150920, "Medical", 0.8),
    "nasal spray": (18150920, "Medical", 0.8),
    "sinus rinse": (18150920, "Medical", 0.9),
    "bandage": (18150920, "Medical", 0.9),
    "plasters": (18150920, "Medical", 0.8),

    # Electronics
    "bluetooth": (18372191, "Electronic Devices", 0.6),
    "headphone": (18372191, "Electronic Devices", 0.9),
    "earbuds": (18372191, "Electronic Devices", 0.9),
    "ear plug": (18372191, "Electronic Devices", 0.8),
    "charger": (18372191, "Electronic Devices", 0.7),
    "usb": (18372191, "Electronic Devices", 0.6),
    "cable": (18372191, "Electronic Devices", 0.6),
    "adapter": (18372191, "Electronic Devices", 0.7),
    "mouse": (18372191, "Electronic Devices", 0.7),
    "keyboard": (18372191, "Electronic Devices", 0.8),
    "webcam": (18372191, "Electronic Devices", 0.7),
    "speaker": (18372191, "Electronic Devices", 0.7),
    "transmitter": (18372191, "Electronic Devices", 0.7),
    "audio": (18372191, "Electronic Devices", 0.6),

    # Household
    "milk frother": (18150899, "Household", 0.9),
    "frother": (18150899, "Household", 0.8),
    "jar": (18150899, "Household", 0.8),
    "container": (18150899, "Household", 0.7),
    "storage": (18150899, "Household", 0.7),
    "bottle": (18150899, "Household", 0.6),
    "tumbler": (18150899, "Household", 0.8),
    "cup": (18150899, "Household", 0.7),
    "mug": (18150899, "Household", 0.8),
    "iron": (18150899, "Household", 0.8),
    "steamer": (18150899, "Household", 0.8),
    "cleaner": (18150899, "Household", 0.8),
    "vacuum": (18150899, "Household", 0.8),
    "broom": (18150899, "Household", 0.8),
    "towel": (18150899, "Household", 0.7),
    "sheet": (18150899, "Household", 0.7),
    "curtain": (18150899, "Household", 0.6),
    "mat": (18150899, "Household", 0.7),
    "bath mat": (18150899, "Household", 0.8),
    "shower": (18150899, "Household", 0.8),
    "soap": (18150899, "Household", 0.7),
    "laundry": (18150899, "Household", 0.7),
    "paper": (18150899, "Household", 0.7),
    "toilet": (18150899, "Household", 0.7),

    # Home Improvement
    "curtain rod": (18150914, "Home Improvement", 0.9),
    "light bulb": (18150914, "Home Improvement", 0.9),
    "lighting": (18150914, "Home Improvement", 0.8),
    "led": (18150914, "Home Improvement", 0.8),
    "switch": (18150914, "Home Improvement", 0.7),
    "power point": (18150914, "Home Improvement", 0.8),
    "outlet": (18150914, "Home Improvement", 0.8),
    "wall mount": (18150914, "Home Improvement", 0.7),
    "shelf": (18150914, "Home Improvement", 0.7),
    "hooks": (18150914, "Home Improvement", 0.7),

    # Clothing
    "sock": (18150932, "Clothing", 0.8),
    "underwear": (18150932, "Clothing", 0.8),
    "underwear": (18150932, "Clothing", 0.8),
    "shirt": (18150932, "Clothing", 0.8),
    "pants": (18150932, "Clothing", 0.8),
    "shorts": (18150932, "Clothing", 0.8),
    "dress": (18150932, "Clothing", 0.8),
    "clothing": (18150932, "Clothing", 0.8),
    "sunglasses": (18150932, "Clothing", 0.9),
    "glasses": (18150932, "Clothing", 0.9),
    "shoes": (18150932, "Clothing", 0.8),

    # Books / Media
    "book": (18150929, "Media", 0.7),
    "kindle": (18150929, "Media", 0.9),
    "audio": (18150929, "Media", 0.8),
    "yoto": (18150929, "Media", 0.9),
    "stories": (18150929, "Media", 0.7),
    "journal": (18150929, "Media", 0.8),
    "coloring": (18150929, "Media", 0.9),
    "sticker": (18150929, "Media", 0.7),
    "workbook": (18150929, "Media", 0.8),

    # Automotive
    "car charger": (18150953, "Automotive", 0.8),
    "tire": (18150953, "Automotive", 0.9),
    "wheel": (18150953, "Automotive", 0.8),
    "car wash": (19866864, "Car Wash", 0.9),
    "car cleaning": (19866864, "Car Wash", 0.8),
    "fan": (18150953, "Automotive", 0.7),

    # Camping / Outdoors
    "tent": (22264471, "Camping", 0.9),
    "sleeping bag": (22264471, "Camping", 0.9),
    "camp": (22264471, "Camping", 0.9),
    "lantern": (22264471, "Camping", 0.9),

    # Personal Care
    "ear plug": (18150896, "Personal Care", 0.9),
    "earplugs": (18150896, "Personal Care", 0.9),
    "hearing protection": (18150896, "Personal Care", 0.9),
    "sleep": (18150896, "Personal Care", 0.7),

    # Recreation
    "drone": (18150902, "Recreation", 0.9),
    "rc": (18150902, "Recreation", 0.9),
    "remote control": (18150902, "Recreation", 0.9),
    "radio": (18150902, "Recreation", 0.8),

    # Tools / DIY
    "drill": (18150914, "Home Improvement", 0.7),
    "tool": (18150914, "Home Improvement", 0.7),
    "kit": (18150914, "Home Improvement", 0.6),

    # Gift items
    "gift": (18152996, "Gifts", 0.7),

    # Food / Groceries
    "tea": (18150158, "Groceries", 0.8),
    "curry": (18150158, "Groceries", 0.8),
    "spices": (18150158, "Groceries", 0.8),
    "salt": (18150158, "Groceries", 0.8),
    "snack": (18150158, "Groceries", 0.8),
    "chocolate": (18150158, "Groceries", 0.8),
    "coffee": (18150158, "Groceries", 0.8),
    "inulin": (18150158, "Groceries", 0.7),
    "agarve": (18150158, "Groceries", 0.7),
}

# Fallback categories
DEFAULT_CATEGORY_ID = 18150899  # Household
DEFAULT_CATEGORY_NAME = "Household"


@dataclass
class OrderItemSplit:
    """A single item from a split Amazon order."""

    title: str
    quantity: int
    amount: float  # The portion of total amount for this item
    category_id: int
    category_name: str
    confidence: float  # 0.0 to 1.0


class OrderSplitter:
    """Splits Amazon orders into categorized items.

    This class takes an Amazon order and splits it into multiple categorized
    items based on product titles and quantities.
    """

    def __init__(
        self,
        default_category_id: int = DEFAULT_CATEGORY_ID,
        default_category_name: str = DEFAULT_CATEGORY_NAME,
        confidence_threshold: float = 0.5,
        min_split_amount: float = 5.0,
        max_splits: int = 10,
    ):
        """Initialize the order splitter.

        Args:
            default_category_id: Category ID to use for unmatched items
            default_category_name: Category name to use for unmatched items
            confidence_threshold: Minimum confidence to auto-categorize
            min_split_amount: Minimum order amount to attempt splitting
            max_splits: Maximum number of items to split an order into
        """
        self.default_category_id = default_category_id
        self.default_category_name = default_category_name
        self.confidence_threshold = confidence_threshold
        self.min_split_amount = min_split_amount
        self.max_splits = max_splits

    def split_order(self, order: AmazonOrder) -> list[OrderItemSplit]:
        """Split an Amazon order into categorized items.

        Args:
            order: The Amazon order to split

        Returns:
            List of OrderItemSplit objects with category assignments
        """
        if not order.items:
            # No items to split, return as single item
            return [
                OrderItemSplit(
                    title=order.order_number,
                    quantity=1,
                    amount=order.grand_total,
                    category_id=self.default_category_id,
                    category_name=self.default_category_name,
                    confidence=0.0,
                )
            ]

        results = []

        # Sort items by amount descending (largest items get better categorization)
        sorted_items = sorted(
            order.items,
            key=lambda i: (i.price or 0) * i.quantity,
            reverse=True,
        )

        # Categorize each item
        for item in sorted_items:
            category_id, category_name, confidence = self.categorize_item(
                item.title, item.quantity
            )

            # Calculate item amount
            item_amount = (item.price or 0) * item.quantity

            results.append(
                OrderItemSplit(
                    title=item.title,
                    quantity=item.quantity,
                    amount=item_amount,
                    category_id=category_id,
                    category_name=category_name,
                    confidence=confidence,
                )
            )

        return results

    def categorize_item(self, title: str, quantity: int) -> tuple[int, str, float]:
        """Categorize an item based on its title.

        Args:
            title: The item title
            quantity: Item quantity

        Returns:
            Tuple of (category_id, category_name, confidence)
        """
        title_lower = title.lower()

        # Find matching categories
        matches: list[tuple[int, str, float]] = []

        for keyword, (cat_id, cat_name, weight) in PRODUCT_CATEGORY_MAPPING.items():
            if keyword in title_lower:
                matches.append((cat_id, cat_name, weight))

        if matches:
            # Sort by weight (confidence) descending
            matches.sort(key=lambda m: m[2], reverse=True)
            best_cat_id, best_cat_name, best_weight = matches[0]

            # Calculate final confidence
            # More matches = higher confidence
            match_count = len(matches)
            confidence = min(1.0, 0.3 + (best_weight * 0.5) + (match_count * 0.1))

            return best_cat_id, best_cat_name, confidence

        # No match found, use default
        return (
            self.default_category_id,
            self.default_category_name,
            0.0,  # No confidence
        )

    def should_split(self, order: AmazonOrder) -> bool:
        """Determine if an order should be split.

        Args:
            order: The Amazon order to check

        Returns:
            True if the order should be split
        """
        # Don't split single small items
        if len(order.items) <= 1:
            return False

        # Don't split if total is too small
        if order.grand_total < self.min_split_amount:
            return False

        # Don't split if too many items
        if len(order.items) > self.max_splits:
            return False

        return True

    def get_split_summary(self, splits: list[OrderItemSplit]) -> str:
        """Get a human-readable summary of splits.

        Args:
            splits: The split items

        Returns:
            Summary string
        """
        lines = []
        for split in splits:
            conf_pct = int(split.confidence * 100)
            lines.append(
                f"  - ${split.amount:.2f} → {split.category_name} "
                f"(conf:{conf_pct}%) {split.title[:50]}"
            )
        return "\n".join(lines)
