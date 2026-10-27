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
        reverse(url), {"username": username, "password": password}, REMOTE_ADDR=address,
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
