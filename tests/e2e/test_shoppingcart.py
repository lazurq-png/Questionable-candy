"""UC-04 in a real browser: every cart interaction is a click and an htmx swap.

The integration tests prove the server's rules. These prove the page carries
them out: that the hx-post fires with a CSRF token, the right fragment is
swapped in, and the header count and totals follow along without a reload.
"""
from decimal import Decimal

from playwright.sync_api import expect

from tests.factories.candy_factory import CandyFactory


def open_cart(page):
    """Follow the header link, and wait for the cart page itself."""
    page.get_by_test_id("shoppingcart-link").click()
    page.wait_for_url("**/shoppingcart/")
    expect(page.get_by_role("heading", name="Your cart")).to_be_visible()


def test_adding_from_the_catalog_updates_the_header_and_fills_the_cart(
    live_server, page, assert_page_is_fully_rendered
):
    """Steps 1, 3 and 5: add, see the change, review the cart."""
    CandyFactory(name="Sour Bricks", price=Decimal("2.50"), stock=5)

    page.goto(live_server.url)
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("0")
    page.get_by_role("button", name="Add to cart").click()

    expect(page.get_by_role("button", name="Added! (Sour Bricks)")).to_be_visible()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")

    open_cart(page)
    expect(page.get_by_test_id("shoppingcart-line")).to_have_count(1)
    expect(page.get_by_test_id("shoppingcart-total")).to_have_text("$2.50")
    assert_page_is_fully_rendered(page)


def test_changing_a_quantity_updates_the_totals_and_caps_at_stock(
    live_server, page, assert_page_is_fully_rendered
):
    """Step 4 and extension 2a, including the message the cap must show."""
    CandyFactory(name="Hollow Humbug", price=Decimal("1.25"), stock=3)
    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    open_cart(page)

    quantity = page.get_by_label("Quantity of Hollow Humbug", exact=True)
    quantity.fill("2")
    page.get_by_role("button", name="Update quantity of Hollow Humbug").click()
    expect(page.get_by_test_id("shoppingcart-total")).to_have_text("$2.50")
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("2")

    # htmx restores focus to the same-id element after replacing the cart, so
    # a keyboard user is not dropped back at the top of the page.
    expect(page.get_by_role("button", name="Update quantity of Hollow Humbug")).to_be_focused()

    page.get_by_label("Quantity of Hollow Humbug", exact=True).fill("40")
    page.get_by_role("button", name="Update quantity of Hollow Humbug").click()
    expect(page.get_by_test_id("shoppingcart-messages")).to_contain_text(
        "Only 3 of Hollow Humbug in stock"
    )
    # ...and the same message reaches the live region that was on the page all
    # along -- the element a screen reader is actually listening to.
    expect(page.get_by_test_id("announcer")).to_have_text(
        "Only 3 of Hollow Humbug in stock, so the quantity is 3."
    )
    expect(page.get_by_label("Quantity of Hollow Humbug", exact=True)).to_have_value("3")
    expect(page.get_by_test_id("shoppingcart-total")).to_have_text("$3.75")
    assert_page_is_fully_rendered(page)


def test_removing_the_last_item_shows_the_empty_cart(
    live_server, page, assert_page_is_fully_rendered
):
    """Step 4 and extension 4a."""
    CandyFactory(name="Sour Bricks", stock=5)
    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    open_cart(page)

    page.get_by_role("button", name="Remove Sour Bricks").click()

    expect(page.get_by_test_id("shoppingcart-empty")).to_be_visible()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("0")
    assert_page_is_fully_rendered(page)


def test_adding_more_than_is_in_stock_is_refused_on_the_page(
    live_server, page, assert_page_is_fully_rendered
):
    """Extension 2a, where the customer meets it: the second add of the last one."""
    CandyFactory(name="Butterscotch Pillows", stock=1)
    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")

    page.get_by_role("link", name="Butterscotch Pillows").click()
    page.wait_for_url("**/candy/*/")
    page.get_by_role("button", name="Add to cart").click()

    expect(page.get_by_test_id("add-to-cart-message")).to_have_text(
        "Only 1 in stock, and they are all in your cart."
    )
    expect(page.get_by_test_id("announcer")).to_have_text(
        "Only 1 in stock, and they are all in your cart."
    )
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    assert_page_is_fully_rendered(page)


def test_an_out_of_stock_candy_offers_no_add_to_cart(
    live_server, page, assert_page_is_fully_rendered
):
    """The button is there, disabled and saying why, rather than missing."""
    CandyFactory(name="Chili Mango Chews", stock=0)

    page.goto(live_server.url)

    expect(page.get_by_role("button", name="Out of stock")).to_be_disabled()
    expect(page.get_by_role("button", name="Add to cart")).to_have_count(0)
    assert_page_is_fully_rendered(page)
