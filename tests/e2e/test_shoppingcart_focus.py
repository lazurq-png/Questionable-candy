"""Keyboard focus after removing a cart line (.claude/rules/frontend.md, focus).

The Remove button a keyboard user just pressed is removed with its line. Left
alone, focus falls back to the page, and the user starts again from the top.

Every case uses three lines and a target that is not simply "the first line",
so the tests tell the position logic apart from a fixed choice.
"""
from playwright.sync_api import expect

from tests.factories.candy_factory import CandyFactory

NAMES = ("Anise Drops", "Butterscotch Pillows", "Cola Bottles")


def fill_cart(page, live_server, *names):
    """Add one of each named candy, then open the cart."""
    for name in names:
        CandyFactory(name=name, stock=5)
    page.goto(live_server.url)
    for count, name in enumerate(names, start=1):
        page.get_by_role("listitem").filter(has_text=name).get_by_role("button", name="Add to cart").click()
        expect(page.get_by_test_id("shoppingcart-count")).to_have_text(str(count))
    page.goto(f"{live_server.url}/shoppingcart/")


def test_removing_the_first_line_focuses_the_line_that_takes_its_place(live_server, page):
    """A, B, C without A: B is now first. Neither "first" nor "last" alone gets both this and the next case."""
    fill_cart(page, live_server, *NAMES)

    page.get_by_role("button", name="Remove Anise Drops").press("Enter")

    expect(page.get_by_test_id("shoppingcart-line")).to_have_count(2)
    expect(page.get_by_role("button", name="Remove Butterscotch Pillows")).to_be_focused()


def test_removing_a_middle_line_focuses_the_line_that_takes_its_place(
    live_server, page, assert_page_is_fully_rendered
):
    """Lines are sorted by name: removing B from A, B, C puts C where B was."""
    fill_cart(page, live_server, *NAMES)

    page.get_by_role("button", name="Remove Butterscotch Pillows").press("Enter")

    expect(page.get_by_test_id("shoppingcart-line")).to_have_count(2)
    expect(page.get_by_role("button", name="Remove Cola Bottles")).to_be_focused()
    assert_page_is_fully_rendered(page)


def test_removing_the_last_line_focuses_the_new_last_line(live_server, page):
    """Nothing moves into the last position, so focus goes to B, not to A."""
    fill_cart(page, live_server, *NAMES)

    page.get_by_role("button", name="Remove Cola Bottles").press("Enter")

    expect(page.get_by_test_id("shoppingcart-line")).to_have_count(2)
    expect(page.get_by_role("button", name="Remove Butterscotch Pillows")).to_be_focused()


def test_emptying_the_cart_focuses_the_way_back_to_the_catalog(live_server, page):
    """Extension 4a: with nothing left, the next thing to do is browse."""
    fill_cart(page, live_server, "Anise Drops")

    page.get_by_role("button", name="Remove Anise Drops").press("Enter")

    expect(page.get_by_test_id("shoppingcart-empty")).to_be_visible()
    expect(page.get_by_role("link", name="Browse the candy")).to_be_focused()
