"""
E2E Test - eBay Shopping Flow
Full scenario: login -> search -> add to cart -> verify total.
Data-Driven: test inputs loaded from data/test_data.yaml at runtime.
"""
import allure
import pytest

from bp import ShoppingBP
from utils.data_loader import DataLoader
from utils.logger import logger


# Load test data from external YAML (Data-Driven requirement)
test_data = DataLoader.load_yaml("test_data.yaml")
scenario = test_data["default_scenario"]


@pytest.mark.e2e
@allure.epic("eBay Shopping")
@allure.feature("Full E2E Flow")
class TestEbayE2EFlow:
    """End-to-end test: search with price filter, add to cart, verify total."""

    @allure.story("Search, Add to Cart, Verify Total")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_shopping_flow(self, shopping_bp: ShoppingBP):
        """
        Full E2E scenario (Data-Driven from YAML):
        1. Login (guest mode)
        2. searchItemsByNameUnderPrice
        3. addItemsToCart (with variant selection)
        4. assertCartTotalNotExceeds
        """
        query = scenario["query"]
        max_price = scenario["max_price"]
        limit = scenario["limit"]

        logger.info("=" * 60)
        logger.info(f"E2E Test: '{query}' under ${max_price}, limit={limit}")
        logger.info("=" * 60)

        shopping_bp.execute_full_flow(
            query=query,
            max_price=max_price,
            limit=limit,
        )

        logger.info("=" * 60)
        logger.info("E2E Test PASSED")
        logger.info("=" * 60)
