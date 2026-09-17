"""The header's cart dropdown and the checkout it leads to, in a real browser.

The integration tests prove the fragment holds the right lines. These prove the
page around it: that the toggle opens it without navigating, that it stays in
view and beside the content rather than over it, that it keeps up with the
steppers while open, and that its Checkout button arrives at the checkout.
"""
from decimal import Decimal

import pytest
from playwright.sync_api import expect

from tests.factories.candy_factory import CandyFactory

DESKTOP = {"width": 1280, "height": 720}
TABLET = {"width": 800, "height": 1000}


def add(page, name):
    """Press a candy's plus on the catalog, and wait for the swap."""
    count = int(page.get_by_test_id("shoppingcart-count").inner_text())
    page.get_by_role("listitem").filter(has_text=name).get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text(str(count + 1))


def test_the_toggle_opens_the_dropdown_with_every_item_instead_of_navigating(
    live_server, page, assert_page_is_fully_rendered
):
    """Press Cart: the products, their quantities and the total, on the same page."""
    CandyFactory(name="Sour Bricks", price=Decimal("2.50"), stock=9, image="shop/candy/sour-bricks.svg")
    CandyFactory(name="Hollow Humbug", price=Decimal("1.25"), stock=9, image="shop/candy/sour-bricks.svg")
    page.goto(live_server.url)
    add(page, "Sour Bricks")
    add(page, "Sour Bricks")
    add(page, "Hollow Humbug")

    toggle = page.get_by_test_id("shoppingcart-link")
    expect(toggle).to_have_attribute("aria-expanded", "false")
    toggle.click()

    panel = page.get_by_test_id("cart-panel")
    expect(panel).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(panel.get_by_test_id("cart-panel-line")).to_have_count(2)
    expect(panel.get_by_test_id("cart-panel-total")).to_have_text("$6.25")
    # Each line has a small copy of the candy's own picture, and it loads.
    thumbnails = panel.locator(".cart-panel-line-image")
    expect(thumbnails).to_have_count(2)
    for index in range(2):
        thumbnail = thumbnails.nth(index)
        expect(thumbnail).to_have_attribute("src", "/static/shop/candy/sour-bricks.svg")
        expect(thumbnail).to_have_js_property("complete", True)
        assert thumbnail.evaluate("img => img.naturalWidth") > 0
        assert thumbnail.bounding_box()["width"] <= 48
    assert page.url == f"{live_server.url}/"
    assert_page_is_fully_rendered(page)

    toggle.click()
    expect(panel).to_be_hidden()

    # The close button arrives in an htmx swap, so its Alpine handler only works
    # if Alpine picked up the swapped-in markup.
    toggle.click()
    panel.get_by_role("button", name="Close cart").click()
    expect(panel).to_be_hidden()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(toggle).to_be_focused()


def test_the_dropdown_keeps_up_with_the_steppers_while_open(live_server, page):
    """An add or a removal on the page shows in the open dropdown without reopening it."""
    CandyFactory(name="Sour Bricks", price=Decimal("2.50"), stock=9)
    page.set_viewport_size(DESKTOP)
    page.goto(live_server.url)

    page.get_by_test_id("shoppingcart-link").click()
    panel = page.get_by_test_id("cart-panel")
    expect(panel.get_by_test_id("cart-panel-empty")).to_be_visible()

    add(page, "Sour Bricks")
    expect(panel.get_by_test_id("cart-panel-line")).to_have_count(1)
    expect(panel.get_by_test_id("cart-panel-total")).to_have_text("$2.50")

    add(page, "Sour Bricks")
    expect(panel.get_by_test_id("cart-panel-total")).to_have_text("$5.00")

    page.get_by_role("button", name="Remove one from cart: Sour Bricks").click()
    expect(panel.get_by_test_id("cart-panel-total")).to_have_text("$2.50")


@pytest.mark.parametrize("viewport", [DESKTOP, TABLET], ids=["desktop", "tablet"])
def test_the_dropdown_follows_the_window_and_leaves_the_content_uncovered(live_server, page, viewport):
    """A small window right of the catalog: nothing under it, nothing pushed down,
    and still on screen once the page has scrolled.
    """
    for number in range(24):
        CandyFactory(name=f"Candy {number:02}", stock=9)
    page.set_viewport_size(viewport)
    page.goto(live_server.url)
    heading_before = page.get_by_role("heading", name="Candy shop").bounding_box()
    add(page, "Candy 00")

    page.get_by_test_id("shoppingcart-link").click()
    panel = page.get_by_test_id("cart-panel")
    expect(panel.get_by_test_id("cart-panel-line")).to_have_count(1)

    main = page.locator("main").bounding_box()
    box = panel.bounding_box()
    assert box["x"] >= main["x"] + main["width"], (main, box)
    assert box["x"] + box["width"] <= viewport["width"], box
    assert box["width"] <= 18 * 16, box  # small: 18rem
    heading_after = page.get_by_role("heading", name="Candy shop").bounding_box()
    assert heading_after["y"] == heading_before["y"], "the catalog moved down"
    assert page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") == 0

    page.mouse.wheel(0, 2000)
    page.wait_for_function("window.scrollY > 1000")
    scrolled = panel.bounding_box()
    header = page.locator(".site-header").bounding_box()
    assert scrolled["y"] >= header["y"] + header["height"], (header, scrolled)
    assert scrolled["y"] + scrolled["height"] <= viewport["height"], scrolled
    expect(page.get_by_test_id("checkout-button")).to_be_in_viewport()


def test_escape_closes_the_dropdown_and_returns_focus_to_the_toggle(live_server, page):
    """Keyboard: open from the toggle, Tab into the dropdown, Escape back out."""
    CandyFactory(name="Sour Bricks", stock=9)
    page.goto(live_server.url)
    add(page, "Sour Bricks")

    toggle = page.get_by_test_id("shoppingcart-link")
    toggle.focus()
    page.keyboard.press("Space")
    panel = page.get_by_test_id("cart-panel")
    expect(panel.get_by_test_id("cart-panel-line")).to_have_count(1)

    page.keyboard.press("Tab")
    expect(panel.get_by_role("button", name="Close cart")).to_be_focused()

    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()
    expect(toggle).to_be_focused()


def test_checkout_from_the_dropdown_shows_the_order(
    live_server, page, assert_page_is_fully_rendered
):
    """The button at the bottom of the dropdown leads to the checkout page."""
    CandyFactory(name="Sour Bricks", price=Decimal("2.50"), stock=9)
    CandyFactory(name="Hollow Humbug", price=Decimal("1.25"), stock=9)
    page.goto(live_server.url)
    add(page, "Sour Bricks")
    add(page, "Hollow Humbug")

    page.get_by_test_id("shoppingcart-link").click()
    page.get_by_test_id("checkout-button").click()

    page.wait_for_url("**/checkout/")
    expect(page.get_by_role("heading", name="Checkout")).to_be_visible()
    expect(page.get_by_test_id("checkout-line")).to_have_count(2)
    expect(page.get_by_test_id("checkout-total")).to_have_text("$3.75")
    assert_page_is_fully_rendered(page)


def test_amounts_are_changed_on_the_checkout_itself(
    live_server, page, assert_page_is_fully_rendered, wait_for_htmx_to_settle
):
    """The checkout is where the order is corrected: its lines carry steppers,
    and the line total, the overall total and the header count all follow.
    """
    CandyFactory(name="Sour Bricks", price=Decimal("2.50"), stock=9)
    CandyFactory(name="Hollow Humbug", price=Decimal("1.25"), stock=9)
    page.goto(live_server.url)
    add(page, "Sour Bricks")
    add(page, "Hollow Humbug")
    page.goto(f"{live_server.url}/checkout/")

    line = page.get_by_test_id("checkout-line").filter(has_text="Sour Bricks")
    line.get_by_role("button", name="Add to cart").click()

    expect(line.get_by_test_id("cart-stepper-quantity")).to_have_value("2")
    # Two swaps land here -- the bar itself, then the whole order around it --
    # and the pressed button keeps focus through both.
    expect(line.get_by_role("button", name="Add to cart")).to_be_focused()
    expect(line).to_contain_text("$5.00")
    expect(page.get_by_test_id("checkout-total")).to_have_text("$6.25")
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("3")

    # Typed amounts too, and 0 takes the line off the order altogether.
    wait_for_htmx_to_settle(page)
    line.get_by_test_id("cart-stepper-quantity").fill("0")
    line.get_by_test_id("cart-stepper-quantity").press("Enter")

    expect(page.get_by_test_id("checkout-line")).to_have_count(1)
    expect(page.get_by_test_id("checkout-total")).to_have_text("$1.25")
    assert_page_is_fully_rendered(page)
