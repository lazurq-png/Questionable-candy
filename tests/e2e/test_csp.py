"""The enforced Content-Security-Policy refuses nothing the site itself uses.

An enforced policy blocks a violating script or style and logs it to the
console; the page may still look fine if what was blocked was small (the 500
page's theme script, say). So each test walks real pages, does what a visitor
or an administrator does there, and fails on any CSP message.

Needs unpkg.com, where base.html loads htmx and Alpine from.
"""
import pytest
from playwright.sync_api import expect

from tests.e2e.test_checkout_confirm import reach_confirmation
from tests.factories.candy_factory import CandyFactory


def csp_messages(page):
    """A list that fills with every console message the page logs from now on."""
    messages = []
    page.on("console", lambda message: messages.append(message.text))
    return messages


def violations(messages):
    """The CSP ones: Chromium logs both enforced and report-only violations this way."""
    return [m for m in messages if "content security policy" in m.lower()]


def test_catalog_and_add_to_cart_raise_no_csp_violations(live_server, page):
    CandyFactory(name="Sour Gummy Worms", price="2.50")
    collected = csp_messages(page)

    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").first.click()
    expect(page.get_by_role("status")).to_contain_text("Added Sour Gummy Worms")

    assert violations(collected) == []


def test_signing_in_and_placing_an_order_raise_no_csp_violations(live_server, page):
    collected = csp_messages(page)

    reach_confirmation(page, live_server)
    page.get_by_label("I have checked my order: 2 items, $6.00").check()
    page.get_by_label("Type the total, $6.00, to confirm the amount").fill("6.00")
    page.get_by_role("button", name="Place my order").click()
    expect(page.get_by_test_id("order-payment-note")).to_be_visible()

    assert violations(collected) == []


def test_the_admin_raises_no_csp_violations(live_server, page, django_user_model):
    """Django's own admin templates run under the same policy."""
    django_user_model.objects.create_superuser("admin", "admin@example.com", "correct-horse-battery")
    CandyFactory(name="Sour Bricks")
    collected = csp_messages(page)

    page.goto(f"{live_server.url}/admin/login/?next=/admin/")
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("correct-horse-battery")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/admin/")
    for path in ("shop/candy/", "shop/candy/add/", "shop/order/", "accounts/user/"):
        page.goto(f"{live_server.url}/admin/{path}")
        expect(page.locator("#content")).to_be_visible()
    page.goto(f"{live_server.url}/admin/shop/candy/")
    page.get_by_role("link", name="Sour Bricks").click()
    expect(page.get_by_role("button", name="Save", exact=True)).to_be_visible()

    assert violations(collected) == []


@pytest.mark.urls("tests.integration.error_urls")
def test_the_500_page_raises_no_csp_violations(live_server, page, settings):
    """500.html renders with no request, so it has no nonce to give an inline script."""
    settings.DEBUG = False
    page.add_init_script("window.localStorage.setItem('theme', 'dark')")
    collected = csp_messages(page)

    response = page.goto(f"{live_server.url}/boom/")

    assert response.status == 500
    assert violations(collected) == []
    assert page.evaluate("document.documentElement.dataset.theme") == "dark"
