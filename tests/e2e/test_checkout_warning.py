"""UC-07's health warning in a real browser (night-2026-09-17 plan T4).

From a cart filled without logging in, through Continue, the login it requires,
the warning itself and its acknowledgment -- and the warning page meeting the
measurable checks at phone width in both themes.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect

from tests.e2e.test_theme import PHONE, check_page
from tests.factories.candy_factory import CandyFactory

PASSWORD = "candy-Shop-2026!"


def fill_cart_and_log_in_at_the_warning(page, live_server):
    """Add two candies anonymously, Continue from checkout, and log in when asked."""
    get_user_model().objects.create_user(username="ada", password=PASSWORD, allergies=["milk"])
    CandyFactory(name="Fudge", sugar_content_g=Decimal("78.0"), allergens=["milk"], stock=5)
    CandyFactory(name="Taffy", sugar_content_g=None, allergens=[], stock=5)

    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart: Fudge").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    page.get_by_role("button", name="Add to cart: Taffy").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("2")

    page.goto(f"{live_server.url}/checkout/")
    page.get_by_test_id("checkout-continue").click()
    page.wait_for_url("**/accounts/login/?next=/checkout/warning/")
    page.get_by_label("Username").fill("ada")
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/checkout/warning/")


def test_the_warning_is_read_and_acknowledged_after_logging_in(live_server, page, assert_page_is_fully_rendered):
    """The cart survives login, the warning is built from it, and the tick is required."""
    fill_cart_and_log_in_at_the_warning(page, live_server)

    expect(page.get_by_test_id("warning-total-sugar")).to_have_text("78.0 g")
    expect(page.get_by_test_id("warning-unknown-sugar")).to_contain_text("Taffy")
    expect(page.get_by_test_id("warning-yours")).to_have_text("You listed this allergy")
    expect(page.get_by_test_id("warning-match-summary")).to_be_visible()
    assert_page_is_fully_rendered(page)

    page.get_by_label("I have read this health warning").check()
    page.get_by_role("button", name="Continue").click()

    page.wait_for_url(f"{live_server.url}/checkout/confirm/")
    expect(page.get_by_test_id("confirm-form")).to_be_visible()


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_the_warning_page_meets_the_measurable_checks(live_server, page, assert_page_is_fully_rendered, scheme):
    """Phone width: the sugar table scrolls inside itself, never the page."""
    page.set_viewport_size(PHONE)
    page.emulate_media(color_scheme=scheme)
    fill_cart_and_log_in_at_the_warning(page, live_server)

    check_page(page, f"health warning, {scheme}", assert_page_is_fully_rendered)

    page.get_by_role("button", name="Continue").click()  # unticked: the browser refuses
    expect(page.get_by_test_id("warning-form")).to_be_visible()
    page.get_by_label("I have read this health warning").check()
    page.get_by_role("button", name="Continue").click()
    page.wait_for_url(f"{live_server.url}/checkout/confirm/")
    page.goto(f"{live_server.url}/checkout/warning/")
    expect(page.get_by_test_id("warning-acknowledged")).to_be_visible()
    check_page(page, f"health warning acknowledged, {scheme}", assert_page_is_fully_rendered)
