"""
Product Page - Element repository for eBay product/item detail page.
All selectors use XPath. Verified against live eBay DOM via Playwright MCP.
"""
from pages.base_page import BasePage


class ProductPage(BasePage):
    """XPath selectors for eBay Product detail page."""

    # Add to cart — eBay uses <a id="atcBtn_btn_1"> with "Add to cart" in child span
    ADD_TO_CART_BTN = "//a[contains(@id,'atcBtn')]"
    ADD_TO_CART_BTN_FALLBACK = "//span[contains(text(),'Add to cart')]/ancestor::a"
    BUY_IT_NOW_BTN = "//a[contains(@id,'binBtn')]"

    # Variant selectors — eBay uses custom listbox-button (not <select>)
    # Each variant group is inside a container with data-testid="x-msku-evo"
    VARIANT_CONTAINER = "//*[@data-testid='x-msku-evo']"
    VARIANT_LISTBOX_BUTTON = "xpath=.//button[@aria-haspopup='listbox']"
    VARIANT_LISTBOX_OPTIONS = "//*[@role='listbox']//*[@role='option']"

    # Legacy <select> dropdowns (some listings still use these)
    SIZE_SELECT = "//select[contains(@id,'SIZE') or contains(@aria-label,'Size')]"
    COLOR_SELECT = "//select[contains(@id,'Color') or contains(@aria-label,'Color')]"
    VARIANT_SELECT = "//select[contains(@id,'msku-sel')]"

    # Price on product page
    PRODUCT_PRICE = "//*[@data-testid='x-price-primary']//span[contains(@class,'ux-textspans')]"

    # Cart confirmation
    VIEW_CART_BTN = "//a[contains(text(),'View cart')] | //a[contains(text(),'Go to cart')]"

    # Add-to-cart overlay (shown after successful add)
    ATC_OVERLAY = "//*[@data-testid='x-atc-action']//*[@data-testid='ux-overlay' and @aria-hidden='false']"
    ATC_OVERLAY_ADDED_TEXT = "//*[@data-testid='x-atc-action']//*[@data-testid='ux-overlay']//*[contains(text(),'Added to cart')]"
    ATC_OVERLAY_SEE_CART = "//*[@data-testid='x-atc-action']//*[@data-testid='ux-overlay']//a[contains(text(),'See in cart')]"

    # Error state
    ITEM_ENDED = "//*[contains(text(),'This listing has ended')]"
