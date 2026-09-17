"""UC-03 (view a candy's description) in a real browser.

With JavaScript, a candy's name opens its details in a popup over the page it
was clicked on -- the catalog, the cart dropdown, the cart page. The detail page
itself remains for everyone else, reached by its URL. The integration tests
assert what the markup holds; these assert that clicking arrives somewhere.
"""
from decimal import Decimal

from playwright.sync_api import expect

from tests.factories.candy_factory import CandyFactory


def open_popup(page, name):
    """Click a candy's name and wait for its details to open over the page."""
    page.get_by_role("link", name=name).first.click()
    popup = page.get_by_test_id("candy-popup")
    expect(popup.get_by_role("heading", name=name)).to_be_visible()
    return popup


def test_selecting_a_candy_opens_its_details_in_a_popup(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-03 steps 1-2: name, description and price -- without leaving the catalog."""
    CandyFactory(
        name="Hollow Humbug",
        description="Looks solid. Is not.",
        price="9.95",
    )

    page.goto(live_server.url)
    popup = open_popup(page, "Hollow Humbug")

    expect(popup.get_by_test_id("candy-description")).to_have_text("Looks solid. Is not.")
    expect(popup.get_by_test_id("candy-price")).to_have_text("$9.95")
    assert page.url == f"{live_server.url}/"
    assert_page_is_fully_rendered(page)


def test_the_popup_closes_by_button_escape_and_backdrop(live_server, page):
    """Each way out closes it, and focus goes back to the link that opened it."""
    CandyFactory(name="Hollow Humbug")
    page.goto(live_server.url)
    link = page.get_by_role("link", name="Hollow Humbug")
    popup = page.get_by_test_id("candy-popup")

    open_popup(page, "Hollow Humbug")
    popup.get_by_role("button", name="Close details").click()
    expect(popup).to_be_hidden()
    expect(link).to_be_focused()

    open_popup(page, "Hollow Humbug")
    page.keyboard.press("Escape")
    expect(popup).to_be_hidden()

    open_popup(page, "Hollow Humbug")
    page.mouse.click(5, 400)  # the backdrop, well outside the popup
    expect(popup).to_be_hidden()


def test_the_detail_page_still_works_by_its_url_and_returns_to_the_catalog(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-03 step 3's first exit, for a shared link or a browser without JavaScript."""
    candy = CandyFactory(name="Hollow Humbug", description="Looks solid. Is not.")

    page.goto(f"{live_server.url}/candy/{candy.pk}/")
    expect(page.get_by_role("heading", name="Hollow Humbug", level=1)).to_be_visible()
    expect(page.get_by_test_id("candy-description")).to_have_text("Looks solid. Is not.")
    page.get_by_test_id("back-to-catalog").click()

    expect(page.get_by_role("heading", name="Candy shop")).to_be_visible()
    expect(page.get_by_role("link", name="Hollow Humbug")).to_be_visible()
    assert_page_is_fully_rendered(page)


def test_adding_to_the_cart_from_the_popup_updates_the_catalog_behind_it(
    live_server, page, assert_page_is_fully_rendered, wait_for_htmx_to_settle
):
    """UC-03 step 3's second exit. The same candy's stepper is on the card and in
    the popup; a change in one must show in both.
    """
    CandyFactory(name="Hollow Humbug", stock=5)

    page.goto(live_server.url)
    assert page.evaluate("typeof window.htmx") == "object", (
        "htmx did not load from the CDN; the cart assertions below cannot mean "
        "anything. This is a network problem, not a regression in the view."
    )
    popup = open_popup(page, "Hollow Humbug")

    expect(popup.get_by_test_id("cart-stepper-quantity")).to_have_value("0")
    popup.get_by_role("button", name="Add to cart").click()
    expect(popup.get_by_test_id("cart-stepper-quantity")).to_have_value("1")
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    wait_for_htmx_to_settle(page)
    popup.get_by_test_id("cart-stepper-quantity").fill("4")
    popup.get_by_role("button", name="Ok").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("4")
    assert_page_is_fully_rendered(page)

    popup.get_by_role("button", name="Close details").click()
    card = page.get_by_role("listitem").filter(has_text="Hollow Humbug")
    expect(card.get_by_test_id("cart-stepper-quantity")).to_have_value("4")


def test_a_candy_in_the_cart_dropdown_opens_the_popup(live_server, page):
    """The dropdown's names lead to the same popup as the catalog's."""
    CandyFactory(name="Hollow Humbug", flaw="Hollow.", stock=5)
    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")

    page.get_by_test_id("shoppingcart-link").click()
    page.get_by_test_id("cart-panel").get_by_role("link", name="Hollow Humbug").click()

    popup = page.get_by_test_id("candy-popup")
    expect(popup.get_by_role("heading", name="Hollow Humbug")).to_be_visible()
    expect(popup.get_by_test_id("candy-flaw")).to_contain_text("Hollow.")


def test_a_change_in_the_popup_updates_the_cart_page_behind_it(
    live_server, page, assert_page_is_fully_rendered
):
    """The cart page's names open the popup too, and its lines and total follow."""
    CandyFactory(name="Hollow Humbug", price=Decimal("1.25"), stock=5)
    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    page.goto(f"{live_server.url}/shoppingcart/")

    popup = open_popup(page, "Hollow Humbug")
    popup.get_by_role("button", name="Add to cart").click()

    expect(page.get_by_test_id("shoppingcart-total")).to_have_text("$2.50")
    expect(page.get_by_label("Quantity of Hollow Humbug", exact=True)).to_have_value("2")
    assert page.url == f"{live_server.url}/shoppingcart/"
    assert_page_is_fully_rendered(page)


def test_a_change_in_the_popup_updates_the_checkout_behind_it(live_server, page, wait_for_htmx_to_settle):
    """The same for the checkout: what is about to be ordered follows the popup."""
    CandyFactory(name="Hollow Humbug", price=Decimal("1.25"), stock=5)
    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    page.goto(f"{live_server.url}/checkout/")

    popup = open_popup(page, "Hollow Humbug")
    wait_for_htmx_to_settle(page)
    popup.get_by_test_id("cart-stepper-quantity").fill("3")
    popup.get_by_test_id("cart-stepper-quantity").press("Enter")

    expect(page.get_by_test_id("checkout-total")).to_have_text("$3.75")


def test_the_flaw_is_visible_to_the_customer(
    live_server, page, assert_page_is_fully_rendered
):
    """UC-06 step 3, in the browser -- in the popup and on the page.

    The integration test asserts the flaw is in the markup. That is not the
    same claim: markup can be present and the reader still never see it.
    `to_be_visible` is the one that matches UC-06's success guarantee, and it
    is the assertion that would start failing the day the details are styled
    and the disclosure ends up hidden, collapsed or off-screen.
    """
    candy = CandyFactory(
        name="Hollow Humbug",
        flaw="Dissolves into a sticky film that outlasts the flavour.",
    )

    page.goto(live_server.url)
    popup = open_popup(page, "Hollow Humbug")
    flaw = popup.get_by_test_id("candy-flaw")
    expect(flaw).to_be_visible()
    expect(flaw).to_contain_text("Dissolves into a sticky film that outlasts the flavour.")
    expect(popup.get_by_role("heading", name="Known flaw")).to_be_visible()
    assert_page_is_fully_rendered(page)

    page.goto(f"{live_server.url}/candy/{candy.pk}/")
    expect(page.get_by_test_id("candy-flaw")).to_be_visible()
    expect(page.get_by_role("heading", name="Known flaw")).to_be_visible()


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


def test_the_popup_shows_sugar_and_allergens(live_server, page, assert_page_is_fully_rendered):
    """Sugar per 100 g and the allergens' names, after the flaw (night-2026-09-17 T2)."""
    CandyFactory(name="Hollow Humbug", sugar_content_g=Decimal("97.0"), allergens=["milk", "gluten"])

    page.goto(live_server.url)
    popup = open_popup(page, "Hollow Humbug")

    expect(popup.get_by_test_id("candy-sugar")).to_have_text("97.0 g per 100 g")
    expect(popup.get_by_test_id("candy-allergens")).to_have_text("Cereals containing gluten, Milk")
    assert_page_is_fully_rendered(page)
