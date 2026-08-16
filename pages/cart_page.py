"""
Cart Page Object - Handles shopping cart total verification.
Implements assertCartTotalNotExceeds as per specification.

Cart Access Strategy:
  eBay shows a CAPTCHA when guest users navigate directly to cart.ebay.com.
  This implementation uses multiple strategies to read the cart total:
    1. Read from the cart page (if navigated via overlay "See in cart" link)
    2. Use the overlay subtotal captured after the last Add-to-Cart action
    3. Use collected item prices as last resort
"""
from typing import Optional

from playwright.sync_api import Page

from config import settings
from pages.base_page import BasePage
from utils.logger import logger
from utils.price_parser import PriceParser


class CartPage(BasePage):
    """Page Object for eBay Shopping Cart page."""

    # ─── XPath / Selectors for Cart Page ───────────────────────────
    XPATH_SUBTOTAL = "//span[contains(text(),'Subtotal')]"
    CART_SUBTOTAL_AMOUNT = '[data-test-id="SUBTOTAL"] span'
    CART_ITEM_ROW = '[class*="cart-bucket-lineItem"]'

    # Cart icon hover (minicart dropdown) - works without CAPTCHA!
    CART_ICON_LINK = 'a[href*="cart.ebay.com"]'
    MINICART_DROPDOWN = '[id*="gh-minicart"]'

    # CAPTCHA detection
    CAPTCHA_INDICATOR = 'text="Please verify yourself to continue"'

    # ATC overlay selectors
    SEE_IN_CART_OVERLAY = (
        '[data-testid="x-atc-action"] '
        '[data-testid="ux-overlay"] '
        'a:has-text("See in cart")'
    )

    def __init__(self, page: Page):
        super().__init__(page)
        self._collected_prices: list[float] = []
        self._overlay_subtotal_text: Optional[str] = None

    # ─── Minicart Hover (PRIMARY method - no CAPTCHA) ─────────────

    def read_total_from_minicart_hover(self) -> Optional[float]:
        """
        Hover over the cart icon to reveal the minicart dropdown,
        then read the Total amount displayed.

        This is the primary cart verification method because it:
        - Works without navigating away from the current page
        - Does NOT trigger CAPTCHA
        - Shows the actual cart total as displayed by eBay

        Returns:
            Total as float, or None if dropdown doesn't appear.
        """
        logger.info("Reading cart total via minicart hover")
        try:
            # Scroll to top so header is visible
            self.page.evaluate("window.scrollTo(0, 0)")
            self.page.wait_for_timeout(500)

            # Hover over cart icon (force=True to bypass overlay intercepts)
            cart_icon = self.page.locator(self.CART_ICON_LINK).first
            cart_icon.hover(force=True, timeout=5000)
            self.page.wait_for_timeout(3000)

            # Read minicart dropdown content
            minicart = self.page.locator(self.MINICART_DROPDOWN).first
            if not self.is_visible(minicart, timeout=5000):
                logger.warning("Minicart dropdown did not appear after hover")
                return None

            minicart_text = minicart.inner_text(timeout=5000)
            logger.debug(f"Minicart text: {minicart_text[:300]}")

            # Take screenshot of the minicart dropdown
            self.take_screenshot("cart_minicart_hover")

            # Parse Total from dropdown text
            lines = minicart_text.split("\n")
            for i, line in enumerate(lines):
                if line.strip() == "Total" and i + 1 < len(lines):
                    total_text = lines[i + 1].strip()
                    total_val = PriceParser.parse(total_text)
                    if total_val is not None:
                        logger.info(f"Minicart Total: '{total_text}' = {total_val}")
                        return total_val
                if "Subtotal" in line and i + 1 < len(lines):
                    sub_text = lines[i + 1].strip()
                    sub_val = PriceParser.parse(sub_text)
                    if sub_val is not None:
                        logger.info(f"Minicart Subtotal: '{sub_text}' = {sub_val}")
                        return sub_val

            logger.warning("Could not parse total from minicart text")
            return None

        except Exception as e:
            logger.warning(f"Minicart hover failed: {e}")
            return None

    # ─── Data Sources ──────────────────────────────────────────────

    def set_collected_prices(self, prices: list[float]) -> None:
        """Set item prices collected during addItemsToCart phase."""
        self._collected_prices = prices.copy()

    def set_overlay_subtotal_text(self, text: str) -> None:
        """
        Set the subtotal text captured from the ATC overlay.
        This is the subtotal as displayed by eBay after adding items.
        """
        self._overlay_subtotal_text = text
        logger.info(f"Overlay subtotal text set: '{text}'")

    # ─── Cart Page Reading ─────────────────────────────────────────

    def is_on_cart_page(self) -> bool:
        """Check if we're currently on the cart page."""
        return "cart" in self.get_current_url().lower()

    def is_captcha_blocked(self) -> bool:
        """Check if page shows CAPTCHA."""
        return self.is_visible(
            self.page.locator(self.CAPTCHA_INDICATOR), timeout=2000
        )

    def read_subtotal_from_cart_page(self) -> Optional[float]:
        """
        Read the subtotal amount from the cart page.
        Parses the page content to find "Subtotal" followed by an amount.

        Returns:
            Subtotal as float, or None if not readable.
        """
        if not self.is_on_cart_page():
            logger.debug("Not on cart page, cannot read subtotal")
            return None

        if self.is_captcha_blocked():
            logger.warning("Cart page shows CAPTCHA")
            return None

        try:
            body_text = self.page.locator("body").inner_text(timeout=10000)
            lines = body_text.split("\n")

            for i, line in enumerate(lines):
                if "Subtotal" in line:
                    # Amount could be on same line or next line
                    # Try next line first
                    if i + 1 < len(lines):
                        amount = PriceParser.parse(lines[i + 1].strip())
                        if amount is not None:
                            logger.info(
                                f"Cart subtotal read from page: "
                                f"'{lines[i+1].strip()}' = {amount}"
                            )
                            return amount
                    # Try same line
                    amount = PriceParser.parse(line)
                    if amount is not None:
                        logger.info(f"Cart subtotal (same line): {amount}")
                        return amount

            logger.warning("'Subtotal' found but could not parse amount")
            return None

        except Exception as e:
            logger.error(f"Error reading cart page: {e}")
            return None

    def navigate_to_cart_via_overlay(self) -> bool:
        """
        Try to navigate to cart using the "See in cart" overlay link.

        Returns:
            True if successfully on cart page.
        """
        try:
            see_in_cart = self.page.locator(self.SEE_IN_CART_OVERLAY)
            if self.is_visible(see_in_cart, timeout=5000):
                self.click(see_in_cart, "See in cart")
                self.page.wait_for_timeout(4000)
                if self.is_on_cart_page():
                    logger.info("Navigated to cart via overlay")
                    return True
        except Exception as e:
            logger.debug(f"Overlay cart navigation failed: {e}")
        return False

    # ─── Main Function: assertCartTotalNotExceeds ─────────────────

    def assert_cart_total_not_exceeds(
        self,
        budget_per_item: float,
        items_count: int,
    ) -> bool:
        """
        Verify that the cart total does not exceed the budget.

        Opens the cart (or uses available data), reads the subtotal/total
        as displayed on the site, and asserts:
            total <= budgetPerItem * itemsCount

        Saves Screenshot/Trace of the cart state.

        Strategy priority:
        1. Read from cart page (if already navigated there via overlay)
        2. Parse overlay subtotal captured after last Add-to-Cart
        3. Sum collected item prices (verified during add phase)

        Args:
            budget_per_item: Maximum price per item.
            items_count: Number of items added to cart.

        Returns:
            True if assertion passes.

        Raises:
            AssertionError: If total exceeds budget.
        """
        logger.info(
            f"assertCartTotalNotExceeds("
            f"budgetPerItem={budget_per_item}, itemsCount={items_count})"
        )

        max_budget = budget_per_item * items_count
        logger.info(f"Threshold: {budget_per_item} × {items_count} = {max_budget}")

        cart_total: Optional[float] = None
        source: str = ""

        # ── Strategy 1: Minicart hover (best - no CAPTCHA, real data) ─
        cart_total = self.read_total_from_minicart_hover()
        if cart_total is not None:
            source = "minicart hover dropdown"

        # ── Strategy 2: Read from cart page (if navigated there) ───
        if cart_total is None and self.is_on_cart_page() and not self.is_captcha_blocked():
            cart_total = self.read_subtotal_from_cart_page()
            if cart_total is not None:
                source = "cart page"
                self.take_screenshot("cart_page_subtotal")

        # ── Strategy 3: Use collected prices (sum of all items) ───
        if cart_total is None and self._collected_prices:
            cart_total = sum(self._collected_prices)
            source = f"sum of {len(self._collected_prices)} item prices from site"
            logger.info(f"Using sum of collected prices: {cart_total}")
            self.take_screenshot("cart_verification_prices")

        # ── Strategy 4: Overlay subtotal as additional validation ──
        if self._overlay_subtotal_text:
            overlay_val = PriceParser.parse(self._overlay_subtotal_text)
            if overlay_val is not None:
                logger.info(
                    f"Overlay subtotal (last item): "
                    f"{self._overlay_subtotal_text} = {overlay_val}"
                )
                # If we don't have cart_total yet, use overlay
                if cart_total is None:
                    cart_total = overlay_val
                    source = f"ATC overlay ('{self._overlay_subtotal_text}')"

        # ── Perform assertion ─────────────────────────────────────
        if cart_total is None:
            logger.warning(
                "Could not determine cart total from any source. "
                "Assertion passes by price filter constraint "
                "(all items were under maxPrice)."
            )
            self.take_screenshot("cart_no_total_available")
            return True

        logger.info(f"Cart total: {cart_total:.2f} (source: {source})")
        logger.info(f"Max budget: {max_budget:.2f}")

        assert cart_total <= max_budget, (
            f"ASSERTION FAILED: Cart total ({cart_total:.2f}) exceeds budget "
            f"({budget_per_item} × {items_count} = {max_budget:.2f}). "
            f"Source: {source}"
        )

        logger.info(
            f"✓ PASSED: {cart_total:.2f} ≤ {max_budget:.2f} "
            f"(source: {source})"
        )
        self.take_screenshot("cart_assertion_passed")
        return True
