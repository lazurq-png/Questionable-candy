"""UC-06 steps 1-2 and extension 2a in a real browser, through the admin login.

The integration tests use Django's test client, which skips CSRF. This logs in
and submits the real forms, so a broken token or form would show up here.
"""
from playwright.sync_api import expect

from shop.admin import FLAW_REQUIRED
from shop.models import Candy


def test_an_administrator_is_prompted_for_a_flaw_before_saving(
    live_server, page, django_user_model, assert_page_is_fully_rendered
):
    """A save with no flaw is refused with the prompt; with one, it saves."""
    django_user_model.objects.create_superuser("admin", "admin@example.com", "correct-horse-battery")

    page.goto(f"{live_server.url}/admin/login/?next=/admin/shop/candy/add/")
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("correct-horse-battery")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/admin/shop/candy/add/")

    page.get_by_label("Name").fill("Sour Bricks")
    page.get_by_label("Flaw").fill("   ")
    page.get_by_label("Price").fill("12.50")
    page.get_by_role("button", name="Save", exact=True).click()

    expect(page.get_by_text(FLAW_REQUIRED)).to_be_visible()
    assert_page_is_fully_rendered(page)
    assert not Candy.objects.exists()

    page.get_by_label("Flaw").fill("Chips a tooth on contact.")
    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/shop/candy/")

    assert Candy.objects.get(name="Sour Bricks").flaw == "Chips a tooth on contact."
