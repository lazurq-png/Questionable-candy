"""One address can make only so many accounts a day (audit 2026-11-10, S2).

Logins were throttled and sign-ups were not, so a script could create accounts
without end. The count is per address, kept under a keyed hash, and only a
form that would have made an account is counted.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from accounts.models import SignUpCount
from accounts.signup_limit import address_key

pytestmark = pytest.mark.django_db

PASSWORD = "candy-Shop-2026!"


def sign_up(client, username, address="10.0.0.1", **headers):
    return client.post(
        reverse("accounts:signup"),
        {"username": username, "password1": PASSWORD, "password2": PASSWORD},
        REMOTE_ADDR=address,
        **headers,
    )


def usernames():
    return set(get_user_model().objects.values_list("username", flat=True))


def test_sign_ups_past_the_limit_are_refused_and_make_no_account(client, settings):
    settings.SIGNUP_MAX_PER_DAY = 2
    assert sign_up(client, "one").status_code == 302
    client.logout()
    assert sign_up(client, "two").status_code == 302
    client.logout()

    response = sign_up(client, "three")

    assert response.status_code == 429
    assert "Too many accounts were created from here today" in response.content.decode()
    assert usernames() == {"one", "two"}
    assert "_auth_user_id" not in client.session


def test_another_address_has_a_count_of_its_own(client, settings):
    settings.SIGNUP_MAX_PER_DAY = 1
    sign_up(client, "one", address="10.0.0.1")
    client.logout()

    assert sign_up(client, "two", address="10.0.0.2").status_code == 302


def test_a_form_that_makes_no_account_is_not_counted(client, settings):
    """Mistyping the second password must not use up the day's sign-ups."""
    settings.SIGNUP_MAX_PER_DAY = 1
    for _ in range(3):
        response = client.post(
            reverse("accounts:signup"),
            {"username": "ada", "password1": PASSWORD, "password2": "something-else-2026"},
            REMOTE_ADDR="10.0.0.1",
        )
        assert response.status_code == 200

    assert sign_up(client, "ada").status_code == 302


def test_the_count_starts_again_after_a_day(client, settings):
    settings.SIGNUP_MAX_PER_DAY = 1
    sign_up(client, "one")
    client.logout()
    SignUpCount.objects.update(window_start=timezone.now() - timedelta(days=1, minutes=1))

    assert sign_up(client, "two").status_code == 302
    assert SignUpCount.objects.get().count == 1


def test_behind_a_proxy_the_visitors_own_address_is_counted(client, settings):
    """REMOTE_ADDR is then the proxy's, the same for everyone."""
    settings.SIGNUP_MAX_PER_DAY = 1
    settings.CLIENT_IP_HEADER = "CF-Connecting-IP"
    sign_up(client, "one", HTTP_CF_CONNECTING_IP="203.0.113.7")
    client.logout()

    assert sign_up(client, "two", HTTP_CF_CONNECTING_IP="203.0.113.8").status_code == 302
    client.logout()
    assert sign_up(client, "three", HTTP_CF_CONNECTING_IP="203.0.113.7").status_code == 429


def test_the_address_itself_is_never_stored(client):
    sign_up(client, "one", address="10.0.0.1")

    key = SignUpCount.objects.get().key
    assert "10.0.0.1" not in key
    assert key == address_key("10.0.0.1")


def test_an_ipv6_address_is_counted_by_its_64():
    """One household holds a whole /64, and could use a new address each time."""
    assert address_key("2001:db8:1:2::1") == address_key("2001:db8:1:2:ffff::9")
    assert address_key("2001:db8:1:2::1") != address_key("2001:db8:1:3::1")
    assert address_key("::ffff:10.0.0.1") == address_key("10.0.0.1")
    assert address_key("not an address") == address_key("")
