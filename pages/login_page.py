"""
Login Page - Element repository for eBay login/authentication page.
"""
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Selectors for eBay Login page."""

    USERNAME_INPUT = "#userid"
    CONTINUE_BTN = "#signin-continue-btn"
    PASSWORD_INPUT = "#pass"
    SIGN_IN_BTN = "#sgnBt"
    ERROR_MESSAGE = "#signin-error-msg"
    SIGN_IN_LINK = 'a:has-text("Sign in")'
    GO_TO_HOMEPAGE = 'a:has-text("Go to homepage")'
