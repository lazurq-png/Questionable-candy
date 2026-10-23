"""The whole checkout in a real browser, ending in a placed order (night-2026-09-17 plan T6).

cart → review → login → warning → the three confirmations → receipt, starting
as an anonymous visitor, as a customer would.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from playwright.sync_api import expect

from shop.models import Candy, Order
from tests.factories.candy_factory import CandyFactory

PASSWORD = "candy-Shop-2026!"


def test_an_anonymous_cart_becomes_a_placed_order(live_server, page, assert_page_is_fully_rendered):
    """Every checkout step in order; stock is taken and the cart is empty afterwards."""
    ada = get_user_model().objects.create_user(username="ada", password=PASSWORD, allergies=["milk"])
    fudge = CandyFactory(name="Fudge", price=Decimal("4.50"), sugar_content_g=Decimal("78.0"),
                         allergens=["milk"], stock=3)

    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart: Fudge").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    page.get_by_role("button", name="Add to cart: Fudge").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("2")

    page.goto(f"{live_server.url}/checkout/")
    expect(page.get_by_test_id("checkout-total")).to_have_text("$9.00")
    page.get_by_test_id("checkout-continue").click()

    page.wait_for_url("**/accounts/login/**")
    page.get_by_label("Username").fill("ada")
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Log in").click()

    page.wait_for_url(f"{live_server.url}/checkout/warning/")
    expect(page.get_by_test_id("warning-yours")).to_be_visible()
    page.get_by_label("I have read this health warning").check()
    page.get_by_role("button", name="Continue").click()

    page.wait_for_url(f"{live_server.url}/checkout/confirm/")
    page.get_by_label("I have checked my order: 2 items, $9.00").check()
    page.get_by_label("Type the total, $9.00, to confirm the amount").fill("9.00")
    page.get_by_role("button", name="Place my order").click()

    order = Order.objects.get()
    page.wait_for_url(f"{live_server.url}/orders/{order.pk}/")
    expect(page.get_by_role("heading", name=f"Order #{order.pk} received")).to_be_visible()
    expect(page.get_by_test_id("order-total")).to_have_text("$9.00")
    expect(page.get_by_test_id("order-status")).to_have_text("Pending")
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("0")
    assert_page_is_fully_rendered(page)
    assert order.user == ada
    assert Candy.objects.get(pk=fudge.pk).stock == 1
