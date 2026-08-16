"""
Base Page Object - Foundation for all page objects.
Implements common actions and waits used across all pages.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, Locator, expect

from config import settings
from utils.logger import logger


class BasePage:
    """Base class for all Page Object Model classes."""

    def __init__(self, page: Page):
        self.page = page
        self.timeout = settings.TIMEOUT

    # ─── Navigation ────────────────────────────────────────────────

    def navigate(self, url: str) -> None:
        """Navigate to a URL and wait for network idle."""
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

    def get_current_url(self) -> str:
        """Return the current page URL."""
        return self.page.url

    # ─── Element Interactions ──────────────────────────────────────

    def click(self, locator: Locator, description: str = "") -> None:
        """Click an element with logging."""
        logger.debug(f"Clicking: {description or locator}")
        locator.click(timeout=self.timeout)

    def fill(self, locator: Locator, text: str, description: str = "") -> None:
        """Fill a text input with logging."""
        logger.debug(f"Filling '{description or locator}' with: {text}")
        locator.fill(text, timeout=self.timeout)

    def get_text(self, locator: Locator) -> str:
        """Get text content of an element."""
        return locator.text_content(timeout=self.timeout) or ""

    def is_visible(self, locator: Locator, timeout: Optional[int] = None) -> bool:
        """Check if an element is visible."""
        try:
            locator.wait_for(state="visible", timeout=timeout or 5000)
            return True
        except Exception:
            return False

    # ─── Waits ─────────────────────────────────────────────────────

    def wait_for_load(self) -> None:
        """Wait for page to finish loading."""
        self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)

    def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """Wait for a selector and return the locator."""
        self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
        return self.page.locator(selector)

    def wait_for_url_contains(self, url_part: str, timeout: Optional[int] = None) -> None:
        """Wait until URL contains a specific substring."""
        self.page.wait_for_url(f"**{url_part}**", timeout=timeout or self.timeout)

    # ─── Screenshots & Traces ─────────────────────────────────────

    def take_screenshot(self, name: str) -> Path:
        """
        Take a screenshot and save it to the reports folder.

        Args:
            name: Descriptive name for the screenshot.

        Returns:
            Path to the saved screenshot file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = settings.SCREENSHOTS_DIR / filename
        self.page.screenshot(path=str(filepath), full_page=True)
        logger.info(f"Screenshot saved: {filepath}")
        return filepath

    # ─── Utility ───────────────────────────────────────────────────

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page."""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.page.wait_for_timeout(500)

    def get_page_title(self) -> str:
        """Return the page title."""
        return self.page.title()
