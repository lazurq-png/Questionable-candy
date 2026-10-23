"""Logging in and out, signing up, and "My allergies" (night-2026-09-17 plan T3).

Every client enforces CSRF and posts the token a real page handed out, as a
browser would; the default test client would pass even if every browser were
refused.
"""
import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from shop.models import Order

pytestmark = pytest.mark.django_db

PASSWORD = "candy-Shop-2026!"


@pytest.fixture(name="visitor")
def fixture_visitor():
    """A browser-like client: CSRF enforced, token taken from a real page."""
    client = Client(enforce_csrf_checks=True)
    client.get(reverse("candy_list"))
    client.token = client.cookies["csrftoken"].value
    return client


def post(client, url, data=None):
    """A plain form post carrying the page's CSRF token."""
    return client.post(url, {"csrfmiddlewaretoken": client.token, **(data or {})})


def make_user(username="ada", **fields):
    """A customer with the shared test password."""
    return get_user_model().objects.create_user(username=username, password=PASSWORD, **fields)


def log_in(client, username="ada"):
    """Log in as a browser would, then pick up the new CSRF token.

    Django rotates the token on login, so a page loaded before it holds a token
    that no longer matches; the browser gets the new one from the next page.
    """
    response = post(client, reverse("accounts:login"), {"username": username, "password": PASSWORD})
    assert response.status_code == 302
    client.get(response["Location"])
    client.token = client.cookies["csrftoken"].value


def signed_in_user(client):
    """Who the client's session belongs to, as the next request sees it."""
    return client.get(reverse("candy_list")).wsgi_request.user


# --- Log in ------------------------------------------------------------------

def test_logging_in_returns_to_the_page_named_by_next(visitor):
    """The header sends `next`; the customer lands back where they were."""
    make_user()

    response = post(visitor, reverse("accounts:login"),
                    {"username": "ada", "password": PASSWORD, "next": "/checkout/"})

    assert response.status_code == 302
    assert response["Location"] == "/checkout/"
    assert signed_in_user(visitor).username == "ada"


def test_logging_in_without_next_goes_to_the_catalog(visitor):
    """LOGIN_REDIRECT_URL is the catalog."""
    make_user()

    response = post(visitor, reverse("accounts:login"), {"username": "ada", "password": PASSWORD})

    assert response["Location"] == reverse("candy_list")


def test_a_wrong_password_is_refused_with_a_message(visitor):
    """The form says why, and nobody is signed in."""
    make_user()

    response = post(visitor, reverse("accounts:login"), {"username": "ada", "password": "wrong"})

    assert response.status_code == 200
    assert "Please enter a correct username and password" in response.content.decode()
    assert not signed_in_user(visitor).is_authenticated


def test_an_external_next_is_ignored_after_login(visitor):
    """An open redirect would let a crafted link send a customer to another site."""
    make_user()

    response = post(visitor, reverse("accounts:login"),
                    {"username": "ada", "password": PASSWORD, "next": "https://evil.example/"})

    assert response["Location"] == reverse("candy_list")


# --- Log out -----------------------------------------------------------------

def test_logging_out_takes_a_post(visitor):
    """The header's Log out form ends the session and returns to the catalog."""
    make_user()
    log_in(visitor)

    response = post(visitor, reverse("accounts:logout"))

    assert response.status_code == 302
    assert response["Location"] == reverse("candy_list")
    assert not signed_in_user(visitor).is_authenticated


def test_a_get_does_not_log_anyone_out(visitor):
    """A link, a prefetch or an image tag must not end a session."""
    make_user()
    log_in(visitor)

    response = visitor.get(reverse("accounts:logout"))

    assert response.status_code == 405
    assert signed_in_user(visitor).is_authenticated


# --- Sign up -----------------------------------------------------------------

def signup_data(**overrides):
    """A valid sign-up submission, with `overrides` applied."""
    data = {"username": "bea", "password1": PASSWORD, "password2": PASSWORD}
    data.update(overrides)
    return data


def test_signing_up_creates_the_account_logs_in_and_returns_to_next(visitor):
    """One step: the account exists, the customer is in, and back where they were."""
    response = post(visitor, reverse("accounts:signup"), signup_data(next="/shoppingcart/"))

    assert response.status_code == 302
    assert response["Location"] == "/shoppingcart/"
    user = get_user_model().objects.get(username="bea")
    assert user.check_password(PASSWORD)
    assert user.allergies == []
    assert signed_in_user(visitor).username == "bea"


def test_signing_up_records_the_allergies_ticked(visitor):
    """The optional allergy picker is saved with the account."""
    post(visitor, reverse("accounts:signup"), signup_data(allergies=["milk", "peanuts"]))

    assert sorted(get_user_model().objects.get(username="bea").allergies) == ["milk", "peanuts"]


def test_signing_up_with_an_allergy_outside_the_vocabulary_is_refused(visitor):
    """A crafted key outside the EU 14 creates no account."""
    response = post(visitor, reverse("accounts:signup"), signup_data(allergies=["lactose"]))

    assert response.status_code == 200
    assert not get_user_model().objects.filter(username="bea").exists()


def test_a_username_already_taken_is_refused_whatever_its_case(visitor):
    """'BEA' and 'bea' would be two accounts a person cannot tell apart."""
    make_user("bea")

    response = post(visitor, reverse("accounts:signup"), signup_data(username="BEA"))

    assert response.status_code == 200
    assert "A user with that username already exists." in response.content.decode()
    assert get_user_model().objects.count() == 1


def test_mismatched_or_weak_passwords_are_refused(visitor):
    """Django's password validators from settings apply to sign-up."""
    mismatched = post(visitor, reverse("accounts:signup"), signup_data(password2="something-else-2026"))
    weak = post(visitor, reverse("accounts:signup"), signup_data(password1="12345678", password2="12345678"))

    assert mismatched.status_code == 200
    assert weak.status_code == 200
    assert "This password is entirely numeric." in weak.content.decode()
    assert not get_user_model().objects.exists()


def test_an_external_next_is_ignored_after_sign_up(visitor):
    """Sign-up uses the same safe-redirect check as login."""
    response = post(visitor, reverse("accounts:signup"), signup_data(next="//evil.example/"))

    assert response["Location"] == reverse("candy_list")


# --- My profile --------------------------------------------------------------

def test_profile_requires_login(visitor):
    """Anonymous visitors are sent to log in, and back here afterwards."""
    response = visitor.get(reverse("accounts:profile"))

    assert response.status_code == 302
    assert response["Location"] == f'{reverse("accounts:login")}?next={reverse("accounts:profile")}'


def test_profile_changes_only_the_signed_in_customers_own_record(visitor):
    """No id in the URL or the form: another customer's record is unreachable."""
    ada = make_user("ada", allergies=["eggs"])
    bob = make_user("bob", allergies=["fish"])
    log_in(visitor)

    response = post(visitor, reverse("accounts:profile"), {"allergies": ["milk", "soy"]})

    assert response.status_code == 302
    ada.refresh_from_db()
    bob.refresh_from_db()
    assert sorted(ada.allergies) == ["milk", "soy"]
    assert bob.allergies == ["fish"]
    assert "Your profile was saved." in visitor.get(response["Location"]).content.decode()


def test_name_and_email_boxes_start_empty_with_hints(visitor):
    """What is saved is a hint; with nothing saved, first name hints the username."""
    make_user("ada", last_name="Lovelace", email="ada@example.com")
    log_in(visitor)

    page = visitor.get(reverse("accounts:profile")).content.decode()

    assert 'placeholder="ada"' in page
    assert 'placeholder="Lovelace"' in page
    assert 'placeholder="ada@example.com"' in page
    assert 'value="Lovelace"' not in page
    assert 'value="ada@example.com"' not in page


def test_saving_with_empty_boxes_keeps_what_is_saved(visitor):
    """An empty box means keep it; only a typed value replaces the saved one."""
    make_user("ada", first_name="Ada", last_name="Lovelace", email="ada@example.com")
    log_in(visitor)

    post(visitor, reverse("accounts:profile"), {"first_name": "", "last_name": "King", "email": ""})

    ada = get_user_model().objects.get(username="ada")
    assert (ada.first_name, ada.last_name, ada.email) == ("Ada", "King", "ada@example.com")


def test_unticking_every_allergy_saves_none(visitor):
    """A form with nothing ticked stores [], not the old list."""
    make_user("ada", allergies=["eggs"])
    log_in(visitor)

    post(visitor, reverse("accounts:profile"))

    assert get_user_model().objects.get(username="ada").allergies == []


def test_profile_refuses_a_key_outside_the_vocabulary(visitor):
    """A crafted key is refused and the stored allergies are kept."""
    make_user("ada", allergies=["eggs"])
    log_in(visitor)

    response = post(visitor, reverse("accounts:profile"), {"allergies": ["lactose"]})

    assert response.status_code == 200
    assert get_user_model().objects.get(username="ada").allergies == ["eggs"]


def test_account_posts_are_refused_without_a_csrf_token(visitor):
    """The account forms are protected like every other form."""
    make_user()

    response = visitor.post(reverse("accounts:login"), {"username": "ada", "password": PASSWORD})

    assert response.status_code == 403
    assert not signed_in_user(visitor).is_authenticated


# --- Change password ---------------------------------------------------------

def test_changing_the_password_returns_to_the_profile_with_a_message(visitor):
    """The new password works, the old one no longer does, and the customer stays in."""
    make_user()
    log_in(visitor)
    new_password = "fudge-Tray-2027!"

    response = post(visitor, reverse("accounts:password_change"), {
        "old_password": PASSWORD, "new_password1": new_password, "new_password2": new_password,
    })

    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:profile")
    assert "Your password was changed." in visitor.get(response["Location"]).content.decode()
    assert signed_in_user(visitor).is_authenticated
    ada = get_user_model().objects.get(username="ada")
    assert ada.check_password(new_password) and not ada.check_password(PASSWORD)


# --- My orders ---------------------------------------------------------------

def make_order(user, status=Order.Status.PENDING):
    """An order row as place() leaves it; the lines do not matter to this page."""
    return Order.objects.create(
        user=user, status=status, total_amount=Decimal("1.00"), confirmation_token=uuid.uuid4(),
    )


def test_orders_requires_login(visitor):
    """Anonymous visitors are sent to log in, and back here afterwards."""
    response = visitor.get(reverse("accounts:orders"))

    assert response.status_code == 302
    assert response["Location"] == f'{reverse("accounts:login")}?next={reverse("accounts:orders")}'


def test_orders_lists_only_the_signed_in_customers_own_newest_first(visitor):
    """Each order's "View order" button opens its receipt; its status and total show; nobody else's appear."""
    ada = make_user("ada")
    older = make_order(ada)
    newer = make_order(ada, Order.Status.CANCELLED)
    bobs = make_order(make_user("bob"))
    log_in(visitor)

    page = visitor.get(reverse("accounts:orders")).content.decode()

    def receipt_link(order):
        return f'href="{reverse("order_received", args=[order.pk])}"'

    assert page.index(receipt_link(newer)) < page.index(receipt_link(older))
    assert page.count('class="button button-secondary order-line-view">View order<') == 2
    assert "order-status-cancelled" in page and "Cancelled" in page
    assert "$1.00" in page
    assert receipt_link(bobs) not in page
    assert "Order #" not in page  # the button, not the order's number, names each row


def test_orders_says_so_when_there_are_none(visitor):
    """An empty state, not an empty list."""
    make_user()
    log_in(visitor)

    response = visitor.get(reverse("accounts:orders"))

    assert 'data-testid="no-orders"' in response.content.decode()
    assert 'data-testid="order-list"' not in response.content.decode()


def test_profile_no_longer_lists_orders(visitor):
    """They moved to their own page, reached from the account menu."""
    make_order(make_user())
    log_in(visitor)

    page = visitor.get(reverse("accounts:profile")).content.decode()

    assert 'data-testid="order-list"' not in page
    assert f'href="{reverse("accounts:orders")}"' in page  # the header's menu link


# --- The header ----------------------------------------------------------------

def test_the_header_offers_log_in_and_sign_up_with_the_current_page_as_next(visitor):
    """Logged out, both links carry the current page, query string included."""
    content = visitor.get("/shoppingcart/?from=header").content.decode()

    assert f'href="{reverse("accounts:login")}?next=/shoppingcart/%3Ffrom%3Dheader"' in content
    assert f'href="{reverse("accounts:signup")}?next=/shoppingcart/%3Ffrom%3Dheader"' in content


def test_the_header_on_an_account_page_does_not_send_next_back_to_it(visitor):
    """From the login page, `next` would return the customer to a form."""
    content = visitor.get(reverse("accounts:login")).content.decode()

    assert f'href="{reverse("accounts:signup")}" class="site-account site-signup"' in content


def test_the_header_names_a_signed_in_customer_and_offers_log_out(visitor):
    """Logged in, the username replaces Log in, with Log out as a form."""
    make_user("ada")
    log_in(visitor)

    content = visitor.get(reverse("candy_list")).content.decode()

    assert '<span class="site-account-name">ada</span>' in content
    assert f'action="{reverse("accounts:logout")}"' in content
    assert 'data-testid="login-link"' not in content


def test_sign_up_masks_the_passwords_and_is_never_cached(visitor):
    """As LoginView does: an error report must not carry a plain-text password."""
    page = visitor.get(reverse("accounts:signup"))
    response = post(visitor, reverse("accounts:signup"), signup_data())

    assert response.wsgi_request.sensitive_post_parameters == ("password1", "password2")
    assert "no-cache" in page["Cache-Control"]
