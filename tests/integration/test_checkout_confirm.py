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


@pytest.mark.parametrize("field, error_id", [
    ("checked_order", "id_checked_order_error"),
    ("typed_total", "id_typed_total_error"),
], ids=["the tick", "the typed total"])
def test_a_refused_control_is_marked_invalid_and_points_at_its_own_message(acknowledged, field, error_id):
    """Otherwise a screen reader calls the field valid and never reads the reason.

    This page refuses routinely, by design -- three controls, each required --
    and it is the page where money is about to be spent (findings.md F2).
    """
    response = confirm(acknowledged, checked_order=None, typed_total="nonsense")

    content = response.content.decode()
    control = [line for line in content.splitlines() if f'name="{field}"' in line]
    assert control, content
    assert 'aria-invalid="true"' in control[0], control[0]
    assert f'aria-describedby="{error_id}"' in control[0], control[0]
    assert f'<ul class="errorlist" id="{error_id}">' in content


def test_the_controls_keep_what_was_typed_and_the_alpine_bindings(acknowledged):
    """Rendering through the form must not lose the page's behaviour."""
    response = confirm(acknowledged, typed_total="11.01")

    content = response.content.decode()
    typed_lines = [line for line in content.splitlines() if 'name="typed_total"' in line]
    assert typed_lines, content
    typed = typed_lines[0]
    assert 'value="11.01"' in typed
    assert 'x-model="typed"' in typed
    assert 'x-bind:disabled="!checked"' in typed
    assert 'inputmode="decimal"' in typed
    tick = [line for line in content.splitlines() if 'name="checked_order"' in line]
    assert tick, content
    assert 'x-model="checked"' in tick[0]
    # The attribute, not the substring: "checked" is also in name= and x-model=.
    assert tick[0].rstrip().endswith("checked>"), tick[0]


def test_the_controls_are_not_given_a_browser_required_attribute(acknowledged):
    """The refusals stay the server's, worded, and reachable without JavaScript.

    Rendering through the form would otherwise add `required`, and a browser
    would answer an empty control with a bubble of its own before the server
    ever saw it -- including on the no-JavaScript path, where the button is not
    disabled.
    """
    content = acknowledged.get(CONFIRM).content.decode()

    for field in ("checked_order", "typed_total"):
        control = [line for line in content.splitlines() if f'name="{field}"' in line]
        assert control, content
        assert " required" not in control[0], control[0]


def place_order_button(page):
    """The Place my order button's own tag, which spans several lines."""
    start = page.index('<button type="submit" name="place_order"')
    return page[start:page.index(">", start) + 1]


def test_the_place_order_button_points_at_its_message_only_when_there_is_one(acknowledged):
    """An aria-describedby naming an id that is not on the page is worse than none."""
    without = acknowledged.get(CONFIRM).content.decode()
    assert "aria-describedby" not in place_order_button(without)

    refused = confirm(acknowledged, place_order=None).content.decode()

    button = place_order_button(refused)
    assert 'aria-describedby="id_place_order_error"' in button, button
    assert 'aria-invalid="true"' in button, button
    assert '<ul class="errorlist" id="id_place_order_error">' in refused
