"""UC-01 (browse the catalog) and the add-to-cart flow, in a real browser.

`django.test.Client` cannot stand in for these. It does not enforce CSRF, does
not run htmx, and does not swap anything into a DOM -- which is how the
add-to-cart button came to return 403 in every real browser for two commits
while the suite stayed green (docs/adr/0006-frontend-htmx-alpine.md).

`live_server` runs a real server on a real port and pulls in `transactional_db`
by itself (pytest_django/fixtures.py:641), so rows created here are visible to
the server thread without a `django_db` marker.
"""
from playwright.sync_api import expect

from shop.models import CandyProduct
from tests.factories.candy_factory import CandyProductFactory


def test_catalog_renders_the_available_candy(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-01 steps 1-3: the catalog a customer opens lists what is for sale."""
    CandyProductFactory(name="Sour Gummy Worms", price="2.50")
    CandyProductFactory(name="Chocolate Fudge", price="4.00")

    page.goto(live_server.url)

    expect(page.get_by_role("heading", name="Candy shop")).to_be_visible()
    expect(page.get_by_text("Sour Gummy Worms")).to_be_visible()
    expect(page.get_by_text("Chocolate Fudge")).to_be_visible()
    expect(page.get_by_test_id("catalog-empty")).to_have_count(0)
    assert_page_is_fully_rendered(page)


def test_empty_catalog_says_so_instead_of_rendering_a_blank_page(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-01 extension 2a.

    A page with no items and no message is indistinguishable from one that
    failed to load, so the absence of candy must be stated.
    """
    # Arranged rather than assumed: this test means nothing if a previous test
    # left rows behind, and "empty because the suite happened to run in this
    # order" is not a precondition worth relying on.
    assert not CandyProduct.objects.exists()

    page.goto(live_server.url)

    expect(page.get_by_test_id("catalog-empty")).to_be_visible()
    expect(page.get_by_role("button", name="Add to cart")).to_have_count(0)
    assert_page_is_fully_rendered(page)


def test_add_to_cart_swaps_the_button_in_the_browser(
    live_server, page, assert_page_is_fully_rendered
):
    """The htmx round trip end to end: click, POST, swap.

    This is the assertion the test client cannot make. The POST carries the
    CSRF token from base.html's hx-headers; without it CsrfViewMiddleware
    answers 403, htmx swaps nothing, and the button keeps its original label --
    so the expectation below fails exactly where the browser would.
    """
    CandyProductFactory(name="Sour Gummy Worms")

    page.goto(live_server.url)

    # htmx comes from unpkg (ADR 0006 accepted the no-offline-story cost). If
    # the CDN is unreachable, nothing below can work -- checked here so the
    # failure says "htmx did not load" rather than pointing at the cart.
    assert page.evaluate("typeof window.htmx") == "object", (
        "htmx did not load from the CDN; the cart assertions below cannot mean "
        "anything. This is a network problem, not a regression in the view."
    )

    page.get_by_role("button", name="Add to cart").click()

    expect(page.get_by_role("button", name="Added! (Sour Gummy Worms)")).to_be_visible()
    expect(page.get_by_role("button", name="Add to cart")).to_have_count(0)
    assert_page_is_fully_rendered(page)
