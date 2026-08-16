"""
Cart Page - Element repository for eBay shopping cart page.
"""
from pages.base_page import BasePage


class CartPage(BasePage):
    """Selectors for eBay Cart page."""

    # Cart page elements
    XPATH_SUBTOTAL = "//span[contains(text(),'Subtotal')]"
    CART_SUBTOTAL_AMOUNT = '[data-test-id="SUBTOTAL"] span'
    CART_ITEM_ROW = '[class*="cart-bucket-lineItem"]'

    # Cart icon / minicart hover
    CART_ICON_LINK = 'a[href*="cart.ebay.com"]'
    MINICART_DROPDOWN = '[id*="gh-minicart"]'

    # CAPTCHA detection
    CAPTCHA_INDICATOR = 'text="Please verify yourself to continue"'

    # ATC overlay "See in cart" link
    SEE_IN_CART_OVERLAY = (
        '[data-testid="x-atc-action"] '
        '[data-testid="ux-overlay"] '
        'a:has-text("See in cart")'
    )
