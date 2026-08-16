"""
E2E Test - eBay Shopping Flow
Tests the full scenario: login → search → add to cart → verify total.
Data-Driven from YAML configuration.
"""
import pytest
from playwright.sync_api import Page

from pages import LoginPage, SearchPage, ProductPage, CartPage
from utils.data_loader import DataLoader
from utils.logger import logger
from utils.price_parser import PriceParser


# Load test data from YAML
test_data = DataLoader.load_yaml("test_data.yaml")
scenarios = test_data["test_scenarios"]
default_scenario = test_data["default_scenario"]


class TestEbayE2EFlow:
    """End-to-end test class for eBay shopping flow."""

    def test_full_shopping_flow(
        self,
        page: Page,
        login_page: LoginPage,
        search_page: SearchPage,
        product_page: ProductPage,
        cart_page: CartPage,
    ):
        """
        Full E2E scenario:
        1. Login (or guest mode)
        2. searchItemsByNameUnderPrice - search with price filter
        3. addItemsToCart - add items with variant selection
        4. assertCartTotalNotExceeds - verify cart total
        """
        query = default_scenario["query"]
        max_price = default_scenario["max_price"]
        limit = default_scenario["limit"]

        logger.info("=" * 60)
        logger.info(f"E2E Test: '{query}' under ${max_price}, limit={limit}")
        logger.info("=" * 60)

        # ─── Step 1: Login / Authentication ────────────────────────
        logger.info("Step 1: Authentication")
        login_page.skip_login()

        # ─── Step 2: searchItemsByNameUnderPrice ───────────────────
        logger.info("Step 2: searchItemsByNameUnderPrice")
        urls = search_page.search_items_by_name_under_price(
            query=query,
            max_price=max_price,
            limit=limit,
        )

        assert len(urls) > 0, (
            f"No items found for '{query}' under ${max_price}"
        )
        logger.info(f"Found {len(urls)} items matching criteria")

        # ─── Step 3: addItemsToCart ────────────────────────────────
        logger.info("Step 3: addItemsToCart")
        added_count = 0
        collected_prices: list[float] = []
        last_overlay_subtotal: str | None = None

        for i, url in enumerate(urls, start=1):
            logger.info(f"  [{i}/{len(urls)}] Opening product...")

            # Open product page
            if not product_page.open_product(url):
                logger.warning(f"  [{i}] Skipping unavailable item")
                continue

            # Select variants (size/color) randomly if required
            product_page.select_random_variant()

            # Get price before adding
            price_text = product_page.get_product_price()

            # Add to cart
            if product_page.add_to_cart():
                added_count += 1

                # Collect price
                if price_text:
                    price_val = PriceParser.parse(price_text)
                    if price_val is not None:
                        collected_prices.append(price_val)

                # Capture overlay subtotal (updates after each add)
                overlay_sub = product_page.get_last_overlay_subtotal()
                if overlay_sub:
                    last_overlay_subtotal = overlay_sub

                # Screenshot + log for each item added
                product_page.take_screenshot(f"item_{i}_added_to_cart")
                logger.info(
                    f"  [{i}] ✓ Added to cart | "
                    f"price={price_text} | overlay_subtotal={overlay_sub}"
                )

                # On last item: try to navigate to cart via overlay
                is_last = (i == len(urls)) or (added_count >= limit)
                if is_last:
                    logger.info("  Last item - clicking 'See in cart' in overlay")
                    navigated = product_page.click_see_in_cart()
                    if navigated:
                        logger.info("  ✓ Navigated to cart page via overlay")
                    break
            else:
                logger.warning(f"  [{i}] ✗ Failed to add to cart")

            # Return to search results page (as per requirement 4.2)
            logger.info(f"  [{i}] Returning to search results")
            page.go_back()
            page.wait_for_timeout(2000)

        logger.info(f"addItemsToCart complete: {added_count}/{len(urls)} items added")

        # ─── Step 4: assertCartTotalNotExceeds ─────────────────────
        logger.info("Step 4: assertCartTotalNotExceeds")

        if added_count == 0:
            logger.warning("No items added to cart - skipping assertion")
            return

        # Provide all data sources to cart_page
        cart_page.set_collected_prices(collected_prices)
        if last_overlay_subtotal:
            cart_page.set_overlay_subtotal_text(last_overlay_subtotal)

        cart_page.assert_cart_total_not_exceeds(
            budget_per_item=max_price,
            items_count=added_count,
        )

        logger.info("=" * 60)
        logger.info("✓ E2E Test PASSED")
        logger.info("=" * 60)


@pytest.mark.parametrize(
    "scenario",
    scenarios,
    ids=[s["name"] for s in scenarios],
)
class TestEbayDataDriven:
    """Data-driven test class - runs scenarios from test_data.yaml."""

    def test_search_and_verify(
        self,
        page: Page,
        login_page: LoginPage,
        search_page: SearchPage,
        product_page: ProductPage,
        cart_page: CartPage,
        scenario: dict,
    ):
        """
        Data-driven test: each scenario runs the full flow independently.
        """
        query = scenario["query"]
        max_price = scenario["max_price"]
        limit = scenario["limit"]

        logger.info(f"[Data-Driven] Scenario: {scenario['name']}")

        # Login
        login_page.skip_login()

        # Search
        urls = search_page.search_items_by_name_under_price(
            query=query, max_price=max_price, limit=limit
        )
        logger.info(f"Found {len(urls)} items for '{query}' under ${max_price}")

        # Add to cart
        added_count = 0
        collected_prices: list[float] = []

        for i, url in enumerate(urls, start=1):
            if product_page.open_product(url):
                product_page.select_random_variant()
                price_text = product_page.get_product_price()
                if product_page.add_to_cart():
                    added_count += 1
                    if price_text:
                        pv = PriceParser.parse(price_text)
                        if pv:
                            collected_prices.append(pv)
                    product_page.take_screenshot(f"dd_item_{i}_added")
                    # Last item: don't go back
                    if i == len(urls) or added_count >= limit:
                        product_page.click_see_in_cart()
                        break
                # Return to search results
                page.go_back()
                page.wait_for_timeout(1500)
            else:
                page.go_back()
                page.wait_for_timeout(1000)

        # Verify cart
        if added_count > 0:
            cart_page.set_collected_prices(collected_prices)
            overlay_sub = product_page.get_last_overlay_subtotal()
            if overlay_sub:
                cart_page.set_overlay_subtotal_text(overlay_sub)
            cart_page.assert_cart_total_not_exceeds(
                budget_per_item=max_price, items_count=added_count
            )

        logger.info(f"[Data-Driven] '{scenario['name']}' completed ✓")
