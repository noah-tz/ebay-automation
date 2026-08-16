"""
Base Business Process (BaseBP) - Common actions shared across all BPs.

Provides reusable low-level interactions with the browser:
click, fill, navigate, waits, element visibility checks, etc.

All specific BPs inherit from this class.
"""
from typing import Optional

from playwright.sync_api import Page, Locator

from config import settings
from utils.logger import logger


class BaseBP:
    """Base class for all Business Process objects."""

    def __init__(self, page: Page):
        self.page = page
        self.timeout = settings.TIMEOUT

    # ─── Navigation ────────────────────────────────────────────────

    def navigate(self, url: str) -> None:
        """Navigate to a URL and wait for DOM content loaded."""
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

    def get_current_url(self) -> str:
        """Return the current page URL."""
        return self.page.url

    def go_back(self) -> None:
        """Navigate back and wait for page load."""
        self.page.go_back()
        self.page.wait_for_load_state("domcontentloaded")

    # ─── Element Interactions ──────────────────────────────────────

    def click(self, selector: str, description: str = "", timeout: Optional[int] = None) -> None:
        """Click an element by selector."""
        logger.debug(f"Clicking: {description or selector}")
        self.page.locator(selector).first.click(timeout=timeout or self.timeout)

    def fill(self, selector: str, text: str, description: str = "") -> None:
        """Fill a text input by selector."""
        logger.debug(f"Filling '{description or selector}' with: {text}")
        self.page.locator(selector).first.fill(text, timeout=self.timeout)

    def press_key(self, selector: str, key: str) -> None:
        """Press a keyboard key on a focused element."""
        self.page.locator(selector).first.press(key)

    def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """Get text content of an element by selector."""
        return self.page.locator(selector).first.text_content(
            timeout=timeout or self.timeout
        ) or ""

    def get_attribute(self, selector: str, attribute: str, timeout: Optional[int] = None) -> str:
        """Get an attribute value from an element."""
        return self.page.locator(selector).first.get_attribute(
            attribute, timeout=timeout or 3000
        ) or ""

    def select_option(self, selector: str, value: str, timeout: Optional[int] = None) -> None:
        """Select an option from a dropdown by value."""
        self.page.locator(selector).first.select_option(
            value=value, timeout=timeout or 5000
        )

    def hover(self, selector: str, force: bool = False, timeout: Optional[int] = None) -> None:
        """Hover over an element."""
        self.page.locator(selector).first.hover(
            force=force, timeout=timeout or 5000
        )

    # ─── Visibility & State ────────────────────────────────────────

    def is_visible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Check if an element is visible on page."""
        try:
            self.page.locator(selector).first.wait_for(
                state="visible", timeout=timeout or 5000
            )
            return True
        except Exception:
            return False

    def is_attached(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Check if an element is attached to the DOM."""
        try:
            self.page.locator(selector).first.wait_for(
                state="attached", timeout=timeout or 5000
            )
            return True
        except Exception:
            return False

    def element_count(self, selector: str) -> int:
        """Return the number of elements matching a selector."""
        return self.page.locator(selector).count()

    # ─── Waits ─────────────────────────────────────────────────────

    def wait_for_load(self) -> None:
        """Wait for DOM content loaded."""
        self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)

    def wait_for_element(self, selector: str, state: str = "visible", timeout: Optional[int] = None) -> None:
        """Wait for an element to reach a specific state (visible, attached, hidden)."""
        self.page.locator(selector).first.wait_for(
            state=state, timeout=timeout or self.timeout
        )

    def wait_for_url_contains(self, url_part: str, timeout: Optional[int] = None) -> None:
        """Wait until URL contains a specific substring."""
        self.page.wait_for_url(f"**{url_part}**", timeout=timeout or self.timeout)

    # ─── Utility ───────────────────────────────────────────────────

    def scroll_to_top(self) -> None:
        """Scroll to the top of the page."""
        self.page.evaluate("window.scrollTo(0, 0)")

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page."""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def get_page_title(self) -> str:
        """Return the page title."""
        return self.page.title()

    def get_inner_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """Get inner text (rendered text) of an element."""
        return self.page.locator(selector).first.inner_text(
            timeout=timeout or self.timeout
        )
