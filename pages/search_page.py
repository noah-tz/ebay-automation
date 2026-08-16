"""
Search Page Object - Handles product search with price filtering.
Implements searchItemsByNameUnderPrice with XPath-based item extraction
and pagination support.
"""
import re
from typing import Optional

from playwright.sync_api import Page

from config import settings
from pages.base_page import BasePage
from utils.logger import logger
from utils.price_parser import PriceParser


class SearchPage(BasePage):
    """Page Object for eBay Search Results page."""

    # ─── Selectors ─────────────────────────────────────────────────
    SEARCH_INPUT = "#gh-ac"
    SEARCH_INPUT_FALLBACK = 'input[type="text"][name="_nkw"], input[aria-label*="Search"]'
    SEARCH_BUTTON = '#gh-btn, button:has-text("Search")'
    SEARCH_CATEGORY = "#gh-cat"

    # XPath selectors for extracting search result items
    # (per requirement: "שלוף בעזרת xpath את ה-limit פריטים ראשונים")
    XPATH_RESULT_ITEMS = "//ul[contains(@class,'srp-results')]//li[@data-view]"
    XPATH_ITEM_LINK = ".//a[contains(@class,'s-card__link')]"
    XPATH_ITEM_TITLE = ".//*[contains(@class,'s-card__title')]//span"
    XPATH_ITEM_PRICE = ".//*[contains(@class,'s-card__price') or contains(@class,'su-price')]"

    # CSS fallbacks
    CSS_RESULTS_LIST = ".srp-results li[data-view]"

    # Price filter
    PRICE_MIN_INPUT = 'input[aria-label*="Minimum Value"]'
    PRICE_MAX_INPUT = 'input[aria-label*="Maximum Value"]'
    PRICE_SUBMIT_BTN = 'button[aria-label="Submit price range"]'

    # Pagination
    NEXT_PAGE_BTN = 'a[aria-label*="next" i], a[aria-label*="Next" i]'

    def __init__(self, page: Page):
        super().__init__(page)

    # ─── Actions ───────────────────────────────────────────────────

    def search(self, query: str) -> None:
        """
        Perform a search for the given query.

        Args:
            query: Search term to look for.
        """
        logger.info(f"Searching for: '{query}'")

        # Try multiple search input selectors
        selectors = [
            self.SEARCH_INPUT,
            self.SEARCH_INPUT_FALLBACK,
            'input[placeholder*="Search"]',
            '[role="combobox"]',
        ]

        search_input = None
        for selector in selectors:
            locator = self.page.locator(selector).first
            if self.is_visible(locator, timeout=3000):
                search_input = locator
                logger.debug(f"Found search input with: {selector}")
                break

        if search_input is None:
            logger.warning("Search input not found, using direct URL navigation")
            search_url = (
                f"{settings.BASE_URL}/sch/i.html"
                f"?_nkw={query.replace(' ', '+')}&_sacat=0"
            )
            self.navigate(search_url)
            self.page.wait_for_timeout(3000)
            return

        search_input.click()
        self.page.wait_for_timeout(500)
        search_input.fill(query)
        search_input.press("Enter")
        self.wait_for_load()
        self.page.wait_for_timeout(3000)
        logger.info(f"Search results loaded for: '{query}'")

    def apply_price_filter_via_url(
        self, max_price: float, min_price: float = 0
    ) -> None:
        """
        Apply price filter using URL parameters (_udhi/_udlo).
        This is the most reliable method as it uses eBay's server-side filtering.

        Args:
            max_price: Maximum price.
            min_price: Minimum price.
        """
        current_url = self.get_current_url()

        if "ebay.com/sch" not in current_url:
            logger.warning("Not on search page, cannot apply price filter")
            return

        # Clean existing price params
        url_clean = re.sub(r"&_udhi=[^&]*", "", current_url)
        url_clean = re.sub(r"&_udlo=[^&]*", "", url_clean)

        new_url = f"{url_clean}&_udlo={int(min_price)}&_udhi={int(max_price)}"
        logger.info(f"Applying price filter: max={max_price}")
        self.navigate(new_url)
        self.page.wait_for_timeout(3000)

    def get_results_via_xpath(self, limit: int) -> list[dict]:
        """
        Extract search result items using XPath selectors.
        Returns up to `limit` items with title, price, and URL.

        Uses XPath as required by the project specification:
        "שלוף בעזרת xpath את ה-limit פריטים ראשונים אשר מחירם שווה או נמוך ל maxPrice"

        Args:
            limit: Maximum number of items to extract.

        Returns:
            List of dicts with 'title', 'price', 'url' for each item.
        """
        items = self.page.locator(f"xpath={self.XPATH_RESULT_ITEMS}")
        count = items.count()
        logger.debug(f"XPath found {count} result items on page")

        results = []
        for i in range(min(count, limit * 2)):  # Check more than limit for filtering
            item = items.nth(i)
            try:
                # Extract link via XPath
                link_el = item.locator(f"xpath={self.XPATH_ITEM_LINK}").first
                url = link_el.get_attribute("href", timeout=3000) or ""

                # Extract title via XPath
                title_el = item.locator(f"xpath={self.XPATH_ITEM_TITLE}").first
                title = title_el.text_content(timeout=3000) or ""

                # Extract price via XPath
                price_el = item.locator(f"xpath={self.XPATH_ITEM_PRICE}").first
                price_text = price_el.text_content(timeout=3000) or ""

                if url:
                    results.append({
                        "title": title.strip(),
                        "price": price_text.strip(),
                        "url": url.strip(),
                    })
            except Exception:
                continue

            if len(results) >= limit * 2:
                break

        logger.debug(f"XPath extracted {len(results)} items")
        return results

    def has_next_page(self) -> bool:
        """Check if pagination Next button is available."""
        next_btn = self.page.locator(self.NEXT_PAGE_BTN)
        return self.is_visible(next_btn, timeout=3000)

    def go_to_next_page(self) -> bool:
        """Navigate to the next page of results."""
        try:
            next_btn = self.page.locator(self.NEXT_PAGE_BTN).first
            if self.is_visible(next_btn, timeout=3000):
                self.click(next_btn, "Next Page")
                self.page.wait_for_timeout(3000)
                logger.info("Navigated to next page")
                return True
        except Exception as e:
            logger.warning(f"Could not navigate to next page: {e}")
        return False

    # ─── Main Function: searchItemsByNameUnderPrice ────────────────

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
        - Uses price filter (min/max) to narrow results
        - Extracts items via XPath, verifying price <= maxPrice
        - Supports pagination if fewer than `limit` items on current page
        - Returns array of URLs (up to `limit`) meeting price criteria

        Args:
            query: Search term (e.g., "shoes").
            max_price: Maximum price per item.
            limit: Max number of URLs to return (default: 5).

        Returns:
            List of item URLs (up to `limit`). May be empty or < limit.
        """
        logger.info(
            f"searchItemsByNameUnderPrice('{query}', "
            f"maxPrice={max_price}, limit={limit})"
        )

        # Step 1: Perform search
        self.search(query)

        # Step 2: Apply price filter (server-side)
        self.apply_price_filter_via_url(max_price)

        # Step 3: Collect items via XPath with pagination
        collected_urls: list[str] = []
        max_pages = 3

        for page_num in range(1, max_pages + 1):
            logger.info(f"Processing page {page_num}...")

            # Extract items using XPath
            results = self.get_results_via_xpath(limit)

            for item in results:
                if len(collected_urls) >= limit:
                    break

                # Verify price <= maxPrice
                price_value = PriceParser.parse(item["price"])

                if price_value is not None and price_value <= max_price:
                    if item["url"] not in collected_urls:
                        collected_urls.append(item["url"])
                        logger.info(
                            f"  [{len(collected_urls)}/{limit}] "
                            f"{item['title'][:40]}... @ {item['price']}"
                        )
                elif price_value is None and item["url"]:
                    # Price not parseable but filter was applied server-side
                    if item["url"] not in collected_urls:
                        collected_urls.append(item["url"])
                        logger.info(
                            f"  [{len(collected_urls)}/{limit}] "
                            f"{item['title'][:40]}... @ {item['price']} (unverified)"
                        )

            if len(collected_urls) >= limit:
                break

            # Pagination: if fewer than limit, try next page
            if page_num < max_pages and self.has_next_page():
                if not self.go_to_next_page():
                    break
            else:
                if len(collected_urls) < limit:
                    logger.info("No more pages available")
                break

        logger.info(
            f"searchItemsByNameUnderPrice complete: "
            f"found {len(collected_urls)} items"
        )
        self.take_screenshot(f"search_results_{query}")
        return collected_urls
