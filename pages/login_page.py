"""
Login Page - Element repository for eBay login/authentication page.
All selectors use XPath.
"""
from pages.base_page import BasePage


class LoginPage(BasePage):
    """XPath selectors for eBay Login page."""

    USERNAME_INPUT = "//input[@id='userid']"
    CONTINUE_BTN = "//button[@id='signin-continue-btn']"
    PASSWORD_INPUT = "//input[@id='pass']"
    SIGN_IN_BTN = "//button[@id='sgnBt']"
    ERROR_MESSAGE = "//*[@id='signin-error-msg']"
    SIGN_IN_LINK = "//a[contains(text(),'Sign in')]"
    GO_TO_HOMEPAGE = "//a[contains(text(),'Go to homepage')]"
