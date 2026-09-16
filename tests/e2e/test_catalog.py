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

from shop.models import Candy
from tests.factories.candy_factory import CandyFactory


def test_catalog_renders_the_available_candy(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-01 steps 1-3: the catalog a customer opens lists what is for sale."""
    CandyFactory(name="Sour Gummy Worms", price="2.50")
    CandyFactory(name="Chocolate Fudge", price="4.00")

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
    assert not Candy.objects.exists()

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
    CandyFactory(name="Sour Gummy Worms")

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


def test_candy_pictures_load_in_the_catalog_and_on_the_detail_page(
    live_server, page, assert_page_is_fully_rendered
):
    """An <img> with a wrong static path still renders -- as a broken icon.

    naturalWidth is 0 for an image the browser could not load or decode, so
    this fails on a missing file, a wrong URL or a malformed SVG, none of which
    the HTML alone would show. The second candy has no picture and must get the
    placeholder rather than a broken image.
    """
    CandyFactory(name="Sour Bricks", image="shop/candy/sour-bricks.svg")
    CandyFactory(name="Mystery Mix", image="")

    page.goto(live_server.url)
    images = page.get_by_test_id("candy-image")
    expect(images).to_have_count(2)
    for index in range(2):
        image = images.nth(index)
        expect(image).to_have_js_property("complete", True)
        assert image.evaluate("img => img.naturalWidth") > 0, image.get_attribute("src")
    expect(page.get_by_role("img", name="Mystery Mix")).to_have_attribute(
        "src", "/static/shop/candy/placeholder.svg"
    )

    page.get_by_role("link", name="Sour Bricks").click()
    page.wait_for_url("**/candy/*/")
    detail_image = page.get_by_role("img", name="Sour Bricks")
    expect(detail_image).to_have_js_property("complete", True)
    assert detail_image.evaluate("img => img.naturalWidth") > 0
    assert_page_is_fully_rendered(page)
