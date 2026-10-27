"""The report-only Content-Security-Policy reports nothing on the main pages.

A report-only policy blocks nothing, so a violation is visible only as a
console message. This loads the catalog, adds a candy (htmx and Alpine both
run) and fails on any CSP message, which is what must be true before the
policy is moved from SECURE_CSP_REPORT_ONLY to SECURE_CSP and enforced.

Needs unpkg.com, where base.html loads htmx and Alpine from.
"""
from playwright.sync_api import expect

from tests.factories.candy_factory import CandyFactory


def test_catalog_and_add_to_cart_raise_no_csp_violations(live_server, page):
    CandyFactory(name="Sour Gummy Worms", price="2.50")
    messages = []
    page.on("console", lambda message: messages.append(message.text))

    page.goto(live_server.url)
    page.get_by_role("button", name="Add to cart").first.click()
    expect(page.get_by_role("status")).to_contain_text("Added Sour Gummy Worms")

    violations = [m for m in messages if "content security policy" in m.lower()]
    assert violations == []
