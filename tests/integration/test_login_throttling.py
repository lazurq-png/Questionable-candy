"""Repeated wrong passwords lock a login out for a while (audit finding S3).

Locking is per username *and* address, so an attacker elsewhere cannot lock a
customer out, and one customer's typos do not affect another.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db

LIMIT = 5  # settings.AXES_FAILURE_LIMIT


@pytest.fixture(name="ada")
def fixture_ada():
    return get_user_model().objects.create_user(username="ada", password="right-password-1")


def attempt(client, username, password, url="accounts:login", address="10.0.0.1"):
    return client.post(
        reverse(url),
        {"username": username, "password": password},
        REMOTE_ADDR=address,
    )


def test_the_limit_comes_from_settings(settings):
    assert settings.AXES_FAILURE_LIMIT == LIMIT


def test_too_many_wrong_passwords_lock_the_login_even_for_the_right_one(client, ada):
    for _ in range(LIMIT - 1):
        assert attempt(client, "ada", "wrong").status_code == 200
    assert attempt(client, "ada", "wrong").status_code == 429  # the failure that trips it

    response = attempt(client, "ada", "right-password-1")

    assert response.status_code == 429
    assert "_auth_user_id" not in client.session


def test_fewer_failures_than_the_limit_do_not_lock(client, ada):
    for _ in range(LIMIT - 1):
        attempt(client, "ada", "wrong")

    assert attempt(client, "ada", "right-password-1").status_code == 302


def test_a_lock_on_one_user_does_not_affect_another_user(client, ada):
    get_user_model().objects.create_user(username="grace", password="right-password-2")
    for _ in range(LIMIT):
        attempt(client, "ada", "wrong")

    assert attempt(client, "grace", "right-password-2").status_code == 302


def test_a_lock_does_not_follow_the_username_to_another_address(client, ada):
    for _ in range(LIMIT):
        attempt(client, "ada", "wrong", address="10.0.0.1")

    assert attempt(client, "ada", "right-password-1", address="10.0.0.2").status_code == 302


def test_the_admin_login_is_throttled_too(client):
    get_user_model().objects.create_superuser(username="boss", password="right-password-3")
    for _ in range(LIMIT):
        attempt(client, "boss", "wrong", url="admin:login")

    assert attempt(client, "boss", "right-password-3", url="admin:login").status_code == 429


# --- Behind a proxy (DJANGO_CLIENT_IP_HEADER) -----------------------------------
#
# On Render every request arrives from the proxy, so REMOTE_ADDR is the same for
# all visitors; CF-Connecting-IP carries each one's own address.

PROXY = "10.9.9.9"


@pytest.fixture(name="behind_render")
def fixture_behind_render(settings):
    """settings.py as DJANGO_CLIENT_IP_HEADER=CF-Connecting-IP leaves it."""
    settings.CLIENT_IP_HEADER = "CF-Connecting-IP"
    settings.AXES_CLIENT_IP_CALLABLE = "mysite.client_ip.client_ip"


def through_proxy(client, username, password, visitor):
    return client.post(
        reverse("accounts:login"),
        {"username": username, "password": password},
        REMOTE_ADDR=PROXY,
        HTTP_CF_CONNECTING_IP=visitor,
    )


def test_behind_the_proxy_one_visitors_failures_do_not_lock_out_another(client, ada, behind_render):
    """Without the header every visitor shares the proxy's address -- and its lock."""
    for _ in range(LIMIT):
        through_proxy(client, "ada", "wrong", visitor="198.51.100.7")

    assert through_proxy(client, "ada", "right-password-1", visitor="198.51.100.7").status_code == 429
    assert through_proxy(client, "ada", "right-password-1", visitor="203.0.113.4").status_code == 302


def test_without_the_setting_a_forged_header_is_ignored(client, ada):
    """With no proxy configured, anyone could send CF-Connecting-IP themselves."""
    for visitor in ("198.51.100.1", "198.51.100.2", "198.51.100.3", "198.51.100.4", "198.51.100.5"):
        through_proxy(client, "ada", "wrong", visitor=visitor)

    assert through_proxy(client, "ada", "right-password-1", visitor="198.51.100.6").status_code == 429
