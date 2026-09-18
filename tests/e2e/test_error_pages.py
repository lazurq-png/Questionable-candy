"""The 404, 500 and CSRF pages in a real browser, at phone width.

The same measurable checks every other page gets (test_theme.check_page), and
the way back to the catalog actually works.

With JavaScript, a stale CSRF token on an htmx post gets a 403 that htmx does
not swap in, so the customer sees nothing. The CSRF page is what a plain form
post gets -- the cart page's forms without JavaScript, which the test below
reproduces with a native form.submit(), which htmx does not intercept.
"""
import pytest
from playwright.sync_api import expect

from tests.e2e.test_theme import background, check_page, show_theme
from tests.factories.candy_factory import CandyFactory

# (system setting, stored toggle choice, theme expected on screen)
THEMES = [("light", None, "light"), ("dark", None, "dark"), ("light", "dark", "dark")]


def _back_to_the_catalog(page, live_server):
    page.get_by_test_id("back-to-catalog").click()
    page.wait_for_url(f"{live_server.url}/")
    expect(page.get_by_role("heading", name="Candy shop")).to_be_visible()


@pytest.mark.parametrize("case", THEMES, ids=lambda case: f"system-{case[0]}-stored-{case[1]}")
def test_the_404_page_leads_back_to_the_catalog(
    live_server, page, settings, assert_page_is_fully_rendered, case
):
    """404.html extends base.html, so it is measured as any other page is."""
    settings.DEBUG = False
    expected = show_theme(page, case)

    response = page.goto(f"{live_server.url}/no-such-page/")

    assert response.status == 404
    expect(page.get_by_role("heading", name="This page melted away")).to_be_visible()
    assert background(page) == expected
    check_page(page, f"404 page, {case}", assert_page_is_fully_rendered)
    _back_to_the_catalog(page, live_server)


@pytest.mark.urls("tests.integration.error_urls")
@pytest.mark.parametrize("case", THEMES, ids=lambda case: f"system-{case[0]}-stored-{case[1]}")
def test_the_500_page_is_styled_and_leads_back_to_the_catalog(
    live_server, page, settings, assert_page_is_fully_rendered, case
):
    """500.html stands alone, so this checks its stylesheet and theme script load."""
    settings.DEBUG = False
    expected = show_theme(page, case)

    response = page.goto(f"{live_server.url}/boom/")

    assert response.status == 500
    expect(page.get_by_role("heading", name="Our candy machine jammed")).to_be_visible()
    assert background(page) == expected
    check_page(page, f"500 page, {case}", assert_page_is_fully_rendered)
    _back_to_the_catalog(page, live_server)


def test_a_plain_form_post_with_a_stale_token_shows_the_stale_form_page(
    live_server, page, settings, assert_page_is_fully_rendered
):
    """A cart page left open until its cookies are gone, then Remove without htmx."""
    settings.DEBUG = False
    expected = show_theme(page, THEMES[0])
    CandyFactory(name="Taffy", stock=5)
    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart: Taffy").click()
    expect(page.get_by_test_id("shoppingcart-count")).to_have_text("1")
    page.goto(f"{live_server.url}/shoppingcart/")
    expect(page.get_by_test_id("shoppingcart-line")).to_have_count(1)

    page.context.clear_cookies()
    with page.expect_navigation() as navigation:
        page.evaluate("document.querySelector('form.cart-line-remove').submit()")

    assert navigation.value.status == 403
    expect(page.get_by_role("heading", name="That form went stale")).to_be_visible()
    assert background(page) == expected
    check_page(page, "CSRF page", assert_page_is_fully_rendered)
    _back_to_the_catalog(page, live_server)
