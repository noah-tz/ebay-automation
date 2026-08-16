"""
Cart Page - Element repository for eBay shopping cart page.
All selectors use XPath.
"""
from pages.base_page import BasePage


class CartPage(BasePage):
    """XPath selectors for eBay Cart page."""

    # Cart page elements
    CART_SUBTOTAL = "//span[contains(text(),'Subtotal')]"
    CART_ITEM_ROW = "//*[contains(@class,'cart-bucket-lineItem')]"

    # Cart icon / minicart hover
    CART_ICON_LINK = "//a[contains(@href,'cart.ebay.com')]"
    MINICART_DROPDOWN = "//*[contains(@id,'gh-minicart')]"

    # CAPTCHA detection
    CAPTCHA_INDICATOR = "//*[contains(text(),'Please verify yourself to continue')]"

    # ATC overlay "See in cart" link
    SEE_IN_CART_OVERLAY = (
        "//*[@data-testid='x-atc-action']"
        "//*[@data-testid='ux-overlay']"
        "//a[contains(text(),'See in cart')]"
    )
