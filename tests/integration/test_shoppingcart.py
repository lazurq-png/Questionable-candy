"""UC-04: manage the shopping cart, kept in the session.

Every client here enforces CSRF and posts with the token a page actually
handed out, because the default test client would pass even if every real
browser were refused (docs/adr/0006-frontend-htmx-alpine.md).
"""
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories.candy_factory import CandyFactory

pytestmark = pytest.mark.django_db

HTMX = {"HX-Request": "true"}


@pytest.fixture(name="shopper")
def fixture_shopper():
    """A browser-like client: CSRF enforced, token taken from a real page."""
    client = Client(enforce_csrf_checks=True)
    client.get(reverse("candy_list"))
    client.token = client.cookies["csrftoken"].value
    return client


def post(client, url, data=None, htmx=True):
    """POST with the page's CSRF token, as htmx would unless htmx=False."""
    headers = {"x-csrftoken": client.token, **(HTMX if htmx else {})}
    return client.post(url, data or {}, headers=headers)


def add(client, candy):
    """Press a candy's Add to cart button."""
    return post(client, reverse("add_to_shoppingcart", args=[candy.pk]))


def update(client, candy, quantity, htmx=True):
    """Submit a line's quantity form."""
    return post(client, reverse("update_shoppingcart", args=[candy.pk]), {"quantity": quantity}, htmx)


def stored(client):
    """What the session actually holds, bypassing every page."""
    return client.session.get("shoppingcart", {})


# --- Adding: UC-04 steps 1-3 and ext. 2a -------------------------------------

def test_adding_updates_the_session_and_the_header_count(shopper):
    """Step 3: the cart changes and the page shows the change."""
    candy = CandyFactory(stock=5)

    response = add(shopper, candy)

    assert stored(shopper) == {str(candy.pk): 1}
    assert b"Added!" in response.content
    assert b'hx-swap-oob="true"' in response.content
    assert b'data-testid="shoppingcart-count">1<' in response.content


def test_adding_beyond_stock_is_rejected_and_says_so(shopper):
    """Ext. 2a: with one in stock and one in the cart, a second add is refused."""
    candy = CandyFactory(stock=1)
    add(shopper, candy)

    response = add(shopper, candy)

    assert response.status_code == 200  # htmx only swaps 2xx; the message must show
    assert b"Only 1 in stock" in response.content
    assert stored(shopper) == {str(candy.pk): 1}


def test_an_out_of_stock_candy_cannot_be_added(shopper):
    """Ext. 2a at its limit: nothing to add at all."""
    candy = CandyFactory(stock=0)

    response = add(shopper, candy)

    assert b"out of stock" in response.content
    assert stored(shopper) == {}


def test_the_catalog_disables_add_to_cart_for_an_out_of_stock_candy(shopper):
    """No button that can only ever be refused."""
    CandyFactory(name="Chili Mango Chews", stock=0)

    response = shopper.get(reverse("candy_list"))

    assert b"Out of stock" in response.content
    assert b"hx-post" not in response.content


# --- The cart page: UC-04 step 5 and ext. 4a ---------------------------------

def test_the_cart_lists_items_quantities_line_totals_and_the_total(shopper):
    """Step 5: every line, its quantity, its total, and the overall total."""
    sour = CandyFactory(name="Sour Bricks", price=Decimal("2.50"), stock=9)
    humbug = CandyFactory(name="Hollow Humbug", price=Decimal("1.25"), stock=9)
    add(shopper, sour)
    add(shopper, sour)
    add(shopper, humbug)

    content = shopper.get(reverse("shoppingcart")).content.decode()

    assert content.count('data-testid="shoppingcart-line"') == 2
    assert 'value="2"' in content and 'value="1"' in content
    assert "$5.00" in content  # 2 × 2.50
    assert '<span data-testid="shoppingcart-total">$6.25</span>' in content


def test_an_empty_cart_says_so(shopper):
    """Ext. 4a."""
    response = shopper.get(reverse("shoppingcart"))

    assert b'data-testid="shoppingcart-empty"' in response.content


# --- Changing a quantity: UC-04 step 4 and ext. 2a ---------------------------

def test_a_quantity_within_stock_is_set(shopper):
    """Step 4: the ordinary edit."""
    candy = CandyFactory(stock=10)
    add(shopper, candy)

    response = update(shopper, candy, "4")

    assert stored(shopper) == {str(candy.pk): 4}
    assert b'value="4"' in response.content


def test_a_quantity_above_stock_is_capped_and_says_so(shopper):
    """Ext. 2a: capped, and the customer is told why the number changed."""
    candy = CandyFactory(name="Hollow Humbug", stock=3)
    add(shopper, candy)

    response = update(shopper, candy, "50")

    assert stored(shopper) == {str(candy.pk): 3}
    assert b"Only 3 of Hollow Humbug in stock" in response.content


@pytest.mark.parametrize("bad", ["0", "-2", "two", "", "1.5"])
def test_a_quantity_that_is_not_a_positive_whole_number_is_rejected(shopper, bad):
    """Untrusted input: refused with a message, the stored quantity untouched."""
    candy = CandyFactory(stock=10)
    add(shopper, candy)

    response = update(shopper, candy, bad)

    assert stored(shopper) == {str(candy.pk): 1}
    assert b'data-testid="shoppingcart-messages"' in response.content
    assert (b"at least 1" in response.content) or (b"whole number" in response.content)


def test_a_quantity_cannot_be_set_for_a_candy_not_in_the_cart(shopper):
    """A crafted post must not put a candy in the cart past the add rules."""
    candy = CandyFactory(stock=10)

    update(shopper, candy, "3")

    assert stored(shopper) == {}


def test_updating_a_candy_that_sold_out_since_removes_it_and_says_so(shopper):
    """The cart page was open while the last one sold elsewhere."""
    candy = CandyFactory(name="Hollow Humbug", stock=5)
    add(shopper, candy)
    candy.stock = 0
    candy.save()

    response = update(shopper, candy, "2")

    assert stored(shopper) == {}
    assert b"Hollow Humbug is out of stock" in response.content


def test_updating_a_candy_unpublished_since_reports_it_once(shopper):
    """The cart drops it and says so -- once, not once per code path."""
    candy = CandyFactory(name="Withdrawn Toffee")
    add(shopper, candy)
    candy.is_published = False
    candy.save()

    content = update(shopper, candy, "2").content.decode()

    assert stored(shopper) == {}
    assert content.count("no longer available") == 2  # the visible notice + the announcement


# --- Removing: UC-04 step 4 and ext. 4a ---------------------------------------

def test_removing_the_last_item_shows_the_empty_state(shopper):
    """Ext. 4a, and the header count follows."""
    candy = CandyFactory()
    add(shopper, candy)

    response = post(shopper, reverse("remove_from_shoppingcart", args=[candy.pk]))

    assert stored(shopper) == {}
    assert b'data-testid="shoppingcart-empty"' in response.content
    assert b'data-testid="shoppingcart-count">0<' in response.content


def test_removing_a_line_still_reports_what_changed_in_a_stale_cart(shopper):
    """A remove must not swallow the notices for entries dropped or capped."""
    kept = CandyFactory(name="Sour Bricks", stock=5)
    capped = CandyFactory(name="Hollow Humbug", stock=5)
    withdrawn = CandyFactory(name="Withdrawn Toffee")
    for candy in (kept, capped, withdrawn):
        add(shopper, candy)
    update(shopper, capped, "5")
    capped.stock = 2
    capped.save()
    withdrawn.is_published = False
    withdrawn.save()

    content = post(shopper, reverse("remove_from_shoppingcart", args=[kept.pk])).content.decode()

    assert "1 item is no longer available" in content
    assert "Only 2 of Hollow Humbug left in stock" in content


def test_a_plain_remove_reports_a_stale_cart_on_the_page_it_redirects_to(shopper):
    """The same, without htmx: the notice must survive the redirect."""
    kept = CandyFactory(name="Sour Bricks")
    withdrawn = CandyFactory(name="Withdrawn Toffee")
    add(shopper, kept)
    add(shopper, withdrawn)
    withdrawn.is_published = False
    withdrawn.save()

    response = post(shopper, reverse("remove_from_shoppingcart", args=[kept.pk]), htmx=False)

    assert response.status_code == 302
    assert b"no longer available" in shopper.get(response.url).content


# --- The shop changed since the cart was filled -------------------------------

def test_unpublished_and_deleted_candy_leave_the_cart_with_a_notice(shopper):
    """The cart may be days old; it is reconciled with the shop when viewed."""
    kept = CandyFactory(name="Sour Bricks")
    withdrawn = CandyFactory(name="Withdrawn Toffee")
    deleted = CandyFactory(name="Gone Gum")
    for candy in (kept, withdrawn, deleted):
        add(shopper, candy)
    withdrawn.is_published = False
    withdrawn.save()
    deleted.delete()

    content = shopper.get(reverse("shoppingcart")).content.decode()

    assert stored(shopper) == {str(kept.pk): 1}
    assert "2 items are no longer available" in content
    assert "Withdrawn Toffee" not in content


def test_a_quantity_above_current_stock_is_capped_when_the_cart_is_viewed(shopper):
    """Stock fell after the cart was filled."""
    candy = CandyFactory(name="Hollow Humbug", stock=5)
    add(shopper, candy)
    update(shopper, candy, "5")
    candy.stock = 2
    candy.save()

    content = shopper.get(reverse("shoppingcart")).content.decode()

    assert stored(shopper) == {str(candy.pk): 2}
    assert "Only 2 of Hollow Humbug left in stock" in content


def test_a_candy_that_sold_out_since_is_removed_when_the_cart_is_viewed(shopper):
    """Stock reached zero after the cart was filled."""
    candy = CandyFactory(name="Hollow Humbug", stock=5)
    add(shopper, candy)
    candy.stock = 0
    candy.save()

    content = shopper.get(reverse("shoppingcart")).content.decode()

    assert stored(shopper) == {}
    assert "Hollow Humbug is out of stock" in content


# --- Without JavaScript, and without a token ---------------------------------

def test_a_plain_form_post_redirects_back_to_the_cart_with_its_notice(shopper):
    """The forms work without htmx; the notice survives the redirect."""
    candy = CandyFactory(name="Hollow Humbug", stock=3)
    add(shopper, candy)

    response = update(shopper, candy, "50", htmx=False)

    assert response.status_code == 302
    assert response.url == reverse("shoppingcart")
    assert b"Only 3 of Hollow Humbug in stock" in shopper.get(response.url).content


def test_cart_changes_are_refused_without_a_csrf_token(shopper):
    """CSRF stays enforced on the new endpoints; the fix is the token, not an exemption."""
    candy = CandyFactory()
    add(shopper, candy)

    response = shopper.post(reverse("update_shoppingcart", args=[candy.pk]), {"quantity": "5"})

    assert response.status_code == 403
    assert stored(shopper) == {str(candy.pk): 1}


def test_cart_changes_are_post_only(client):
    """A followed link or a prefetch must not change the cart."""
    candy = CandyFactory()

    assert client.get(reverse("update_shoppingcart", args=[candy.pk])).status_code == 405
    assert client.get(reverse("remove_from_shoppingcart", args=[candy.pk])).status_code == 405


def test_a_corrupt_session_cart_is_ignored_rather_than_crashing(shopper):
    """Session contents are data written by older code, not a trusted schema."""
    session = shopper.session
    session["shoppingcart"] = {"abc": 1, "7": "many", "8": -3}
    session.save()

    response = shopper.get(reverse("shoppingcart"))

    assert response.status_code == 200
    assert b'data-testid="shoppingcart-empty"' in response.content
