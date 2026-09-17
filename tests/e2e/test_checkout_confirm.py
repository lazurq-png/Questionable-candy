"""UC-08's triple confirmation in a real browser (night-2026-09-17 plan T5).

The server checks all three controls whatever the page does; these check what
only a browser shows -- that each control unlocks only after the one before it,
that a wrong total keeps the button locked, and that the page submits.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect

from tests.e2e.test_theme import PHONE, check_page
from tests.factories.candy_factory import CandyFactory

PASSWORD = "candy-Shop-2026!"


def reach_confirmation(page, live_server):
    """Log in, put 2 x $3.00 in the cart, acknowledge the warning, arrive at confirming."""
    get_user_model().objects.create_user(username="ada", password=PASSWORD)
    CandyFactory(name="Toffee", price=Decimal("3.00"), sugar_content_g=Decimal("60"), stock=5)

    page.goto(f"{live_server.url}/accounts/login/")
    page.get_by_label("Username").fill("ada")
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")
    page.get_by_role("button", name="Add to cart: Toffee").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    page.get_by_role("button", name="Add to cart: Toffee").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("2")

    page.goto(f"{live_server.url}/checkout/warning/")
    page.get_by_label("I have read this health warning").check()
    page.get_by_role("button", name="Continue").click()
    page.wait_for_url(f"{live_server.url}/checkout/confirm/")


def assert_enter_does_not_submit(page, field):
    """Enter in `field` sends no request: typing and placing are two actions.

    Watches for the POST itself rather than for the page staying put, which a
    slow server would also produce. The wait gives a submission time to start;
    one would begin at once.
    """
    posts = []
    page.on("request", lambda request: posts.append(request) if request.method == "POST" else None)
    field.press("Enter")
    page.wait_for_timeout(300)
    assert not posts, [request.url for request in posts]


def test_the_three_controls_unlock_in_order_and_confirm_the_order(live_server, page, assert_page_is_fully_rendered):
    """Tick, then type the total, then place -- and not before."""
    reach_confirmation(page, live_server)
    tick = page.get_by_label("I have checked my order: 2 items, $6.00")
    total = page.get_by_label("Type the total, $6.00, to confirm the amount")
    place = page.get_by_role("button", name="Place my order")

    expect(total).to_be_disabled()
    expect(place).to_be_disabled()
    assert_page_is_fully_rendered(page)

    tick.check()
    expect(total).to_be_enabled()
    expect(place).to_be_disabled()

    total.fill("6.01")
    expect(place).to_be_disabled()

    total.fill("$6.00")
    expect(place).to_be_enabled()
    assert_enter_does_not_submit(page, total)
    tick.uncheck()
    expect(place).to_be_disabled()
    tick.check()

    place.click()
    expect(page.get_by_role("heading", name="received")).to_be_visible()
    assert_page_is_fully_rendered(page)


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_the_confirmation_page_meets_the_measurable_checks(live_server, page, assert_page_is_fully_rendered, scheme):
    """Phone width, both themes: confirming, and the receipt it leads to."""
    page.set_viewport_size(PHONE)
    page.emulate_media(color_scheme=scheme)
    reach_confirmation(page, live_server)

    check_page(page, f"confirm, {scheme}", assert_page_is_fully_rendered)
    page.get_by_label("I have checked my order: 2 items, $6.00").check()
    page.get_by_label("Type the total, $6.00, to confirm the amount").fill("6.00")
    check_page(page, f"confirm, all unlocked, {scheme}", assert_page_is_fully_rendered)
    page.get_by_role("button", name="Place my order").click()
    expect(page.get_by_test_id("order-payment-note")).to_be_visible()
    check_page(page, f"order received, {scheme}", assert_page_is_fully_rendered)


def test_enter_does_not_place_the_order_without_javascript(live_server, page, browser):
    """The guarantee is HTML's, not Alpine's: it holds before a script loads, or with none.

    The cart is filled with JavaScript, then the confirmation page is opened in
    a second context with it switched off and the same cookies.
    """
    reach_confirmation(page, live_server)
    no_script = browser.new_context(java_script_enabled=False)
    try:
        no_script.add_cookies(page.context.cookies())
        plain = no_script.new_page()
        plain.goto(f"{live_server.url}/checkout/confirm/")

        plain.get_by_label("I have checked my order: 2 items, $6.00").check()
        total = plain.get_by_label("Type the total, $6.00, to confirm the amount")
        expect(total).to_be_enabled()
        total.fill("6.00")
        assert_enter_does_not_submit(plain, total)

        plain.get_by_role("button", name="Place my order").click()
        expect(plain.get_by_test_id("order-payment-note")).to_be_visible()
    finally:
        no_script.close()
