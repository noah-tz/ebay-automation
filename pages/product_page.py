"""
Product Page Object - Handles individual product pages.
Selects variants (size/color) and adds items to cart.
"""
import random
from typing import Optional

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.logger import logger
from utils.price_parser import PriceParser


class ProductPage(BasePage):
    """Page Object for eBay Product/Item detail page."""

    # ─── Selectors ─────────────────────────────────────────────────
    ADD_TO_CART_BTN = 'a[data-testid="ux-call-to-action"]:has-text("Add to cart")'
    ADD_TO_CART_BTN_FALLBACK = 'a:has-text("Add to cart"), button:has-text("Add to cart")'
    BUY_IT_NOW_BTN = 'a:has-text("Buy It Now")'

    # Variant selectors
    SIZE_SELECT = 'select[id*="SIZE"], select[aria-label*="Size"]'
    COLOR_SELECT = 'select[id*="Color"], select[aria-label*="Color"]'
    VARIANT_SELECT = 'select[id*="msku-sel"]'
    VARIANT_BUTTONS = '[data-testid*="variant"] button, .x-msku button'

    # Price on product page
    PRODUCT_PRICE = '[data-testid="x-price-primary"] span, .x-price-primary span'

    # Cart confirmation
    CART_CONFIRMATION = '[class*="cart-bucket"], [aria-label*="Added to cart"]'
    VIEW_CART_BTN = 'a:has-text("View cart"), a:has-text("Go to cart")'

    # Add-to-cart overlay (shown after successful add)
    ATC_OVERLAY = '[data-testid="x-atc-action"] [data-testid="ux-overlay"][aria-hidden="false"]'
    ATC_OVERLAY_SEE_CART = '[data-testid="x-atc-action"] [data-testid="ux-overlay"] a:has-text("See in cart")'

    # Error state
    ITEM_ENDED = 'text="This listing has ended"'

    def __init__(self, page: Page):
        super().__init__(page)
        self._last_overlay_subtotal: Optional[str] = None

    # ─── Actions ───────────────────────────────────────────────────

    def open_product(self, url: str) -> bool:
        """
        Navigate to a product page.

        Args:
            url: Product URL.

        Returns:
            True if page loaded successfully, False if item ended/unavailable.
        """
        logger.info(f"Opening product: {url[:80]}...")
        self.navigate(url)
        self.page.wait_for_timeout(2000)

        # Check if item has ended
        if self.is_visible(self.page.locator(self.ITEM_ENDED), timeout=2000):
            logger.warning("Item listing has ended, skipping")
            return False

        return True

    def select_random_variant(self) -> None:
        """
        Select random variants (size/color) if required.
        Tries dropdown selects first, then clickable buttons.
        """
        self._try_select_dropdown(self.SIZE_SELECT, "Size")
        self._try_select_dropdown(self.COLOR_SELECT, "Color")
        self._try_select_dropdown(self.VARIANT_SELECT, "Variant")
        self._try_select_variant_buttons()

    def _try_select_dropdown(self, selector: str, name: str) -> None:
        """Try to select a random option from a dropdown."""
        try:
            dropdown = self.page.locator(selector).first
            if not self.is_visible(dropdown, timeout=2000):
                return

            # Get available options (skip the first "Select" placeholder)
            options = dropdown.locator("option").all()
            valid_options = []
            for opt in options:
                value = opt.get_attribute("value") or ""
                text = opt.text_content() or ""
                # Skip placeholders and disabled options
                if value and value != "-1" and "Select" not in text:
                    disabled = opt.get_attribute("disabled")
                    if disabled is None:
                        valid_options.append(value)

            if valid_options:
                chosen = random.choice(valid_options)
                dropdown.select_option(value=chosen, timeout=5000)
                logger.info(f"Selected {name}: {chosen}")
                self.page.wait_for_timeout(1000)

        except Exception as e:
            logger.debug(f"No {name} dropdown found or selection failed: {e}")

    def _try_select_variant_buttons(self) -> None:
        """Try to click a random variant button if available."""
        try:
            buttons = self.page.locator(self.VARIANT_BUTTONS)
            count = buttons.count()
            if count == 0:
                return

            # Find enabled buttons
            enabled_buttons = []
            for i in range(count):
                btn = buttons.nth(i)
                if btn.is_enabled() and btn.is_visible():
                    aria_checked = btn.get_attribute("aria-checked")
                    # Skip already-selected variants
                    if aria_checked != "true":
                        enabled_buttons.append(btn)

            if enabled_buttons:
                chosen = random.choice(enabled_buttons)
                chosen.click(timeout=5000)
                logger.info("Selected variant via button click")
                self.page.wait_for_timeout(1000)

        except Exception as e:
            logger.debug(f"Variant button selection failed: {e}")

    def add_to_cart(self) -> bool:
        """
        Click the "Add to cart" button.
        Waits for the ATC overlay confirmation to appear and captures
        the overlay subtotal for cart verification.

        Returns:
            True if add to cart was successful, False otherwise.
        """
        try:
            # Try primary selector
            add_btn = self.page.locator(self.ADD_TO_CART_BTN).first
            if not self.is_visible(add_btn, timeout=5000):
                # Try fallback selector
                add_btn = self.page.locator(self.ADD_TO_CART_BTN_FALLBACK).first
                if not self.is_visible(add_btn, timeout=3000):
                    logger.warning("Add to Cart button not found")
                    return False

            self.click(add_btn, "Add to Cart")

            # Wait for the ATC overlay/confirmation
            atc_overlay = self.page.locator(self.ATC_OVERLAY)
            try:
                atc_overlay.wait_for(state="visible", timeout=10000)

                # Wait for overlay to finish loading
                # (changes from "Adding to your cart" → "Added to cart")
                try:
                    self.page.locator(
                        '[data-testid="x-atc-action"] [data-testid="ux-overlay"] '
                        ':text("Added to cart")'
                    ).wait_for(state="visible", timeout=10000)
                    self.page.wait_for_timeout(500)  # Let subtotal render
                except Exception:
                    # Even if "Added to cart" text doesn't appear,
                    # the overlay might still have useful data
                    self.page.wait_for_timeout(2000)

                logger.info("Item added to cart successfully (overlay confirmed)")

                # Capture subtotal from the fully-loaded overlay
                self._capture_overlay_subtotal(atc_overlay)

            except Exception:
                self.page.wait_for_timeout(3000)
                logger.info("Item added to cart (no overlay confirmation)")

            return True

        except Exception as e:
            logger.error(f"Failed to add item to cart: {e}")
            self.take_screenshot("add_to_cart_failed")
            return False

    def _capture_overlay_subtotal(self, overlay) -> None:
        """Capture the subtotal displayed in the ATC overlay."""
        try:
            overlay_text = overlay.inner_text(timeout=5000)
            logger.debug(f"Overlay text (first 300 chars): {overlay_text[:300]}")
            lines = overlay_text.split("\n")
            for i, line in enumerate(lines):
                if "Subtotal" in line or "subtotal" in line.lower():
                    # Amount might be on same line or next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        parsed = PriceParser.parse(next_line)
                        if parsed is not None:
                            self._last_overlay_subtotal = next_line
                            logger.info(
                                f"Overlay subtotal captured: {next_line} = {parsed}"
                            )
                            return
                    # Try parsing the same line
                    parsed = PriceParser.parse(line)
                    if parsed is not None:
                        self._last_overlay_subtotal = line
                        logger.info(f"Overlay subtotal (same line): {line} = {parsed}")
                        return

            # If "Subtotal" not found, look for price-like patterns
            for line in lines:
                if "$" in line or "ILS" in line:
                    parsed = PriceParser.parse(line.strip())
                    if parsed is not None:
                        self._last_overlay_subtotal = line.strip()
                        logger.info(f"Overlay price captured: {line.strip()}")
                        return

            logger.debug("Could not find subtotal in overlay text")
        except Exception as e:
            logger.debug(f"Could not capture overlay subtotal: {e}")

    def get_last_overlay_subtotal(self) -> Optional[str]:
        """Return the last captured overlay subtotal text."""
        return self._last_overlay_subtotal

    def click_see_in_cart(self) -> bool:
        """
        Click "See in cart" link inside the ATC overlay.
        This navigates to the cart page without CAPTCHA.

        Returns:
            True if navigation was successful.
        """
        try:
            see_in_cart = self.page.locator(self.ATC_OVERLAY_SEE_CART)
            if self.is_visible(see_in_cart, timeout=5000):
                self.click(see_in_cart, "See in cart (overlay)")
                self.page.wait_for_timeout(4000)
                if "cart" in self.get_current_url().lower():
                    logger.info("Navigated to cart via overlay link")
                    return True
        except Exception as e:
            logger.debug(f"Could not click 'See in cart': {e}")
        return False

    def get_product_price(self) -> Optional[str]:
        """Get the price displayed on the product page."""
        try:
            price_el = self.page.locator(self.PRODUCT_PRICE).first
            if self.is_visible(price_el, timeout=3000):
                return self.get_text(price_el)
        except Exception:
            pass
        return None
