"""Signing up, logging in and out, and "My allergies", in a real browser.

The integration tests (tests/integration/test_accounts.py) cover the rules;
these cover what only a browser shows: the header's account control, the
forms actually submitting with the tokens the pages hand out, and the new
pages meeting the measurable checks at phone width in both themes.
"""
import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect

from tests.e2e.test_theme import PHONE, check_page

PASSWORD = "candy-Shop-2026!"
WIDE = {"width": 1024, "height": 800}


def fill_sign_up(page, username):
    """Fill the sign-up form's username and both password fields."""
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password:", exact=True).fill(PASSWORD)
    page.get_by_label("Password confirmation").fill(PASSWORD)


def test_sign_up_returns_to_the_page_then_log_out(live_server, page, assert_page_is_fully_rendered):
    """Sign up from the cart page, land back on it signed in, then log out."""
    page.set_viewport_size(WIDE)
    page.goto(f"{live_server.url}/shoppingcart/")

    page.get_by_test_id("signup-link").click()
    page.wait_for_url("**/accounts/signup/**")
    fill_sign_up(page, "bea")
    page.get_by_label("Milk").check()
    page.get_by_role("button", name="Create account").click()

    page.wait_for_url(f"{live_server.url}/shoppingcart/")
    expect(page.get_by_test_id("account-menu-toggle")).to_have_text("bea, account menu")
    expect(page.get_by_role("group").get_by_text("bea", exact=True)).to_be_visible()
    expect(page.get_by_test_id("login-link")).to_have_count(0)
    assert get_user_model().objects.get(username="bea").allergies == ["milk"]
    assert_page_is_fully_rendered(page)

    page.get_by_test_id("account-menu-toggle").click()
    page.get_by_test_id("logout-button").click()

    page.wait_for_url(f"{live_server.url}/")
    expect(page.get_by_test_id("login-link")).to_be_visible()
    expect(page.get_by_test_id("account-menu")).to_have_count(0)


def test_log_in_from_a_phone_and_change_my_allergies(live_server, page, assert_page_is_fully_rendered):
    """The phone header's one account control, then the allergies page it leads to."""
    get_user_model().objects.create_user(username="ada", password=PASSWORD, allergies=["eggs"])
    page.set_viewport_size(PHONE)
    page.goto(live_server.url)

    expect(page.get_by_test_id("signup-link")).to_be_hidden()
    page.get_by_test_id("login-link").click()
    page.get_by_label("Username").fill("ada")
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")

    page.get_by_test_id("account-menu-toggle").click()
    page.get_by_test_id("my-allergies-link").click()
    page.wait_for_url("**/accounts/allergies/")
    expect(page.get_by_label("Eggs")).to_be_checked()
    page.get_by_label("Eggs").uncheck()
    page.get_by_label("Peanuts").check()
    page.get_by_role("button", name="Save allergies").click()

    expect(page.get_by_test_id("account-messages")).to_have_text("Your allergies are saved.")
    page.reload()
    expect(page.get_by_label("Peanuts")).to_be_checked()
    expect(page.get_by_label("Eggs")).not_to_be_checked()
    assert get_user_model().objects.get(username="ada").allergies == ["peanuts"]
    assert_page_is_fully_rendered(page)


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_account_pages_and_the_signed_in_header_meet_the_measurable_checks(
    live_server, page, assert_page_is_fully_rendered, scheme
):
    """Phone width: no overflow, one-row header, 44px targets, 4.5:1 text.

    Signed in with a long username, because the header has room for about
    ninety pixels of account control and a long name must not break the row.
    """
    page.set_viewport_size(PHONE)
    page.emulate_media(color_scheme=scheme)

    page.goto(f"{live_server.url}/accounts/login/")
    check_page(page, f"login, {scheme}", assert_page_is_fully_rendered)
    page.get_by_label("Username").fill("nobody")
    page.get_by_label("Password").fill("wrong")
    page.get_by_role("button", name="Log in").click()
    expect(page.locator(".errorlist").first).to_be_visible()
    check_page(page, f"login with errors, {scheme}", assert_page_is_fully_rendered)

    page.get_by_test_id("signup-from-login").click()
    page.wait_for_url("**/accounts/signup/**")
    check_page(page, f"sign-up, {scheme}", assert_page_is_fully_rendered)

    fill_sign_up(page, "a-customer-with-a-very-long-username")
    page.get_by_role("button", name="Create account").click()
    page.wait_for_url(f"{live_server.url}/")
    expect(page.get_by_test_id("account-menu-toggle")).to_be_visible()
    check_page(page, f"catalog signed in, {scheme}", assert_page_is_fully_rendered)

    page.get_by_test_id("account-menu-toggle").click()
    expect(page.get_by_test_id("logout-button")).to_be_visible()
    check_page(page, f"account menu open, {scheme}", assert_page_is_fully_rendered)

    page.get_by_test_id("my-allergies-link").click()
    page.wait_for_url("**/accounts/allergies/")
    check_page(page, f"my allergies, {scheme}", assert_page_is_fully_rendered)
