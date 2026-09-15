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

# --- UC-03: candy detail ---------------------------------------------------

def test_candy_detail_shows_name_description_and_price(client):
    """UC-03 step 2. The flaw is asserted separately -- that is UC-06."""
    candy = CandyProductFactory(
        name="Hollow Humbug",
        description="Looks solid. Is not.",
        price="9.95",
    )

    response = client.get(reverse("candy_detail", args=[candy.id]))

    assert response.status_code == 200
    assert b"Hollow Humbug" in response.content
    assert b"Looks solid. Is not." in response.content
    assert b"9.95" in response.content


def test_candy_detail_offers_both_ways_out(client):
    """UC-03 step 3: return to the catalog, or add to the cart."""
    candy = CandyProductFactory()

    response = client.get(reverse("candy_detail", args=[candy.id]))

    # As an attribute, not a bare substring: the catalog is mounted at "/", so
    # `reverse("candy_list").encode() in response.content` asserts that b"/"
    # appears somewhere in the HTML, which no document can fail.
    assert f'href="{reverse("candy_list")}"'.encode() in response.content
    assert reverse("add_to_shoppingcart", args=[candy.id]).encode() in response.content


def test_candy_detail_404s_for_an_item_that_does_not_exist(client):
    """UC-03 extension 2a, as far as the current model can express it.

    Publication state is not modelled, so 'unpublished' has no representation
    and only deletion is testable -- see docs/ai/night-2026-09-15/questions.md
    Q2. This asserts the status, so whichever way that question is answered has
    a test to change rather than a gap to discover.
    """
    candy = CandyProductFactory()
    url = reverse("candy_detail", args=[candy.id])
    candy.delete()

    assert client.get(url).status_code == 404


def test_catalog_links_each_candy_to_its_detail_page(client):
    """UC-03 step 1 needs the catalog to be where the customer selects an item."""
    candy = CandyProductFactory(name="Sour Gummy Worms")

    response = client.get(reverse("candy_list"))

    expected = f'href="{reverse("candy_detail", args=[candy.id])}"'
    assert expected.encode() in response.content


# --- UC-06: flaw disclosure ------------------------------------------------

def test_candy_detail_discloses_the_flaw(client):
    """UC-06 step 3, and UC-03 step 2's fourth field."""
    candy = CandyProductFactory(
        name="Hollow Humbug",
        flaw="Dissolves into a sticky film that outlasts the flavour.",
    )

    response = client.get(reverse("candy_detail", args=[candy.id]))

    assert b"Dissolves into a sticky film that outlasts the flavour." in response.content


def test_the_flaw_is_labelled_as_a_flaw(client):
    """A disclosure indistinguishable from the sales copy discloses nothing.

    UC-06's success guarantee is that the detail view *shows a flaw* -- so the
    text has to be identifiable as one, not merely present somewhere on the
    page. This asserts the labelled region exists; the browser test asserts the
    reader can see it.
    """
    candy = CandyProductFactory()

    response = client.get(reverse("candy_detail", args=[candy.id]))

    assert b'data-testid="candy-flaw"' in response.content
    assert b"Known flaw" in response.content
