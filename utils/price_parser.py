"""
Price parsing utility.
Handles various eBay price formats and currency conversions.
"""
import re
from typing import Optional


class PriceParser:
    """Parses price strings from eBay pages into float values."""

    # Pattern matches prices like: $29.99, ILS 29,552.00, US $100.00, etc.
    PRICE_PATTERN = re.compile(
        r"(?:ILS|US\s*\$|\$|EUR|GBP|£|€)\s*([\d,]+\.?\d*)"
    )

    @staticmethod
    def parse(price_text: str) -> Optional[float]:
        """
        Parse a price string into a float value.

        Args:
            price_text: Raw price text from eBay (e.g., "ILS 29,552.00", "$29.99")

        Returns:
            Float price value, or None if parsing fails.
        """
        if not price_text:
            return None

        # Handle price ranges (e.g., "$10.00 to $20.00") - take the first price
        price_text = price_text.split(" to ")[0].strip()

        match = PriceParser.PRICE_PATTERN.search(price_text)
        if match:
            price_str = match.group(1).replace(",", "")
            try:
                return float(price_str)
            except ValueError:
                return None

        # Fallback: try to find any number
        numbers = re.findall(r"[\d,]+\.?\d*", price_text)
        if numbers:
            try:
                return float(numbers[0].replace(",", ""))
            except ValueError:
                return None

        return None

    @staticmethod
    def is_within_budget(price_text: str, max_price: float) -> bool:
        """Check if a price is within the given budget."""
        price = PriceParser.parse(price_text)
        if price is None:
            return False
        return price <= max_price
