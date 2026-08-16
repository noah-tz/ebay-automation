"""
Price parsing utility.
Handles various eBay price formats with currency detection.
Supports currency-aware comparison to avoid cross-currency mismatches.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Price:
    """Represents a parsed price with currency."""

    amount: float
    currency: str  # "USD", "ILS", "EUR", "GBP"

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"


class PriceParser:
    """Parses price strings from eBay pages into structured Price objects."""

    # Currency detection patterns (order matters - more specific first)
    CURRENCY_PATTERNS = [
        (re.compile(r"ILS\s*([\d,]+\.?\d*)"), "ILS"),
        (re.compile(r"US\s*\$\s*([\d,]+\.?\d*)"), "USD"),
        (re.compile(r"GBP\s*([\d,]+\.?\d*)"), "GBP"),
        (re.compile(r"£\s*([\d,]+\.?\d*)"), "GBP"),
        (re.compile(r"€\s*([\d,]+\.?\d*)"), "EUR"),
        (re.compile(r"EUR\s*([\d,]+\.?\d*)"), "EUR"),
        (re.compile(r"\$\s*([\d,]+\.?\d*)"), "USD"),  # bare $ last (ambiguous)
    ]

    @staticmethod
    def parse_with_currency(price_text: str) -> Optional[Price]:
        """
        Parse a price string into a Price object (amount + currency).

        Args:
            price_text: Raw price text from eBay (e.g., "ILS 29,552.00", "US $29.99")

        Returns:
            Price object with amount and currency, or None if parsing fails.
        """
        if not price_text:
            return None

        # Handle price ranges - take the first price
        price_text = price_text.split(" to ")[0].strip()

        for pattern, currency in PriceParser.CURRENCY_PATTERNS:
            match = pattern.search(price_text)
            if match:
                price_str = match.group(1).replace(",", "")
                try:
                    return Price(amount=float(price_str), currency=currency)
                except ValueError:
                    continue

        # Fallback: try to find any number (unknown currency)
        numbers = re.findall(r"[\d,]+\.?\d*", price_text)
        if numbers:
            try:
                return Price(amount=float(numbers[0].replace(",", "")), currency="USD")
            except ValueError:
                return None

        return None

    @staticmethod
    def parse(price_text: str) -> Optional[float]:
        """
        Parse a price string into a float value (backward compatible).

        Args:
            price_text: Raw price text from eBay.

        Returns:
            Float price value, or None if parsing fails.
        """
        result = PriceParser.parse_with_currency(price_text)
        return result.amount if result else None

    @staticmethod
    def detect_currency(price_text: str) -> Optional[str]:
        """Detect the currency from a price string."""
        result = PriceParser.parse_with_currency(price_text)
        return result.currency if result else None

    @staticmethod
    def is_within_budget(
        price_text: str,
        max_price: float,
        expected_currency: str = "USD",
    ) -> bool:
        """
        Check if a price is within the given budget.
        Only compares if currency matches expected_currency.

        Args:
            price_text: Raw price text.
            max_price: Maximum allowed price.
            expected_currency: Currency to compare against (default USD).

        Returns:
            True if within budget and same currency, False otherwise.
        """
        result = PriceParser.parse_with_currency(price_text)
        if result is None:
            return False
        if result.currency != expected_currency:
            # Cross-currency comparison is invalid
            return False
        return result.amount <= max_price
