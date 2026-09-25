"""The order admin's lines in a real browser (shop/static/shop/admin/order_lines.js).

The integration tests post the forms these produce; only a browser shows that
the dialogs open and close, that the green plus and the red X save through
them, that a save's messages and errors arrive as popups, and that the page
comes back where it was.
"""
import uuid
from decimal import Decimal

import pytest
from django.utils import timezone
from playwright.sync_api import expect

from shop.cart import Line
from shop.checkout import order_snapshot
from shop.models import Candy, Order
from tests.factories.candy_factory import CandyFactory

PASSWORD = "correct-horse-battery"


def place(user, *pairs):
    """An order placed as checkout places it, for (candy, quantity) pairs."""
    lines = [Line(candy, quantity) for candy, quantity in pairs]
    snapshot = order_snapshot(lines, sum((line.total for line in lines), Decimal("0.00")))
    now = timezone.now()
    return Order.objects.place(user, snapshot, now, now, uuid.uuid4())


def stock(candy):
    """The candy's stock as the database has it now."""
    return Candy.objects.get(pk=candy.pk).stock


@pytest.fixture(name="admin")
def fixture_admin(django_user_model):
    """A superuser, who is also the customer on the orders here."""
    return django_user_model.objects.create_superuser("admin", "admin@example.com", PASSWORD)


@pytest.fixture(name="candies")
def fixture_candies():
    """Toffee, 5 in stock, and Drops, 2."""
    return (
        CandyFactory(name="Toffee", price=Decimal("3.00"), stock=5, flaw="Welds your molars together."),
        CandyFactory(name="Drops", price=Decimal("5.00"), stock=2),
    )


@pytest.fixture(name="open_order")
def fixture_open_order(live_server, page, assert_page_is_fully_rendered):
    """Log in and open an order's change page."""
    def open_order(order):
        page.goto(f"{live_server.url}/admin/login/?next=/admin/shop/order/{order.pk}/change/")
        page.get_by_label("Username").fill("admin")
        page.get_by_label("Password").fill(PASSWORD)
        page.get_by_role("button", name="Log in").click()
        page.wait_for_url(f"**/admin/shop/order/{order.pk}/change/")
        assert_page_is_fully_rendered(page)

    return open_order


def success_popup(page):
    """The popup a successful save leaves, in the corner."""
    return page.locator("ul.messagelist li.success")


def test_a_lines_candy_name_opens_its_details_in_a_dialog(page, admin, candies, open_order):
    """Click the name: the details show; Close and Escape each close them."""
    toffee, _ = candies
    open_order(place(admin, (toffee, 2)))

    expect(page.locator(".candy-line-title")).to_have_text("2 x Toffee")
    name = page.get_by_role("button", name="Toffee", exact=True)
    dialog = page.get_by_role("dialog", name="Toffee")
    expect(dialog).to_be_hidden()

    name.click()
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text("Welds your molars together.")
    expect(dialog).to_contain_text("$3.00")

    dialog.get_by_role("button", name="Close").click()
    expect(dialog).to_be_hidden()
    expect(name).to_be_focused()

    name.click()
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()


def test_the_green_plus_adds_a_line_through_a_dialog_and_saves(page, admin, candies, open_order):
    """No "Add another" row: the plus opens a dialog, and Enter there adds the line and saves."""
    toffee, drops = candies
    order = place(admin, (toffee, 2))
    open_order(order)

    expect(page.locator("#items-group .add-row")).to_have_count(0)
    expect(page.get_by_role("link", name="Add another Order item")).to_have_count(0)

    page.get_by_role("button", name="Add another Order item").click()
    dialog = page.get_by_role("dialog", name="Add a candy to the order")
    expect(dialog).to_be_visible()
    dialog.get_by_label("Candy").select_option(label="Drops")
    dialog.get_by_label("Quantity").fill("2")
    dialog.get_by_label("Quantity").press("Enter")

    expect(success_popup(page)).to_contain_text("was changed successfully")
    expect(page.locator(".candy-line-title", has_text="Drops")).to_have_text("2 x Drops")
    assert stock(drops) == 0
    order.refresh_from_db()
    assert order.total_amount == Decimal("16.00")

    page.get_by_role("button", name="Close message").click()
    expect(page.locator("ul.messagelist")).to_have_count(0)


def test_adding_a_candy_the_order_has_joins_its_line(page, admin, candies, open_order):
    """Saved at once, so the page comes back with one line, not two."""
    toffee, _ = candies
    order = place(admin, (toffee, 2))
    open_order(order)

    page.get_by_role("button", name="Add another Order item").click()
    dialog = page.get_by_role("dialog", name="Add a candy to the order")
    dialog.get_by_label("Candy").select_option(label="Toffee")
    dialog.get_by_label("Quantity").fill("1")
    dialog.get_by_role("button", name="Add").click()

    expect(success_popup(page)).to_be_visible()
    expect(page.locator(".candy-line-title")).to_have_text("3 x Toffee")
    assert order.items.get().quantity == 3
    assert stock(toffee) == 2


def test_a_refused_save_shows_its_errors_as_popups(page, admin, candies, open_order):
    """Not enough stock: the errors leave the page for a popup that stays until closed."""
    toffee, _ = candies
    order = place(admin, (toffee, 2))  # 3 left
    open_order(order)

    page.get_by_role("button", name="Add another Order item").click()
    dialog = page.get_by_role("dialog", name="Add a candy to the order")
    dialog.get_by_label("Candy").select_option(label="Toffee")
    dialog.get_by_label("Quantity").fill("9")
    dialog.get_by_role("button", name="Add").click()

    errors = page.locator("ul.messagelist li.error")
    expect(errors.filter(has_text="Not enough stock: Toffee.")).to_be_visible()
    expect(errors.filter(has_text="Please correct")).to_be_visible()
    expect(page.locator("#order_form .errornote")).to_have_count(0)
    expect(page.locator("#order_form ul.errorlist.nonform")).to_have_count(0)
    assert order.items.get().quantity == 2
    assert stock(toffee) == 3

    page.wait_for_timeout(6000)  # past the time a success message closes itself
    expect(errors).to_have_count(2)
    for close in page.get_by_role("button", name="Close message").all():
        close.click()
    expect(page.locator("ul.messagelist")).to_have_count(0)


def test_the_red_x_removes_a_line_once_confirmed(page, admin, candies, open_order):
    """Cancel keeps the line; Remove saves without it and returns its stock."""
    toffee, drops = candies
    order = place(admin, (toffee, 2), (drops, 1))  # stock: toffee 3, drops 1
    open_order(order)

    expect(page.locator('#items-group td.delete input[type="checkbox"]').first).to_be_hidden()
    confirm = page.get_by_role("dialog", name="Remove this line?")

    page.get_by_role("button", name="Remove Toffee").click()
    expect(confirm).to_contain_text("Remove 2 x Toffee from the order?")
    expect(confirm.get_by_role("button", name="Cancel")).to_be_focused()
    confirm.get_by_role("button", name="Cancel").click()
    expect(confirm).to_be_hidden()
    assert order.items.count() == 2

    page.get_by_role("button", name="Remove Toffee").click()
    confirm.get_by_role("button", name="Remove", exact=True).click()

    expect(success_popup(page)).to_be_visible()
    expect(page.get_by_role("button", name="Toffee", exact=True)).to_have_count(0)
    assert list(order.items.values_list("candy__name", flat=True)) == ["Drops"]
    assert stock(toffee) == 5
    order.refresh_from_db()
    assert order.total_amount == Decimal("5.00")


def test_dragging_out_of_a_dialog_does_not_close_it(page, admin, candies, open_order):
    """Selecting the quantity and letting go outside is not a click on the backdrop; a click there is."""
    open_order(place(admin, (candies[0], 2)))
    page.get_by_role("button", name="Add another Order item").click()
    dialog = page.get_by_role("dialog", name="Add a candy to the order")

    box = dialog.get_by_label("Quantity").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(5, 5)
    page.mouse.up()
    expect(dialog).to_be_visible()

    page.mouse.click(5, 5)
    expect(dialog).to_be_hidden()


def test_a_save_keeps_the_lines_where_they_were_on_screen(page, admin, candies, open_order):
    """The reloaded page scrolls back to the lines instead of starting at the top.

    A save that adds a line, because the page only grows: after one that
    shortens it, a page scrolled to its end cannot scroll as far again, and
    the lines rightly come back lower by the removed row.
    """
    toffee, _ = candies
    page.set_viewport_size({"width": 1024, "height": 420})
    open_order(place(admin, (toffee, 2)))

    lines_top = "document.getElementById('items-group').getBoundingClientRect().top"
    page.evaluate(f"window.scrollBy(0, {lines_top} - 60)")
    assert page.evaluate("window.scrollY") > 0, "the page must scroll for this to test anything"
    before = page.evaluate(lines_top)

    page.get_by_role("button", name="Add another Order item").click()
    dialog = page.get_by_role("dialog", name="Add a candy to the order")
    dialog.get_by_label("Candy").select_option(label="Drops")
    dialog.get_by_role("button", name="Add").click()

    expect(success_popup(page)).to_be_visible()
    assert page.evaluate("window.scrollY") > 0
    assert abs(page.evaluate(lines_top) - before) <= 1
