"""
Pytest fixtures for eBay E2E Automation.
Sets up browser, page, and page objects for tests.
"""
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from config import settings
from pages import LoginPage, SearchPage, ProductPage, CartPage
from utils.logger import logger


@pytest.fixture(scope="session")
def browser():
    """Launch browser for the test session."""
    logger.info(f"Launching browser: {settings.BROWSER} (headless={settings.HEADLESS})")
    with sync_playwright() as p:
        browser_type = getattr(p, settings.BROWSER)
        browser_instance = browser_type.launch(
            headless=settings.HEADLESS,
            slow_mo=settings.SLOW_MO,
        )
        yield browser_instance
        browser_instance.close()
        logger.info("Browser closed")


@pytest.fixture(scope="function")
def context(browser: Browser):
    """Create a new browser context with realistic screen size."""
    # Use a common desktop resolution dynamically
    import ctypes
    try:
        # Get actual screen resolution on Windows
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        # Use slightly smaller than full screen (like a maximized window)
        vw = min(screen_width - 100, 1920)
        vh = min(screen_height - 150, 1080)
    except Exception:
        vw = settings.VIEWPORT_WIDTH
        vh = settings.VIEWPORT_HEIGHT

    logger.info(f"Using viewport: {vw}x{vh}")

    ctx = browser.new_context(
        viewport={"width": vw, "height": vh},
        locale="en-US",
        screen={"width": vw, "height": vh},
    )
    # Start tracing
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield ctx

    # Save trace
    trace_path = settings.TRACE_DIR / "trace.zip"
    ctx.tracing.stop(path=str(trace_path))
    logger.info(f"Trace saved: {trace_path}")
    ctx.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Create a new page for each test."""
    pg = context.new_page()
    pg.set_default_timeout(settings.TIMEOUT)
    yield pg
    pg.close()


# ─── Page Object Fixtures ──────────────────────────────────────

@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """Provide LoginPage instance."""
    return LoginPage(page)


@pytest.fixture
def search_page(page: Page) -> SearchPage:
    """Provide SearchPage instance."""
    return SearchPage(page)


@pytest.fixture
def product_page(page: Page) -> ProductPage:
    """Provide ProductPage instance."""
    return ProductPage(page)


@pytest.fixture
def cart_page(page: Page) -> CartPage:
    """Provide CartPage instance."""
    return CartPage(page)
