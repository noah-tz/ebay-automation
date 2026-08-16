"""
Search Page - Element repository for eBay search results page.
All selectors use XPath. Verified against live eBay DOM via Playwright MCP.
"""
from pages.base_page import BasePage


class SearchPage(BasePage):
    """XPath selectors for eBay Search Results page."""

    # Search input — eBay uses combobox with id="gh-ac"
    SEARCH_INPUT = "//input[@id='gh-ac']"
    SEARCH_INPUT_FALLBACK = "//input[@type='text' and @name='_nkw']"
    SEARCH_INPUT_PLACEHOLDER = "//input[contains(@placeholder,'Search')]"
    SEARCH_COMBOBOX = "//*[@role='combobox']"
    SEARCH_BUTTON = "//button[@id='gh-btn']"

    # Search result items (verified: finds 62 items on results page)
    XPATH_RESULT_ITEMS = "//ul[contains(@class,'srp-results')]//li[@data-view]"
    XPATH_ITEM_LINK = ".//a[contains(@class,'s-card__link')]"
    XPATH_ITEM_TITLE = ".//*[contains(@class,'s-card__title')]//span"
    XPATH_ITEM_PRICE = ".//*[contains(@class,'s-card__price') or contains(@class,'su-price')]"

    # Price filter UI — verified: uses title attribute, not aria-label for submit
    PRICE_MIN_INPUT = "//input[contains(@aria-label,'Minimum Value')]"
    PRICE_MAX_INPUT = "//input[contains(@aria-label,'Maximum Value')]"
    PRICE_SUBMIT_BTN = "//button[@title='Submit price range']"

    # Pagination
    NEXT_PAGE_BTN = "//a[contains(@aria-label,'next') or contains(@aria-label,'Next')]"
