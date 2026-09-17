"""UC-08: the triple confirmation step of checkout (night-2026-09-17 plan T5).

Clients enforce CSRF and post the token a real page handed out; login is
covered in test_accounts.py, so these sign in with force_login.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from shop.checkout import SESSION_KEY, snapshot_fingerprint
from shop.models import Candy, Order
from tests.factories.candy_factory import CandyFactory
from tests.integration.test_checkout_warning import acknowledge, add, browser

pytestmark = pytest.mark.django_db

CONFIRM = reverse("checkout_confirm")
ALL_THREE = {"checked_order": "on", "typed_total": "11.00", "place_order": "yes"}


def confirm(client, **changes):
    """Submit the confirmation form: all three controls, with `changes` (None removes one).

    `shown` and `token` are what the page last shown would post, unless given.
    """
    stored = client.session[SESSION_KEY]
    shown = snapshot_fingerprint(stored["showing"])
    data = {"csrfmiddlewaretoken": client.token, "shown": shown, "token": stored["token"], **ALL_THREE, **changes}
    return client.post(CONFIRM, {key: value for key, value in data.items() if value is not None})


@pytest.fixture(name="acknowledged")
def fixture_acknowledged():
    """A signed-in customer with 2 x $3.00 and 1 x $5.00 in the cart ($11.00),
    the health warning acknowledged, and the confirmation page opened once."""
    user = get_user_model().objects.create_user(username="ada", password="x")
    client = browser(user)
    toffee = CandyFactory(name="Toffee", price=Decimal("3.00"), stock=5)
    drops = CandyFactory(name="Drops", price=Decimal("5.00"), stock=5)
    add(client, toffee, times=2)
    add(client, drops)
    acknowledge(client)
    client.page = client.get(CONFIRM)
    client.candies = {"toffee": toffee, "drops": drops}
    return client


def test_confirming_requires_login():
    """Like the warning, the confirmation is for a signed-in customer."""
    client = browser()
    response = client.get(CONFIRM)
    assert response.status_code == 302
    assert response["Location"] == f'{reverse("accounts:login")}?next={CONFIRM}'


def test_without_an_acknowledged_warning_it_goes_back_to_the_warning():
    """UC-08 precondition: the health warning comes first."""
    user = get_user_model().objects.create_user(username="ada", password="x")
    client = browser(user)
    add(client, CandyFactory(stock=5))

    response = client.get(CONFIRM)

    assert response["Location"] == reverse("checkout_warning")


def test_an_empty_cart_goes_back_to_the_cart_page():
    """Nothing to confirm, so back to the cart."""
    user = get_user_model().objects.create_user(username="ada", password="x")

    response = browser(user).get(CONFIRM)

    assert response["Location"] == reverse("shoppingcart")


def test_the_page_shows_exactly_what_is_being_confirmed_and_remembers_it(acknowledged):
    """Lines, quantities, prices and total, and the snapshot of them in the session."""
    content = acknowledged.page.content.decode()

    assert content.count('data-testid="confirm-line"') == 2
    assert "2 &times; $3.00" in content and "1 &times; $5.00" in content
    assert '<span data-testid="confirm-total">$11.00</span>' in content
    assert "I have checked my order: 3 items, $11.00" in content
    assert "Type the total, $11.00, to confirm the amount" in content
    assert ">Place my order</button>" in content
    shown = acknowledged.session[SESSION_KEY]["showing"]
    toffee, drops = acknowledged.candies["toffee"], acknowledged.candies["drops"]
    assert shown == {"lines": [[drops.pk, 1, "5.00"], [toffee.pk, 2, "3.00"]], "total": "11.00"}


def test_all_three_confirmations_place_the_order(acknowledged):
    """UC-08 step 6 leads into UC-05: the order is placed and its receipt shown."""
    response = confirm(acknowledged)

    order = Order.objects.get()
    assert response.status_code == 302
    assert response["Location"] == reverse("order_received", args=[order.pk])
    assert order.total_amount == Decimal("11.00")


@pytest.mark.parametrize("change", [
    {"checked_order": None},
    {"typed_total": None},
    {"typed_total": "11.01"},
    {"place_order": None},
], ids=["no tick", "no total", "wrong total", "no button"])
def test_any_one_confirmation_missing_or_wrong_is_refused(acknowledged, change):
    """Server-side, with the other two right: no JavaScript is relied on."""
    response = confirm(acknowledged, **change)

    assert response.status_code == 200
    assert 'data-testid="confirm-form"' in response.content.decode()
    assert not Order.objects.exists()


def test_a_price_change_while_confirming_is_refused_and_the_new_order_shown(acknowledged):
    """The customer confirmed $11.00; the order now costs more, so that is not confirmed."""
    Candy.objects.filter(pk=acknowledged.candies["drops"].pk).update(price=Decimal("6.00"))

    response = confirm(acknowledged)

    content = response.content.decode()
    assert response.status_code == 200
    assert "Your order changed while you were confirming it." in content
    assert '<span data-testid="confirm-total">$12.00</span>' in content
    assert not Order.objects.exists()

    assert confirm(acknowledged, typed_total="12.00").status_code == 302  # the new order, placed
    assert Order.objects.get().total_amount == Decimal("12.00")


def test_changing_the_cart_while_confirming_starts_again_at_the_warning(acknowledged):
    """UC-08: the exact cart contents are what is confirmed."""
    add(acknowledged, acknowledged.candies["drops"])

    assert SESSION_KEY not in acknowledged.session
    assert acknowledged.get(CONFIRM)["Location"] == reverse("checkout_warning")


def test_leaving_without_confirming_keeps_the_cart(acknowledged):
    """UC-08 ext.: declining changes nothing."""
    acknowledged.get(reverse("checkout"))

    assert acknowledged.session["shoppingcart"] == {
        str(acknowledged.candies["toffee"].pk): 2, str(acknowledged.candies["drops"].pk): 1,
    }


def test_the_confirmation_form_is_refused_without_a_csrf_token(acknowledged):
    """Protected like every other form."""
    response = acknowledged.post(CONFIRM, ALL_THREE)
    assert response.status_code == 403


def test_a_cart_emptied_while_confirming_goes_back_to_the_cart_with_the_reason(acknowledged):
    """Both candies withdrawn from sale: nothing left to confirm, and the cart page says why."""
    Candy.objects.update(is_published=False)

    response = acknowledged.get(CONFIRM)

    assert response["Location"] == reverse("shoppingcart")
    assert "2 items are no longer available" in acknowledged.get(response["Location"]).content.decode()


def test_confirming_an_older_showing_of_the_page_is_refused(acknowledged):
    """Reloaded or opened again since: only the page last shown can place the order."""
    response = confirm(acknowledged, token="an-older-token")

    assert response.status_code == 200
    assert "Your order changed while you were confirming it." in response.content.decode()
    assert not Order.objects.exists()


def test_confirming_a_page_that_showed_a_different_order_is_refused(acknowledged):
    """Another tab showed a different order: this post is not a confirmation of it."""
    response = confirm(acknowledged, shown="0" * 64)

    assert response.status_code == 200
    assert "Your order changed while you were confirming it." in response.content.decode()
    assert not Order.objects.exists()


@pytest.mark.parametrize("method", ["get", "post"])
def test_a_stock_cap_while_confirming_returns_to_the_warning_with_the_reason(acknowledged, method):
    """Capping the cart is a change to it: warning again, and the customer is told why."""
    Candy.objects.filter(pk=acknowledged.candies["toffee"].pk).update(stock=1)

    response = confirm(acknowledged) if method == "post" else acknowledged.get(CONFIRM)

    assert response["Location"] == reverse("checkout_warning")
    warning = acknowledged.get(response["Location"]).content.decode()
    assert "Only 1 of Toffee left in stock, so the quantity is 1." in warning
