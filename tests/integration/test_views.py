import pytest
from django.test import Client
from django.urls import reverse

from shop.models import Candy
from tests.factories.candy_factory import CandyFactory

pytestmark = pytest.mark.django_db

def test_add_to_shoppingcart_returns_partial_with_added_label(client):
    candy = CandyFactory(name="Sour Gummy Worms")
    url = reverse("add_to_shoppingcart", args=[candy.id])
    response = client.post(url)
    assert response.status_code == 200
    assert b"Added" in response.content
    assert b"<html" not in response.content  # confirms it's a partial, not a full page

def test_candy_list_shows_all_candies(client):
    CandyFactory(name="Sour Gummy Worms")
    CandyFactory(name="Chocolate Fudge")

    response = client.get(reverse("candy_list"))

    assert response.status_code == 200
    assert b"Sour Gummy Worms" in response.content
    assert b"Chocolate Fudge" in response.content


def test_add_to_shoppingcart_rejects_get(client):
    """A GET must not mutate the shoppingcart.

    Without @require_POST, following the URL in a browser silently adds an item.
    """
    candy = CandyFactory()

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
    candy = CandyFactory()
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
    CandyFactory()

    page = csrf_client.get(reverse("candy_list"))

    assert page.status_code == 200
    assert b"hx-headers" in page.content
    assert b"X-CSRFToken" in page.content


def test_add_to_shoppingcart_accepts_post_with_the_token_the_page_supplies():
    """The token the page hands out must actually satisfy the view."""
    csrf_client = Client(enforce_csrf_checks=True)
    candy = CandyFactory()

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
    candy = CandyFactory()

    response = csrf_client.post(reverse("add_to_shoppingcart", args=[candy.id]))

    assert response.status_code == 403

def test_the_catalog_lists_candy_alphabetically(client):
    """UC-01: a stable order. Created out of order, so insertion order cannot pass."""
    for name in ("Zesty Lime Drops", "Anise Twists", "Mint Humbugs"):
        CandyFactory(name=name)

    content = client.get(reverse("candy_list")).content.decode()

    positions = [content.index(name) for name in ("Anise Twists", "Mint Humbugs", "Zesty Lime Drops")]
    assert positions == sorted(positions)


def test_candy_sharing_a_name_keep_a_stable_order(client):
    """Names are not unique; the older row comes first, every time.

    Updating `first` moves it behind `second` in PostgreSQL's physical row
    order, so without the primary-key tie-break the two come out reversed --
    otherwise insertion order alone would pass this test.
    """
    first = CandyFactory(name="Gum", description="first")
    second = CandyFactory(name="Gum", description="second")
    Candy.objects.filter(pk=first.pk).update(description="first, edited")

    content = client.get(reverse("candy_list")).content.decode()

    first_link = f'href="{reverse("candy_detail", args=[first.pk])}"'
    second_link = f'href="{reverse("candy_detail", args=[second.pk])}"'
    assert content.index(first_link) < content.index(second_link)


# --- UC-03: candy detail ---------------------------------------------------

def test_candy_detail_shows_name_description_and_price(client):
    """UC-03 step 2. The flaw is asserted separately -- that is UC-06."""
    candy = CandyFactory(
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
    candy = CandyFactory()

    response = client.get(reverse("candy_detail", args=[candy.id]))

    # As an attribute, not a bare substring: the catalog is mounted at "/", so
    # `reverse("candy_list").encode() in response.content` asserts that b"/"
    # appears somewhere in the HTML, which no document can fail.
    assert f'href="{reverse("candy_list")}"'.encode() in response.content
    assert reverse("add_to_shoppingcart", args=[candy.id]).encode() in response.content


POPUP = {"HX-Request": "true", "HX-Target": "candy-popup-contents"}


def test_the_detail_popup_gets_the_details_without_the_page(client):
    """The popup's own request: the details, the flaw and the stepper, no page around them."""
    candy = CandyFactory(name="Hollow Humbug", description="Looks solid. Is not.", flaw="Hollow.")

    response = client.get(reverse("candy_detail", args=[candy.id]), headers=POPUP)
    content = response.content.decode()

    assert response.status_code == 200
    assert "<html" not in content
    assert 'id="candy-popup-title">Hollow Humbug<' in content
    assert "Looks solid. Is not." in content
    assert 'data-testid="candy-flaw"' in content
    assert f'id="dialog-cart-control-{candy.id}"' in content
    assert "HX-Target" in response["Vary"]


def test_every_candy_link_opens_the_popup(client):
    """The catalog's link carries both: href for no JavaScript, hx-get for the popup."""
    candy = CandyFactory(name="Sour Gummy Worms")

    content = client.get(reverse("candy_list")).content.decode()

    url = reverse("candy_detail", args=[candy.id])
    assert f'href="{url}" class="candy-card-name" hx-get="{url}" hx-target="#candy-popup-contents"' in content


def test_the_popup_for_an_unavailable_candy_says_so_with_200(client):
    """htmx does not swap a 404, so the popup would never open; the wording names nothing."""
    candy = CandyFactory(name="Withdrawn Toffee", is_published=False)

    response = client.get(reverse("candy_detail", args=[candy.id]), headers=POPUP)

    assert response.status_code == 200
    assert b'data-testid="candy-unavailable"' in response.content
    assert b"Withdrawn Toffee" not in response.content


def test_a_deleted_candy_is_no_longer_available(client):
    """UC-03 extension 2a: say so, and offer the way back to the catalog."""
    candy = CandyFactory()
    url = reverse("candy_detail", args=[candy.id])
    candy.delete()

    response = client.get(url)

    assert response.status_code == 404
    assert b'data-testid="candy-unavailable"' in response.content
    assert f'href="{reverse("candy_list")}"'.encode() in response.content


def test_an_unpublished_candy_is_no_longer_available_and_not_named(client):
    """The same response as a deleted one, so the page leaks nothing about it."""
    candy = CandyFactory(name="Withdrawn Toffee", is_published=False)

    response = client.get(reverse("candy_detail", args=[candy.id]))

    assert response.status_code == 404
    assert b'data-testid="candy-unavailable"' in response.content
    assert f'href="{reverse("candy_list")}"'.encode() in response.content
    assert b"Withdrawn Toffee" not in response.content


def test_catalog_hides_unpublished_candy(client):
    """UC-01 step 2: the catalog lists published items only."""
    CandyFactory(name="Sour Gummy Worms")
    CandyFactory(name="Withdrawn Toffee", is_published=False)

    response = client.get(reverse("candy_list"))

    assert b"Sour Gummy Worms" in response.content
    assert b"Withdrawn Toffee" not in response.content


def test_an_unpublished_candy_cannot_be_added_to_the_cart(client):
    """Otherwise a stale page or a guessed URL puts it in the cart anyway.

    Refused with 200 and a message rather than 404: htmx does not swap a 4xx
    response, so a 404 would leave the customer's click doing nothing visible.
    """
    candy = CandyFactory(is_published=False)

    response = client.post(reverse("add_to_shoppingcart", args=[candy.id]))

    assert response.status_code == 200
    assert b"no longer available" in response.content
    assert client.session.get("shoppingcart", {}) == {}


def test_a_deleted_candy_cannot_be_added_to_the_cart(client):
    """The same refusal for a candy deleted since the page was loaded."""
    candy = CandyFactory()
    url = reverse("add_to_shoppingcart", args=[candy.id])
    candy.delete()

    response = client.post(url)

    assert response.status_code == 200
    assert b"no longer available" in response.content
    assert client.session.get("shoppingcart", {}) == {}


def test_catalog_links_each_candy_to_its_detail_page(client):
    """UC-03 step 1 needs the catalog to be where the customer selects an item."""
    candy = CandyFactory(name="Sour Gummy Worms")

    response = client.get(reverse("candy_list"))

    expected = f'href="{reverse("candy_detail", args=[candy.id])}"'
    assert expected.encode() in response.content


# --- UC-06: flaw disclosure ------------------------------------------------

def test_candy_detail_discloses_the_flaw(client):
    """UC-06 step 3, and UC-03 step 2's fourth field."""
    candy = CandyFactory(
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
    candy = CandyFactory()

    response = client.get(reverse("candy_detail", args=[candy.id]))

    assert b'data-testid="candy-flaw"' in response.content
    assert b"Known flaw" in response.content


def test_admin_user_page_lets_an_administrator_edit_allergies(admin_client, django_user_model):
    """The swapped user model is registered, and its extra field is reachable.

    Registering UserAdmin as-is would pass a changelist check and still leave
    allergies off the form, because the stock fieldsets predate the field.
    """
    customer = django_user_model.objects.create_user(username="ada", allergies=["peanuts"])

    response = admin_client.get(reverse("admin:accounts_user_change", args=[customer.pk]))

    assert response.status_code == 200
    assert b'name="allergies"' in response.content
