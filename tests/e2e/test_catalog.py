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


def test_the_stepper_adds_and_takes_out_in_the_browser(
    live_server, page, assert_page_is_fully_rendered
):
    """The htmx round trip end to end: click, POST, swap.

    This is the assertion the test client cannot make. The POST carries the
    CSRF token from base.html's hx-headers; without it CsrfViewMiddleware
    answers 403, htmx swaps nothing, and the quantity stays at 0 -- so the
    expectation below fails exactly where the browser would.
    """
    CandyFactory(name="Sour Gummy Worms", stock=5)

    page.goto(live_server.url)

    # htmx comes from unpkg (ADR 0006 accepted the no-offline-story cost). If
    # the CDN is unreachable, nothing below can work -- checked here so the
    # failure says "htmx did not load" rather than pointing at the cart.
    assert page.evaluate("typeof window.htmx") == "object", (
        "htmx did not load from the CDN; the cart assertions below cannot mean "
        "anything. This is a network problem, not a regression in the view."
    )

    # The bar is the whole control, from the start.
    quantity = page.get_by_test_id("cart-stepper-quantity")
    expect(page.get_by_test_id("cart-stepper")).to_be_visible()
    expect(quantity).to_have_value("0")

    for expected in ("1", "2", "3"):
        page.get_by_role("button", name="Add to cart").click()
        expect(quantity).to_have_value(expected)
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("3")

    page.get_by_role("button", name="Remove one from cart").click()
    expect(quantity).to_have_value("2")
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("2")
    expect(page.get_by_test_id("announcer")).to_have_text("Removed one Sour Gummy Worms from your cart.")

    # Nothing is laid over the number, so it is the number that is read -- an
    # "Add to cart" cover used to sit here and flashed the old count after each
    # swap, until the pointer moved and the browser re-checked hover.
    expect(quantity).to_have_value("2")
    assert_page_is_fully_rendered(page)


def test_a_typed_number_is_set_with_ok_or_enter(
    live_server, page, assert_page_is_fully_rendered, wait_for_htmx_to_settle
):
    """Type over the quantity: Ok appears, and Ok or Enter puts exactly that many in the cart."""
    CandyFactory(name="Sour Gummy Worms", stock=5)
    page.goto(live_server.url)

    quantity = page.get_by_role("textbox", name="Number in cart: Sour Gummy Worms")
    ok = page.get_by_role("button", name="Ok")
    expect(ok).to_be_hidden()

    quantity.fill("3")
    expect(ok).to_be_visible()

    ok.click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("3")
    expect(quantity).to_have_value("3")
    expect(ok).to_be_hidden()
    expect(quantity).to_be_focused()

    wait_for_htmx_to_settle(page)
    quantity.fill("40")
    quantity.press("Enter")
    expect(page.get_by_test_id("add-to-cart-message")).to_have_text("Only 5 in stock")
    expect(quantity).to_have_value("5")
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("5")

    wait_for_htmx_to_settle(page)
    quantity.fill("0")
    quantity.press("Enter")
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("0")
    expect(page.get_by_role("button", name="Remove one from cart")).to_have_attribute("aria-disabled", "true")
    assert_page_is_fully_rendered(page)


def test_the_stepper_is_usable_from_the_keyboard(live_server, page, wait_for_htmx_to_settle):
    """Tab reaches each control in turn, and focus survives every swap -- minus at zero included."""
    CandyFactory(name="Sour Gummy Worms", stock=5)
    page.goto(live_server.url)

    page.get_by_role("link", name="Sour Gummy Worms").focus()
    page.keyboard.press("Tab")
    minus = page.get_by_role("button", name="Remove one from cart: Sour Gummy Worms")
    expect(minus).to_be_focused()

    page.keyboard.press("Tab")
    expect(page.get_by_test_id("cart-stepper-quantity")).to_be_focused()
    page.keyboard.press("Tab")  # Ok is hidden, so straight on to plus
    plus = page.get_by_role("button", name="Add to cart: Sour Gummy Worms")
    expect(plus).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("cart-stepper-quantity")).to_have_value("1")
    expect(plus).to_be_focused()

    wait_for_htmx_to_settle(page)
    minus.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("cart-stepper-quantity")).to_have_value("0")
    expect(minus).to_have_attribute("aria-disabled", "true")
    expect(minus).to_be_focused()


def test_minus_and_plus_grey_out_at_the_ends_of_what_the_cart_can_hold(
    live_server, page, wait_for_htmx_to_settle
):
    """Nothing to take out, and nothing left to add: each end says so on the control."""
    CandyFactory(name="Butterscotch Pillows", stock=2)
    page.goto(live_server.url)

    minus = page.get_by_role("button", name="Remove one from cart")
    plus = page.get_by_role("button", name="Add to cart")
    live = plus.evaluate("el => getComputedStyle(el).backgroundColor")

    expect(minus).to_have_attribute("aria-disabled", "true")
    assert minus.evaluate("el => getComputedStyle(el).backgroundColor") != live
    expect(plus).not_to_have_attribute("aria-disabled", "true")

    plus.click()
    expect(page.get_by_test_id("cart-stepper-quantity")).to_have_value("1")
    expect(minus).not_to_have_attribute("aria-disabled", "true")
    expect(plus).not_to_have_attribute("aria-disabled", "true")

    plus.click()  # the last one in stock
    expect(page.get_by_test_id("cart-stepper-quantity")).to_have_value("2")
    expect(plus).to_have_attribute("aria-disabled", "true")
    assert plus.evaluate("el => getComputedStyle(el).backgroundColor") != live

    # Greyed out, not disabled: it can still be pressed, and then says why.
    # Playwright refuses to click an aria-disabled element, so force past its
    # check -- a real pointer or the Enter key has no such scruples.
    wait_for_htmx_to_settle(page)
    plus.click(force=True)
    expect(page.get_by_test_id("add-to-cart-message")).to_have_text("Out of stock")


def test_a_refusal_pops_up_over_the_page_without_moving_any_bar(
    live_server, page, wait_for_htmx_to_settle
):
    """The message is a bubble, not a line in the card.

    In the flow it made the card taller, so telling the customer anything
    nudged that bar and every other bar on the row -- the bars being what the
    customer is aiming at.
    """
    for name in ("Butterscotch Pillows", "Cola Bottles", "Hollow Humbug"):
        CandyFactory(name=name, stock=1)
    page.goto(live_server.url)

    bars = page.get_by_test_id("cart-stepper")
    expect(bars).to_have_count(3)
    before = [bars.nth(index).bounding_box() for index in range(3)]

    card = page.get_by_role("listitem").filter(has_text="Butterscotch Pillows")
    card.get_by_role("button", name="Add to cart").click()
    expect(card.get_by_test_id("cart-stepper-quantity")).to_have_value("1")
    wait_for_htmx_to_settle(page)
    card.get_by_role("button", name="Add to cart").click(force=True)  # nothing left in stock

    bubble = card.get_by_test_id("add-to-cart-message")
    expect(bubble).to_be_visible()
    assert [bars.nth(index).bounding_box() for index in range(3)] == before, "a bar moved"

    # Out of the flow and over the card, above its bar, rather than in line.
    stepper = card.get_by_test_id("cart-stepper").bounding_box()
    box = bubble.bounding_box()
    assert box["y"] + box["height"] <= stepper["y"], (stepper, box)
    assert bubble.evaluate("el => getComputedStyle(el).position") == "absolute"


def test_candy_pictures_load_in_the_catalog_and_in_the_detail_popup(
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
    detail_image = page.get_by_test_id("candy-popup").get_by_role("img", name="Sour Bricks")
    expect(detail_image).to_have_js_property("complete", True)
    assert detail_image.evaluate("img => img.naturalWidth") > 0
    assert_page_is_fully_rendered(page)
