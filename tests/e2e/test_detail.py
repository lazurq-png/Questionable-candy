"""UC-03 (view a candy's description) in a real browser.

The catalog -> detail -> catalog journey is the part the integration tests
cannot make: they assert that a URL appears in some markup, not that clicking
it arrives anywhere.
"""
from playwright.sync_api import expect

from tests.factories.candy_factory import CandyFactory


def test_selecting_a_candy_opens_its_detail_page(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-03 steps 1-2: select an item, see its name, description and price."""
    CandyFactory(
        name="Hollow Humbug",
        description="Looks solid. Is not.",
        price="9.95",
    )

    page.goto(live_server.url)
    page.get_by_role("link", name="Hollow Humbug").click()

    expect(page.get_by_role("heading", name="Hollow Humbug")).to_be_visible()
    expect(page.get_by_test_id("candy-description")).to_have_text("Looks solid. Is not.")
    expect(page.get_by_test_id("candy-price")).to_have_text("$9.95")
    assert_page_is_fully_rendered(page)


def test_the_detail_page_returns_to_the_catalog(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-03 step 3, the first of its two exits."""
    CandyFactory(name="Hollow Humbug")

    page.goto(live_server.url)
    page.get_by_role("link", name="Hollow Humbug").click()
    page.get_by_test_id("back-to-catalog").click()

    expect(page.get_by_role("heading", name="Candy shop")).to_be_visible()
    expect(page.get_by_role("link", name="Hollow Humbug")).to_be_visible()
    assert_page_is_fully_rendered(page)


def test_adding_to_the_cart_from_the_detail_page(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-03 step 3, the second exit.

    The catalog and the detail page include the same button partial, so this
    is not quite a duplicate of the catalog's add-to-cart test: it is the check
    that the shared partial works on a page that reaches it by {% include %}
    rather than by being the page it was written for.
    """
    CandyFactory(name="Hollow Humbug")

    page.goto(live_server.url)
    page.get_by_role("link", name="Hollow Humbug").click()
    # click() returns once the navigation starts, not once the new page has
    # loaded, so htmx -- a blocking script from unpkg -- may still be
    # downloading. wait_for_url waits for the load event by default. Without
    # it this passed locally with htmx cached and failed in CI's cold browser.
    page.wait_for_url("**/candy/*/")

    assert page.evaluate("typeof window.htmx") == "object", (
        "htmx did not load from the CDN; the cart assertions below cannot mean "
        "anything. This is a network problem, not a regression in the view."
    )

    page.get_by_role("button", name="Add to cart").click()

    expect(page.get_by_role("button", name="Added! (Hollow Humbug)")).to_be_visible()
    assert_page_is_fully_rendered(page)


def test_the_flaw_is_visible_to_the_customer(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-06 step 3, in the browser.

    The integration test asserts the flaw is in the markup. That is not the
    same claim: markup can be present and the reader still never see it.
    `to_be_visible` is the one that matches UC-06's success guarantee, and it
    is the assertion that would start failing the day this page is styled and
    the disclosure ends up hidden, collapsed or off-screen.
    """
    CandyFactory(
        name="Hollow Humbug",
        flaw="Dissolves into a sticky film that outlasts the flavour.",
    )

    page.goto(live_server.url)
    page.get_by_role("link", name="Hollow Humbug").click()

    flaw = page.get_by_test_id("candy-flaw")
    expect(flaw).to_be_visible()
    expect(flaw).to_contain_text("Dissolves into a sticky film that outlasts the flavour.")
    expect(page.get_by_role("heading", name="Known flaw")).to_be_visible()
    assert_page_is_fully_rendered(page)


def test_an_unpublished_candy_is_hidden_and_says_it_is_unavailable(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-01 step 2 and UC-03 extension 2a, as a customer meets them.

    The catalog no longer lists it, and following an old link to it explains
    why and leads back -- rather than an unexplained error page.
    """
    CandyFactory(name="Sour Bricks")
    withdrawn = CandyFactory(name="Withdrawn Toffee", is_published=False)

    page.goto(live_server.url)
    expect(page.get_by_role("link", name="Sour Bricks")).to_be_visible()
    expect(page.get_by_role("link", name="Withdrawn Toffee")).to_have_count(0)

    page.goto(f"{live_server.url}/candy/{withdrawn.pk}/")
    expect(page.get_by_test_id("candy-unavailable")).to_be_visible()
    assert_page_is_fully_rendered(page)

    page.get_by_test_id("back-to-catalog").click()
    expect(page.get_by_role("heading", name="Candy shop")).to_be_visible()
