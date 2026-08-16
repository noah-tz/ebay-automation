"""
Screenshot utility - Technical helper for capturing browser screenshots.
"""
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page

from config import settings
from utils.logger import logger


def take_screenshot(page: Page, name: str) -> Path:
    """
    Take a screenshot and save to the reports folder.

    Args:
        page: Playwright Page instance.
        name: Descriptive name for the screenshot.

    Returns:
        Path to the saved screenshot file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = settings.SCREENSHOTS_DIR / filename
    page.screenshot(path=str(filepath), full_page=True)
    logger.info(f"Screenshot saved: {filepath}")
    return filepath
