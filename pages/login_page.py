"""
Login Page Object - Handles eBay authentication.
Supports both credential-based login and guest/skip mode.
"""
from playwright.sync_api import Page

from config import settings
from pages.base_page import BasePage
from utils.logger import logger


class LoginPage(BasePage):
    """Page Object for eBay Login/Authentication."""

    # ─── Selectors ─────────────────────────────────────────────────
    USERNAME_INPUT = "#userid"
    CONTINUE_BTN = "#signin-continue-btn"
    PASSWORD_INPUT = "#pass"
    SIGN_IN_BTN = "#sgnBt"
    ERROR_MESSAGE = "#signin-error-msg"
    SIGN_IN_LINK = 'a:has-text("Sign in")'

    def __init__(self, page: Page):
        super().__init__(page)
        self.login_url = settings.LOGIN_URL

    # ─── Actions ───────────────────────────────────────────────────

    def go_to_login(self) -> None:
        """Navigate to the eBay login page."""
        self.navigate(self.login_url)
        logger.info("Navigated to login page")

    def login(self, username: str = "", password: str = "") -> bool:
        """
        Perform login with credentials.

        Args:
            username: eBay username/email. Falls back to .env if empty.
            password: eBay password. Falls back to .env if empty.

        Returns:
            True if login was successful, False otherwise.
        """
        _username = username or settings.EBAY_USERNAME
        _password = password or settings.EBAY_PASSWORD

        if not _username or not _password:
            logger.warning("No credentials provided. Using guest mode.")
            return self.skip_login()

        try:
            self.go_to_login()

            # Enter username
            username_field = self.page.locator(self.USERNAME_INPUT)
            self.fill(username_field, _username, "Username")
            self.click(
                self.page.locator(self.CONTINUE_BTN), "Continue button"
            )

            # Wait for password field
            self.page.wait_for_selector(self.PASSWORD_INPUT, timeout=10000)

            # Enter password
            password_field = self.page.locator(self.PASSWORD_INPUT)
            self.fill(password_field, _password, "Password")
            self.click(
                self.page.locator(self.SIGN_IN_BTN), "Sign In button"
            )

            # Wait for redirect to homepage
            self.page.wait_for_url("**/ebay.com/**", timeout=15000)
            logger.info("Login successful!")
            self.take_screenshot("login_success")
            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.take_screenshot("login_failed")
            return False

    def skip_login(self) -> bool:
        """
        Skip login and continue as guest.
        Navigates to eBay homepage and handles any error/blocking pages.

        Returns:
            True (guest mode always succeeds).
        """
        logger.info("Skipping login - using guest mode")
        self.navigate(settings.BASE_URL)
        self.page.wait_for_timeout(3000)

        # Handle error page (eBay sometimes blocks first visit)
        if "Error Page" in self.get_page_title():
            logger.warning("Got error page on first visit, clicking 'Go to homepage'")
            go_home_btn = self.page.locator('a:has-text("Go to homepage")')
            if self.is_visible(go_home_btn, timeout=5000):
                self.click(go_home_btn, "Go to homepage")
                self.page.wait_for_timeout(3000)

        self.wait_for_load()
        return True

    def is_logged_in(self) -> bool:
        """Check if the user is currently logged in."""
        try:
            # If "Sign in" link is visible, user is NOT logged in
            sign_in_link = self.page.locator(self.SIGN_IN_LINK)
            return not self.is_visible(sign_in_link, timeout=3000)
        except Exception:
            return False
