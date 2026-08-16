"""
Product Page - Element repository for eBay product/item detail page.
"""
from pages.base_page import BasePage


class ProductPage(BasePage):
    """Selectors for eBay Product detail page."""

    # Add to cart
    ADD_TO_CART_BTN = 'a[data-testid="ux-call-to-action"]:has-text("Add to cart")'
    ADD_TO_CART_BTN_FALLBACK = 'a:has-text("Add to cart"), button:has-text("Add to cart")'
    BUY_IT_NOW_BTN = 'a:has-text("Buy It Now")'

    # Variant selectors (dropdowns)
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
    ATC_OVERLAY_ADDED_TEXT = (
        '[data-testid="x-atc-action"] [data-testid="ux-overlay"] '
        ':text("Added to cart")'
    )
    ATC_OVERLAY_SEE_CART = (
        '[data-testid="x-atc-action"] [data-testid="ux-overlay"] '
        'a:has-text("See in cart")'
    )

    # Error state
    ITEM_ENDED = 'text="This listing has ended"'
