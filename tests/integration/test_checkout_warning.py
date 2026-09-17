"""UC-07: the health warning step of checkout (night-2026-09-17 plan T4).

Clients enforce CSRF and post the token a real page handed out. Login itself is
covered by tests/integration/test_accounts.py, so these sign in with
force_login.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from shop.checkout import SESSION_KEY
from shop.models import Candy
from tests.factories.candy_factory import CandyFactory

pytestmark = pytest.mark.django_db

WARNING = reverse("checkout_warning")


def browser(user=None):
    """A CSRF-enforcing client, signed in as `user` if given, holding a page's token."""
    client = Client(enforce_csrf_checks=True)
    if user is not None:
        client.force_login(user)
    client.get(reverse("candy_list"))
    client.token = client.cookies["csrftoken"].value
    return client


def add(client, candy, times=1):
    """Press a candy's add-to-cart button `times` times, as htmx would."""
    for _ in range(times):
        client.post(reverse("add_to_shoppingcart", args=[candy.pk]),
                    headers={"x-csrftoken": client.token, "HX-Request": "true"})


def acknowledge(client, fingerprint=None, tick=True):
    """Submit the warning's form, with the fingerprint the page showed unless given."""
    if fingerprint is None:
        fingerprint = client.get(WARNING).context["warning"].fingerprint
    data = {"csrfmiddlewaretoken": client.token, "fingerprint": fingerprint}
    if tick:
        data["acknowledge"] = "on"
    return client.post(WARNING, data)


@pytest.fixture(name="ada")
def fixture_ada():
    """A customer who listed a milk allergy."""
    return get_user_model().objects.create_user(username="ada", password="x", allergies=["milk"])


@pytest.fixture(name="order")
def fixture_order():
    """Two candies with known sugar and allergens, and one with unknown sugar."""
    return {
        "fudge": CandyFactory(name="Maple Fudge", sugar_content_g=Decimal("78.0"), allergens=["milk"], stock=5),
        "ropes": CandyFactory(name="Blue Ropes", sugar_content_g=Decimal("50.0"), allergens=["gluten"], stock=5),
        "mystery": CandyFactory(name="Mystery Chews", sugar_content_g=None, allergens=[], stock=5),
    }


def test_the_warning_requires_login_and_returns_to_it_afterwards(order):
    """Checkout review is open to everyone; login starts at the warning."""
    client = browser()
    add(client, order["fudge"])

    response = client.get(WARNING)

    assert response.status_code == 302
    assert response["Location"] == f'{reverse("accounts:login")}?next={WARNING}'


def test_an_empty_cart_goes_back_to_the_cart_page(ada):
    """Nothing to warn about, so no warning step."""
    response = browser(ada).get(WARNING)

    assert response.status_code == 302
    assert response["Location"] == reverse("shoppingcart")


def test_a_cart_emptied_by_unpublishing_goes_back_with_the_reason(ada, order):
    """The cart's own notice about the removed candy reaches the cart page."""
    client = browser(ada)
    add(client, order["fudge"])
    Candy.objects.filter(pk=order["fudge"].pk).update(is_published=False)

    response = client.get(WARNING)

    assert response["Location"] == reverse("shoppingcart")
    assert "no longer available" in client.get(response["Location"]).content.decode()


def test_the_warning_shows_sugar_unknown_sugar_and_allergens_with_the_customers_own_marked(ada, order):
    """UC-07 step 1: the content is derived from this order and this customer."""
    client = browser(ada)
    add(client, order["fudge"], times=2)
    add(client, order["ropes"])
    add(client, order["mystery"])

    content = client.get(WARNING).content.decode()

    assert '<strong data-testid="warning-total-sugar">206.0 g</strong>' in content  # 78 x 2 + 50
    assert "Counted as 100 g of candy per bag." in content
    assert "Sugar is unknown for Mystery Chews" in content
    assert "Cereals containing gluten" in content
    assert "in Blue Ropes" in content
    assert content.count('data-testid="warning-yours"') == 1  # milk, in Maple Fudge
    assert "This order contains 1 allergen you listed" in content
    assert 'data-testid="warning-form"' in content


def test_continuing_without_ticking_the_box_is_refused(ada, order):
    """UC-07 ext. 3a: no acknowledgment, no progress."""
    client = browser(ada)
    add(client, order["fudge"])

    response = acknowledge(client, tick=False)

    assert response.status_code == 200
    assert "Tick the box to confirm you have read the health warning." in response.content.decode()
    assert SESSION_KEY not in client.session


def test_ticking_the_box_acknowledges_this_warning_and_moves_on_to_confirming(ada, order):
    """UC-07 steps 3-4: recorded, with when, then on to UC-08; coming back says so."""
    client = browser(ada)
    add(client, order["fudge"])

    response = acknowledge(client)

    assert response.status_code == 302
    assert response["Location"] == reverse("checkout_confirm")
    stored = client.session[SESSION_KEY]["warning"]
    assert stored["fingerprint"] == client.get(WARNING).context["warning"].fingerprint
    assert stored["at"]
    page = client.get(WARNING).content.decode()
    assert 'data-testid="warning-acknowledged"' in page
    assert f'href="{reverse("checkout_confirm")}" class="button" data-testid="warning-continue"' in page
    assert 'data-testid="warning-form"' not in page


def test_acknowledging_a_warning_that_has_since_changed_is_refused(ada, order):
    """The cart changed in another tab: the customer has not read this warning."""
    client = browser(ada)
    add(client, order["fudge"])
    shown = client.get(WARNING).context["warning"].fingerprint
    add(client, order["ropes"])

    response = acknowledge(client, fingerprint=shown)

    assert response.status_code == 200
    assert "Your order changed while the warning was open." in response.content.decode()
    assert SESSION_KEY not in client.session


def test_changing_the_cart_after_acknowledging_needs_a_new_acknowledgment(ada, order):
    """One more bag is a different warning."""
    client = browser(ada)
    add(client, order["fudge"])
    acknowledge(client)

    add(client, order["fudge"])

    page = client.get(WARNING)
    assert not page.context["acknowledged"]
    assert 'data-testid="warning-form"' in page.content.decode()


def test_changing_my_allergies_after_acknowledging_needs_a_new_acknowledgment(ada, order):
    """The matches are part of the warning, so they are part of what was read."""
    client = browser(ada)
    add(client, order["ropes"])
    acknowledge(client)

    ada.allergies = ["milk", "gluten"]
    ada.save()

    assert not client.get(WARNING).context["acknowledged"]


def test_the_warning_form_is_refused_without_a_csrf_token(ada, order):
    """The acknowledgment is protected like every other form."""
    client = browser(ada)
    add(client, order["fudge"])

    response = client.post(WARNING, {"acknowledge": "on", "fingerprint": "x"})

    assert response.status_code == 403


def test_the_checkout_review_offers_continue_only_with_something_to_order(order):
    """Open to everyone, so no login is needed to see it."""
    client = browser()
    assert 'data-testid="checkout-continue"' not in client.get(reverse("checkout")).content.decode()

    add(client, order["fudge"])

    content = client.get(reverse("checkout")).content.decode()
    assert f'href="{WARNING}" class="button" data-testid="checkout-continue"' in content


def test_a_cart_change_that_is_later_undone_still_needs_a_new_acknowledgment(ada, order):
    """Any change to the cart clears the acknowledgment, not only a lasting one."""
    client = browser(ada)
    add(client, order["fudge"])
    acknowledge(client)

    add(client, order["ropes"])
    client.post(reverse("remove_from_shoppingcart", args=[order["ropes"].pk]),
                {"csrfmiddlewaretoken": client.token})

    assert SESSION_KEY not in client.session
    assert not client.get(WARNING).context["acknowledged"]


def test_an_unticked_submit_of_a_changed_warning_says_so_and_shows_the_new_one(ada, order):
    """The notice does not wait for the tick, and the form carries the current fingerprint."""
    client = browser(ada)
    add(client, order["fudge"])
    shown = client.get(WARNING).context["warning"].fingerprint
    add(client, order["ropes"])

    response = acknowledge(client, fingerprint=shown, tick=False)

    content = response.content.decode()
    assert "Your order changed while the warning was open." in content
    assert f'value="{response.context["warning"].fingerprint}"' in content
    assert f'value="{shown}"' not in content
