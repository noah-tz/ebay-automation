"""
Search Page - Element repository for eBay search results page.
"""
from pages.base_page import BasePage


class SearchPage(BasePage):
    """Selectors for eBay Search Results page."""

    # Search input
    SEARCH_INPUT = "#gh-ac"
    SEARCH_INPUT_FALLBACK = 'input[type="text"][name="_nkw"], input[aria-label*="Search"]'
    SEARCH_INPUT_PLACEHOLDER = 'input[placeholder*="Search"]'
    SEARCH_COMBOBOX = '[role="combobox"]'
    SEARCH_BUTTON = '#gh-btn, button:has-text("Search")'
    SEARCH_CATEGORY = "#gh-cat"

    # XPath selectors for search result items
    # (per requirement: "שלוף בעזרת xpath את ה-limit פריטים ראשונים")
    XPATH_RESULT_ITEMS = "//ul[contains(@class,'srp-results')]//li[@data-view]"
    XPATH_ITEM_LINK = ".//a[contains(@class,'s-card__link')]"
    XPATH_ITEM_TITLE = ".//*[contains(@class,'s-card__title')]//span"
    XPATH_ITEM_PRICE = ".//*[contains(@class,'s-card__price') or contains(@class,'su-price')]"

    # CSS fallback
    CSS_RESULTS_LIST = ".srp-results li[data-view]"

    # Price filter
    PRICE_MIN_INPUT = 'input[aria-label*="Minimum Value"]'
    PRICE_MAX_INPUT = 'input[aria-label*="Maximum Value"]'
    PRICE_SUBMIT_BTN = 'button[aria-label="Submit price range"]'

    # Pagination
    NEXT_PAGE_BTN = 'a[aria-label*="next" i], a[aria-label*="Next" i]'
