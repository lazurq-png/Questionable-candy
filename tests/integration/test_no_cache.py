"""Pages showing one customer's own state must not be cached (findings.md F1).

Without `Cache-Control: no-store` a browser may serve such a page from its own
history cache after the customer has left -- the next person on a shared
computer pressing Back. `Vary: Cookie`, which every page already carries, is
about shared proxies, not about that.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from shop.checkout import SESSION_KEY
from shop.models import Order
from tests.factories.candy_factory import CandyFactory
from tests.integration.test_checkout_warning import acknowledge, add, browser

pytestmark = pytest.mark.django_db


@pytest.fixture(name="shopper")
def fixture_shopper():
    """A signed-in customer partway through checkout, with an order already placed."""
    user = get_user_model().objects.create_user(username="ada", password="x", allergies=["milk"])
    client = browser(user)
    candy = CandyFactory(name="Fudge", price=Decimal("2.00"), stock=9, sugar_content_g=Decimal("70"))
    add(client, candy)
    acknowledge(client)
    client.get(reverse("checkout_confirm"))
    client.order = Order.objects.place(
        user, {"lines": [[candy.pk, 1, "2.00"]], "total": "2.00"}, None, None, "1" * 32,
    )
    assert SESSION_KEY in client.session  # still mid-checkout: the pages below have content
    return client


@pytest.mark.parametrize("name", [
    "shoppingcart", "shoppingcart_panel", "checkout", "checkout_warning", "checkout_confirm",
])
def test_the_cart_and_checkout_pages_are_never_cached(shopper, name):
    """Each shows what this customer put in their cart, or is about to order."""
    response = shopper.get(reverse(name))

    assert response.status_code == 200, name
    assert "no-store" in response["Cache-Control"], name


def test_the_receipt_is_never_cached(shopper):
    """It names what was bought, and it is the page a customer leaves open."""
    response = shopper.get(reverse("order_received", args=[shopper.order.pk]))

    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]


def test_profile_is_never_cached(shopper):
    """Health information, on a page reached from the header."""
    response = shopper.get(reverse("accounts:profile"))

    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]


def test_my_orders_is_never_cached(shopper):
    """A list of what this customer bought."""
    response = shopper.get(reverse("accounts:orders"))

    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]


def test_the_catalog_stays_cacheable(client):
    """Deliberately: it is the page worth caching, and Vary separates sessions."""
    CandyFactory(name="Fudge")

    response = client.get(reverse("candy_list"))

    assert "no-store" not in response.get("Cache-Control", "")
    assert "Cookie" in response["Vary"]
