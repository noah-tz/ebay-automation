"""
Shopping Business Process - Complete E2E shopping flow orchestration.

Implements all 4 core functions from the specification:
1. Login / Authentication
2. searchItemsByNameUnderPrice
3. addItemsToCart
4. assertCartTotalNotExceeds

Uses Page element repositories (POM) for selectors,
and BaseBP for common browser interactions.
"""
import random
import re
from dataclasses import dataclass, field
from typing import Optional

import allure
from playwright.sync_api import Page

from bp.base_bp import BaseBP
from config import settings
from pages import LoginPage, SearchPage, ProductPage, CartPage
from utils.logger import logger
from utils.price_parser import PriceParser
from utils.screenshot import take_screenshot


@dataclass
class AddToCartResult:
    """Result of the addItemsToCart operation."""

    added_count: int = 0
    collected_prices: list[float] = field(default_factory=list)
    last_overlay_subtotal: Optional[str] = None
    skipped_urls: list[str] = field(default_factory=list)


class ShoppingBP(BaseBP):
    """
    Business Process for the complete eBay shopping flow.

    Encapsulates all interaction logic, using Page classes
    as element repositories (POM pattern) and BaseBP for
    common browser actions.
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self._collected_prices: list[float] = []
        self._overlay_subtotal_text: Optional[str] = None

    # ══════════════════════════════════════════════════════════════
    # STEP 1: LOGIN
    # ══════════════════════════════════════════════════════════════

    @allure.step("Login / Authentication")
    def login(self, username: str = "", password: str = "") -> bool:
        """
        Perform login with credentials, or skip to guest mode.

        Args:
            username: eBay username/email. Falls back to .env if empty.
            password: eBay password. Falls back to .env if empty.

        Returns:
            True if successful.
        """
        _username = username or settings.EBAY_USERNAME
        _password = password or settings.EBAY_PASSWORD

        if not _username or not _password:
            return self._skip_login()

        try:
            self.navigate(settings.LOGIN_URL)
            self.fill(LoginPage.USERNAME_INPUT, _username, "Username")
            self.click(LoginPage.CONTINUE_BTN, "Continue button")
            self.wait_for_element(LoginPage.PASSWORD_INPUT, timeout=10000)
            self.fill(LoginPage.PASSWORD_INPUT, _password, "Password")
            self.click(LoginPage.SIGN_IN_BTN, "Sign In button")
            self.wait_for_url_contains("ebay.com", timeout=15000)
            logger.info("Login successful!")
            take_screenshot(self.page, "login_success")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            take_screenshot(self.page, "login_failed")
            return False

    def _skip_login(self) -> bool:
        """Navigate to eBay homepage as guest."""
        logger.info("Skipping login - using guest mode")
        self.navigate(settings.BASE_URL)
        self.wait_for_load()

        if "Error Page" in self.get_page_title():
            logger.warning("Got error page, clicking 'Go to homepage'")
            if self.is_visible(LoginPage.GO_TO_HOMEPAGE, timeout=5000):
                self.click(LoginPage.GO_TO_HOMEPAGE, "Go to homepage")
                self.wait_for_load()

        return True

    # ══════════════════════════════════════════════════════════════
    # STEP 2: SEARCH ITEMS BY NAME UNDER PRICE
    # ══════════════════════════════════════════════════════════════

    @allure.step("searchItemsByNameUnderPrice('{query}', maxPrice={max_price}, limit={limit})")
    def search_items_by_name_under_price(
        self,
        query: str,
        max_price: float,
        limit: int = 5,
    ) -> list[str]:
        """
        Search for items by name, filter by max price, return up to `limit` URLs.

        Behavior:
        - Performs search by query
        - Uses price filter (min/max) via URL params
        - Extracts items via XPath, verifying price <= maxPrice
        - Supports pagination if fewer than `limit` items on current page
        - Returns array of URLs meeting price criteria (may be < limit or empty)

        Args:
            query: Search term (e.g., "shoes").
            max_price: Maximum price per item.
            limit: Max number of URLs to return (default: 5).

        Returns:
            List of item URLs (up to `limit`).
        """
        logger.info(
            f"searchItemsByNameUnderPrice('{query}', "
            f"maxPrice={max_price}, limit={limit})"
        )

        self._perform_search(query)
        self._apply_price_filter(max_price)

        # Collect items via XPath with pagination
        collected_urls: list[str] = []
        max_pages = 3  # Documented assumption in README

        for page_num in range(1, max_pages + 1):
            logger.info(f"Processing page {page_num}...")
            results = self._extract_results_xpath(limit)

            for item in results:
                if len(collected_urls) >= limit:
                    break

                price_value = PriceParser.parse(item["price"])

                if price_value is not None and price_value <= max_price:
                    if item["url"] not in collected_urls:
                        collected_urls.append(item["url"])
                        logger.info(
                            f"  [{len(collected_urls)}/{limit}] "
                            f"{item['title'][:40]}... @ {item['price']}"
                        )
                elif price_value is None and item["url"]:
                    if item["url"] not in collected_urls:
                        collected_urls.append(item["url"])
                        logger.info(
                            f"  [{len(collected_urls)}/{limit}] "
                            f"{item['title'][:40]}... @ {item['price']} (unverified)"
                        )

            if len(collected_urls) >= limit:
                break

            # Pagination
            if page_num < max_pages and self._has_next_page():
                if not self._go_to_next_page():
                    break
            else:
                if len(collected_urls) < limit:
                    logger.info("No more pages available")
                break

        logger.info(f"searchItemsByNameUnderPrice: found {len(collected_urls)} items")
        take_screenshot(self.page, f"search_results_{query}")
        return collected_urls

    def _perform_search(self, query: str) -> None:
        """Enter query and submit search."""
        selectors = [
            SearchPage.SEARCH_INPUT,
            SearchPage.SEARCH_INPUT_FALLBACK,
            SearchPage.SEARCH_INPUT_PLACEHOLDER,
            SearchPage.SEARCH_COMBOBOX,
        ]

        found_selector = None
        for selector in selectors:
            if self.is_visible(selector, timeout=3000):
                found_selector = selector
                break

        if found_selector is None:
            search_url = (
                f"{settings.BASE_URL}/sch/i.html"
                f"?_nkw={query.replace(' ', '+')}&_sacat=0"
            )
            self.navigate(search_url)
            self.wait_for_load()
            return

        self.click(found_selector)
        self.fill(found_selector, query)
        self.press_key(found_selector, "Enter")
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for_element(
            f"xpath={SearchPage.XPATH_RESULT_ITEMS}", state="attached", timeout=15000
        )

    def _apply_price_filter(self, max_price: float, min_price: float = 0) -> None:
        """Apply price filter via URL parameters."""
        current_url = self.get_current_url()
        if "ebay.com/sch" not in current_url:
            return

        url_clean = re.sub(r"&_udhi=[^&]*", "", current_url)
        url_clean = re.sub(r"&_udlo=[^&]*", "", url_clean)
        new_url = f"{url_clean}&_udlo={int(min_price)}&_udhi={int(max_price)}"

        logger.info(f"Applying price filter: max={max_price}")
        self.navigate(new_url)
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for_element(
            f"xpath={SearchPage.XPATH_RESULT_ITEMS}", state="attached", timeout=15000
        )

    def _extract_results_xpath(self, limit: int) -> list[dict]:
        """Extract search result items using XPath selectors."""
        items = self.page.locator(f"xpath={SearchPage.XPATH_RESULT_ITEMS}")
        count = items.count()

        results = []
        for i in range(min(count, limit * 2)):
            item = items.nth(i)
            try:
                url = item.locator(f"xpath={SearchPage.XPATH_ITEM_LINK}").first.get_attribute("href", timeout=3000) or ""
                title = item.locator(f"xpath={SearchPage.XPATH_ITEM_TITLE}").first.text_content(timeout=3000) or ""
                price_text = item.locator(f"xpath={SearchPage.XPATH_ITEM_PRICE}").first.text_content(timeout=3000) or ""
                if url:
                    results.append({"title": title.strip(), "price": price_text.strip(), "url": url.strip()})
            except Exception:
                continue
            if len(results) >= limit * 2:
                break

        return results

    def _has_next_page(self) -> bool:
        """Check if Next page button exists."""
        return self.is_visible(SearchPage.NEXT_PAGE_BTN, timeout=3000)

    def _go_to_next_page(self) -> bool:
        """Click Next and wait for results."""
        try:
            self.click(SearchPage.NEXT_PAGE_BTN, "Next Page")
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_element(
                f"xpath={SearchPage.XPATH_RESULT_ITEMS}", state="attached", timeout=15000
            )
            logger.info("Navigated to next page")
            return True
        except Exception as e:
            logger.warning(f"Could not navigate to next page: {e}")
            return False

    # ══════════════════════════════════════════════════════════════
    # STEP 3: ADD ITEMS TO CART
    # ══════════════════════════════════════════════════════════════

    @allure.step("addItemsToCart")
    def add_items_to_cart(self, urls: list[str]) -> AddToCartResult:
        """
        Add items to cart from a list of product URLs.

        For each URL:
        - Opens the product page
        - Selects random variants (size/color) if required
        - Clicks "Add to cart"
        - Saves screenshot + log
        - Returns to search results

        On the last item, navigates to cart via overlay.

        Args:
            urls: List of product URLs.

        Returns:
            AddToCartResult with counts, prices, overlay subtotal.
        """
        logger.info(f"addItemsToCart({len(urls)} URLs)")
        result = AddToCartResult()

        for i, url in enumerate(urls, start=1):
            logger.info(f"  [{i}/{len(urls)}] Opening product...")

            if not self._open_product(url):
                result.skipped_urls.append(url)
                continue

            self._select_random_variant()
            price_text = self._get_product_price()

            if self._click_add_to_cart():
                result.added_count += 1

                if price_text:
                    price_val = PriceParser.parse(price_text)
                    if price_val is not None:
                        result.collected_prices.append(price_val)

                overlay_sub = self._overlay_subtotal_text
                if overlay_sub:
                    result.last_overlay_subtotal = overlay_sub

                take_screenshot(self.page, f"item_{i}_added_to_cart")
                logger.info(
                    f"  [{i}] Added to cart | "
                    f"price={price_text} | overlay_subtotal={overlay_sub}"
                )

                # Last item: navigate to cart
                is_last = (i == len(urls)) or (result.added_count >= len(urls))
                if is_last:
                    self._click_see_in_cart()
                    break
            else:
                logger.warning(f"  [{i}] Failed to add to cart")
                result.skipped_urls.append(url)

            # Return to search results
            self.go_back()

        logger.info(f"addItemsToCart complete: {result.added_count}/{len(urls)} added")
        return result

    def _open_product(self, url: str) -> bool:
        """Navigate to product page, check availability."""
        self.navigate(url)
        self.wait_for_load()
        if self.is_visible(ProductPage.ITEM_ENDED, timeout=2000):
            logger.warning("Item listing has ended, skipping")
            return False
        return True

    def _select_random_variant(self) -> None:
        """Select random variants (size/color) if present."""
        self._try_dropdown(ProductPage.SIZE_SELECT, "Size")
        self._try_dropdown(ProductPage.COLOR_SELECT, "Color")
        self._try_dropdown(ProductPage.VARIANT_SELECT, "Variant")
        self._try_variant_buttons()

    def _try_dropdown(self, selector: str, name: str) -> None:
        """Select a random option from a dropdown if visible."""
        try:
            if not self.is_visible(selector, timeout=2000):
                return
            options = self.page.locator(selector).first.locator("option").all()
            valid = [
                opt.get_attribute("value") or ""
                for opt in options
                if (opt.get_attribute("value") or "") not in ("", "-1")
                and "Select" not in (opt.text_content() or "")
                and opt.get_attribute("disabled") is None
            ]
            if valid:
                self.select_option(selector, random.choice(valid))
                logger.info(f"Selected {name}")
        except Exception as e:
            logger.debug(f"{name} dropdown failed: {e}")

    def _try_variant_buttons(self) -> None:
        """Click a random variant button if available."""
        try:
            buttons = self.page.locator(ProductPage.VARIANT_BUTTONS)
            count = buttons.count()
            if count == 0:
                return
            enabled = [
                buttons.nth(i) for i in range(count)
                if buttons.nth(i).is_enabled()
                and buttons.nth(i).is_visible()
                and buttons.nth(i).get_attribute("aria-checked") != "true"
            ]
            if enabled:
                random.choice(enabled).click(timeout=5000)
                logger.info("Selected variant via button")
        except Exception as e:
            logger.debug(f"Variant buttons failed: {e}")

    def _get_product_price(self) -> Optional[str]:
        """Read price from product page."""
        if self.is_visible(ProductPage.PRODUCT_PRICE, timeout=3000):
            return self.get_text(ProductPage.PRODUCT_PRICE)
        return None

    def _click_add_to_cart(self) -> bool:
        """Click Add to Cart and capture overlay subtotal."""
        try:
            if self.is_visible(ProductPage.ADD_TO_CART_BTN, timeout=5000):
                self.click(ProductPage.ADD_TO_CART_BTN, "Add to Cart")
            elif self.is_visible(ProductPage.ADD_TO_CART_BTN_FALLBACK, timeout=3000):
                self.click(ProductPage.ADD_TO_CART_BTN_FALLBACK, "Add to Cart")
            else:
                logger.warning("Add to Cart button not found")
                return False

            # Wait for overlay confirmation
            try:
                self.wait_for_element(ProductPage.ATC_OVERLAY, state="visible", timeout=10000)
                try:
                    self.wait_for_element(ProductPage.ATC_OVERLAY_ADDED_TEXT, state="visible", timeout=10000)
                except Exception:
                    pass
                self._capture_overlay_subtotal()
            except Exception:
                pass

            logger.info("Item added to cart")
            return True
        except Exception as e:
            logger.error(f"Failed to add to cart: {e}")
            take_screenshot(self.page, "add_to_cart_failed")
            return False

    def _capture_overlay_subtotal(self) -> None:
        """Parse subtotal from ATC overlay."""
        try:
            text = self.get_inner_text(ProductPage.ATC_OVERLAY, timeout=5000)
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if "subtotal" in line.lower():
                    if i + 1 < len(lines):
                        val = PriceParser.parse(lines[i + 1].strip())
                        if val is not None:
                            self._overlay_subtotal_text = lines[i + 1].strip()
                            logger.info(f"Overlay subtotal: {self._overlay_subtotal_text}")
                            return
                    val = PriceParser.parse(line)
                    if val is not None:
                        self._overlay_subtotal_text = line
                        return
        except Exception:
            pass

    def _click_see_in_cart(self) -> bool:
        """Click 'See in cart' in overlay to navigate to cart."""
        try:
            if self.is_visible(ProductPage.ATC_OVERLAY_SEE_CART, timeout=5000):
                self.click(ProductPage.ATC_OVERLAY_SEE_CART, "See in cart")
                self.wait_for_load()
                if "cart" in self.get_current_url().lower():
                    logger.info("Navigated to cart via overlay")
                    return True
        except Exception:
            pass
        return False

    # ══════════════════════════════════════════════════════════════
    # STEP 4: ASSERT CART TOTAL NOT EXCEEDS
    # ══════════════════════════════════════════════════════════════

    @allure.step("assertCartTotalNotExceeds(budgetPerItem={budget_per_item}, itemsCount={items_count})")
    def assert_cart_total_not_exceeds(
        self,
        budget_per_item: float,
        items_count: int,
        collected_prices: list[float] | None = None,
        overlay_subtotal: str | None = None,
    ) -> None:
        """
        Verify that the cart total does not exceed the budget.

        Strategy priority:
        1. Minicart hover (no CAPTCHA, real data)
        2. Cart page reading (if navigated there)
        3. Sum of collected item prices
        4. Overlay subtotal from last ATC

        Args:
            budget_per_item: Maximum price per item.
            items_count: Number of items added.
            collected_prices: Prices collected during add phase.
            overlay_subtotal: Subtotal text from overlay.

        Raises:
            AssertionError: If total exceeds budget or cannot be determined.
        """
        logger.info(
            f"assertCartTotalNotExceeds("
            f"budgetPerItem={budget_per_item}, itemsCount={items_count})"
        )

        if collected_prices:
            self._collected_prices = collected_prices
        if overlay_subtotal:
            self._overlay_subtotal_text = overlay_subtotal

        max_budget = budget_per_item * items_count
        logger.info(f"Threshold: {budget_per_item} x {items_count} = {max_budget}")

        cart_total: Optional[float] = None
        source: str = ""

        # Strategy 1: Minicart hover
        cart_total = self._read_minicart_total()
        if cart_total is not None:
            source = "minicart hover dropdown"

        # Strategy 2: Cart page
        if cart_total is None and "cart" in self.get_current_url().lower():
            if not self.is_visible(CartPage.CAPTCHA_INDICATOR, timeout=2000):
                cart_total = self._read_cart_page_subtotal()
                if cart_total is not None:
                    source = "cart page"
                    take_screenshot(self.page, "cart_page_subtotal")

        # Strategy 3: Collected prices
        if cart_total is None and self._collected_prices:
            cart_total = sum(self._collected_prices)
            source = f"sum of {len(self._collected_prices)} item prices"
            take_screenshot(self.page, "cart_verification_prices")

        # Strategy 4: Overlay subtotal
        if cart_total is None and self._overlay_subtotal_text:
            overlay_val = PriceParser.parse(self._overlay_subtotal_text)
            if overlay_val is not None:
                cart_total = overlay_val
                source = f"ATC overlay ('{self._overlay_subtotal_text}')"

        # Assert
        if cart_total is None:
            take_screenshot(self.page, "cart_no_total_available")
            raise AssertionError(
                "Could not determine cart total from any source. "
                f"Expected total <= {max_budget:.2f} but no total was readable."
            )

        logger.info(f"Cart total: {cart_total:.2f} (source: {source})")
        logger.info(f"Max budget: {max_budget:.2f}")

        assert cart_total <= max_budget, (
            f"Cart total ({cart_total:.2f}) exceeds budget "
            f"({budget_per_item} x {items_count} = {max_budget:.2f}). "
            f"Source: {source}"
        )

        logger.info(f"PASSED: {cart_total:.2f} <= {max_budget:.2f} (source: {source})")
        take_screenshot(self.page, "cart_assertion_passed")

    def _read_minicart_total(self) -> Optional[float]:
        """Hover cart icon and read total from dropdown."""
        try:
            self.scroll_to_top()
            self.wait_for_load()
            self.hover(CartPage.CART_ICON_LINK, force=True)

            if not self.is_visible(CartPage.MINICART_DROPDOWN, timeout=5000):
                return None

            text = self.get_inner_text(CartPage.MINICART_DROPDOWN, timeout=5000)
            take_screenshot(self.page, "cart_minicart_hover")

            lines = text.split("\n")
            for i, line in enumerate(lines):
                if line.strip() == "Total" and i + 1 < len(lines):
                    val = PriceParser.parse(lines[i + 1].strip())
                    if val is not None:
                        logger.info(f"Minicart Total: {val}")
                        return val
                if "Subtotal" in line and i + 1 < len(lines):
                    val = PriceParser.parse(lines[i + 1].strip())
                    if val is not None:
                        logger.info(f"Minicart Subtotal: {val}")
                        return val
            return None
        except Exception as e:
            logger.warning(f"Minicart hover failed: {e}")
            return None

    def _read_cart_page_subtotal(self) -> Optional[float]:
        """Read subtotal from cart page body text."""
        try:
            body_text = self.page.locator("body").inner_text(timeout=10000)
            lines = body_text.split("\n")
            for i, line in enumerate(lines):
                if "Subtotal" in line:
                    if i + 1 < len(lines):
                        amount = PriceParser.parse(lines[i + 1].strip())
                        if amount is not None:
                            return amount
                    amount = PriceParser.parse(line)
                    if amount is not None:
                        return amount
            return None
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════
    # FULL FLOW (convenience)
    # ══════════════════════════════════════════════════════════════

    def execute_full_flow(
        self,
        query: str,
        max_price: float,
        limit: int = 5,
        username: str = "",
        password: str = "",
    ) -> None:
        """
        Execute the complete shopping flow end-to-end.

        Args:
            query: Search term.
            max_price: Maximum price per item.
            limit: Max items to find and add.
            username: eBay username (empty = guest).
            password: eBay password (empty = guest).
        """
        self.login(username, password)

        urls = self.search_items_by_name_under_price(query, max_price, limit)
        assert len(urls) > 0, f"No items found for '{query}' under ${max_price}"

        result = self.add_items_to_cart(urls)
        assert result.added_count > 0, (
            f"Failed to add any items to cart from {len(urls)} URLs"
        )

        self.assert_cart_total_not_exceeds(
            budget_per_item=max_price,
            items_count=result.added_count,
            collected_prices=result.collected_prices,
            overlay_subtotal=result.last_overlay_subtotal,
        )
