"""
Pytest fixtures for eBay E2E Automation.
Sets up browser, page, and Business Process (BP) instance.
Integrates with Allure for rich reporting (screenshots on failure).
"""
import allure
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from config import settings
from bp import ShoppingBP
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
    import ctypes
    try:
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
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
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield ctx

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


# ─── Business Process Fixture ─────────────────────────────────

@pytest.fixture
def shopping_bp(page: Page) -> ShoppingBP:
    """Provide ShoppingBP instance."""
    return ShoppingBP(page)


# ─── Allure: attach screenshot on test failure ─────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a screenshot to Allure report when a test fails."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page_fixture = item.funcargs.get("page")
        if page_fixture:
            try:
                screenshot = page_fixture.screenshot(full_page=True)
                allure.attach(
                    screenshot,
                    name="failure_screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception:
                pass
