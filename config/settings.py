"""
Configuration settings for eBay Automation Framework.
Loads settings from .env file and provides defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Central configuration class for the automation framework."""

    # Browser Settings
    BROWSER: str = os.getenv("BROWSER", "chromium")
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    VIEWPORT_WIDTH: int = int(os.getenv("VIEWPORT_WIDTH", "1280"))
    VIEWPORT_HEIGHT: int = int(os.getenv("VIEWPORT_HEIGHT", "720"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30000"))

    # eBay URLs
    BASE_URL: str = os.getenv("BASE_URL", "https://www.ebay.com")
    CART_URL: str = os.getenv("CART_URL", "https://cart.ebay.com")
    LOGIN_URL: str = os.getenv(
        "LOGIN_URL",
        "https://signin.ebay.com/ws/eBayISAPI.dll?SignIn"
    )

    # Credentials (Guest mode by default)
    EBAY_USERNAME: str = os.getenv("EBAY_USERNAME", "")
    EBAY_PASSWORD: str = os.getenv("EBAY_PASSWORD", "")
    USE_GUEST_MODE: bool = os.getenv("USE_GUEST_MODE", "true").lower() == "true"

    # Test Data
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
    DEFAULT_SEARCH_LIMIT: int = int(os.getenv("DEFAULT_SEARCH_LIMIT", "5"))

    # Reports
    SCREENSHOTS_DIR: Path = PROJECT_ROOT / "reports" / "screenshots"
    REPORTS_DIR: Path = PROJECT_ROOT / "reports"
    TRACE_DIR: Path = PROJECT_ROOT / "reports" / "traces"

    @classmethod
    def ensure_dirs(cls):
        """Create report directories if they don't exist."""
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.TRACE_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
