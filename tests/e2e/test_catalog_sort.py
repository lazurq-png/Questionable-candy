"""UC-01 extension 3a in a real browser: the sort menu re-sorts in place.

django.test.Client cannot run htmx, so only a browser shows that changing
the menu swaps the grid without a page load, that the address keeps the
choice, and that the steppers in the swapped-in grid still work.
"""
from decimal import Decimal

from playwright.sync_api import expect

from shop.models import Candy, FlawSeverity


def make_catalog():
    """Three candy whose price and severity orders differ."""
    for name, price, severity in [
        ("Butterscotch Pillows", "4.60", FlawSeverity.MILD),
        ("Sour Bricks", "12.50", FlawSeverity.DENTAL),
        ("Ginger Snap Drops", "3.40", FlawSeverity.AWKWARD),
    ]:
        Candy.objects.create(name=name, price=Decimal(price), flaw="Flawed.", stock=5,
                             flaw_severity=severity)


def test_choosing_an_order_re_sorts_the_grid_without_a_page_load(
    live_server, page, assert_page_is_fully_rendered, wait_for_htmx_to_settle
):
    make_catalog()
    page.goto(live_server.url)
    names = page.locator(".candy-card-name")
    expect(names).to_have_text(["Butterscotch Pillows", "Ginger Snap Drops", "Sour Bricks"])
    # Survives an htmx swap, but not a full page load.
    page.evaluate("window.notReloaded = true")

    page.get_by_label("Sort").select_option("price")

    expect(names).to_have_text(["Ginger Snap Drops", "Butterscotch Pillows", "Sour Bricks"])
    assert page.evaluate("window.notReloaded") is True
    expect(page).to_have_url(f"{live_server.url}/?sort=price")
    assert_page_is_fully_rendered(page)

    page.get_by_label("Sort").select_option("severity")
    expect(names).to_have_text(["Butterscotch Pillows", "Ginger Snap Drops", "Sour Bricks"])
    expect(page.get_by_test_id("candy-severity")).to_have_text(
        ["Flaw severity: Mildly annoying", "Flaw severity: Socially awkward",
         "Flaw severity: Call your dentist"]
    )

    # The swapped-in steppers are live: htmx processed the new markup.
    wait_for_htmx_to_settle(page)
    page.get_by_role("button", name="Add to cart: Sour Bricks").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")


def test_a_reload_keeps_the_chosen_order(live_server, page):
    make_catalog()
    page.goto(f"{live_server.url}/?sort=price-desc")

    expect(page.locator(".candy-card-name")).to_have_text(
        ["Sour Bricks", "Butterscotch Pillows", "Ginger Snap Drops"]
    )
    expect(page.get_by_label("Sort")).to_have_value("price-desc")
