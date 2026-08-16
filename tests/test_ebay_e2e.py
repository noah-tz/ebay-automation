"""
E2E Test - eBay Shopping Flow
Tests the full scenario: login -> search -> add to cart -> verify total.
Data-Driven from YAML configuration.

Test classes are thin — all orchestration logic lives in ShoppingBP.
"""
import allure
import pytest

from bp import ShoppingBP
from utils.data_loader import DataLoader
from utils.logger import logger


# Load test data from YAML
test_data = DataLoader.load_yaml("test_data.yaml")
scenarios = test_data["test_scenarios"]
default_scenario = test_data["default_scenario"]


@pytest.mark.e2e
@allure.epic("eBay Shopping")
@allure.feature("Full E2E Flow")
class TestEbayE2EFlow:
    """End-to-end test class for eBay shopping flow."""

    @allure.story("Search, Add to Cart, Verify Total")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_shopping_flow(self, shopping_bp: ShoppingBP):
        """
        Full E2E scenario using default test data:
        shoes, max $220, up to 5 items.
        """
        query = default_scenario["query"]
        max_price = default_scenario["max_price"]
        limit = default_scenario["limit"]

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


@pytest.mark.data_driven
@allure.epic("eBay Shopping")
@allure.feature("Data-Driven Scenarios")
@pytest.mark.parametrize(
    "scenario",
    scenarios,
    ids=[s["name"] for s in scenarios],
)
class TestEbayDataDriven:
    """Data-driven test class - runs scenarios from test_data.yaml."""

    @allure.severity(allure.severity_level.NORMAL)
    def test_search_and_verify(self, shopping_bp: ShoppingBP, scenario: dict):
        """
        Data-driven test: each scenario runs the full flow independently.
        """
        query = scenario["query"]
        max_price = scenario["max_price"]
        limit = scenario["limit"]

        allure.dynamic.story(f"{query} under ${max_price}")
        logger.info(f"[Data-Driven] Scenario: {scenario['name']}")

        shopping_bp.execute_full_flow(
            query=query,
            max_price=max_price,
            limit=limit,
        )

        logger.info(f"[Data-Driven] '{scenario['name']}' completed")
