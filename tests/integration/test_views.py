import pytest
from django.test import Client
from django.urls import reverse
from tests.factories.candy_factory import CandyProductFactory

pytestmark = pytest.mark.django_db

def test_add_to_shoppingcart_returns_partial_with_added_label(client):
    candy = CandyProductFactory(name="Sour Gummy Worms")
    url = reverse("add_to_shoppingcart", args=[candy.id])
    response = client.post(url)
    assert response.status_code == 200
    assert b"Added" in response.content
    assert b"<html" not in response.content  # confirms it's a partial, not a full page

def test_candy_list_shows_all_candies(client):
    CandyProductFactory(name="Sour Gummy Worms")
    CandyProductFactory(name="Chocolate Fudge")

    response = client.get(reverse("candy_list"))

    assert response.status_code == 200
    assert b"Sour Gummy Worms" in response.content
    assert b"Chocolate Fudge" in response.content


def test_add_to_shoppingcart_rejects_get(client):
    """A GET must not mutate the shoppingcart.

    Without @require_POST, following the URL in a browser silently adds an item.
    """
    candy = CandyProductFactory()

    response = client.get(reverse("add_to_shoppingcart", args=[candy.id]))

    assert response.status_code == 405


def test_adding_the_same_candy_twice_accumulates_in_the_session(client):
    """The quantity must survive the request, not just reach the template.

    Two posts, not one, because only the second exercises the line that persists
    it. On the first add the key is absent, so SessionBase.setdefault routes
    through __setitem__, which marks the session modified by itself. On the
    second it returns the existing dict, and mutating that in place leaves the
    session clean -- request.session.modified = True in the view is the only
    thing that saves it. client.session re-reads the store, so this asserts what
    was written, not what was in memory.
    """
    candy = CandyProductFactory()
    url = reverse("add_to_shoppingcart", args=[candy.id])

    client.post(url)
    client.post(url)

    assert client.session["shoppingcart"] == {str(candy.id): 2}


# --- CSRF -----------------------------------------------------------------
#
# The default test client bypasses CSRF entirely, so the tests above pass even
# though every hx-post 403s in a real browser. These use enforce_csrf_checks so
# the suite actually sees what the browser sees.

def test_catalog_page_supplies_csrf_token_to_htmx():
    """The page must hand htmx a CSRF token for its hx-post requests."""
    csrf_client = Client(enforce_csrf_checks=True)
    CandyProductFactory()

    page = csrf_client.get(reverse("candy_list"))

    assert page.status_code == 200
    assert b"hx-headers" in page.content
    assert b"X-CSRFToken" in page.content


def test_add_to_shoppingcart_accepts_post_with_the_token_the_page_supplies():
    """The token the page hands out must actually satisfy the view."""
    csrf_client = Client(enforce_csrf_checks=True)
    candy = CandyProductFactory()

    csrf_client.get(reverse("candy_list"))
    token = csrf_client.cookies["csrftoken"].value

    response = csrf_client.post(
        reverse("add_to_shoppingcart", args=[candy.id]),
        headers={"x-csrftoken": token},
    )

    assert response.status_code == 200


def test_add_to_shoppingcart_rejects_post_without_csrf_token():
    """CSRF protection stays on; the fix supplies a token, it does not exempt."""
    csrf_client = Client(enforce_csrf_checks=True)
    candy = CandyProductFactory()

    response = csrf_client.post(reverse("add_to_shoppingcart", args=[candy.id]))

    assert response.status_code == 403