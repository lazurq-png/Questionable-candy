"""Fixtures shared by every suite."""

import pytest


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    """Hash passwords with MD5 in tests.

    Django's default hasher is slow on purpose, which is right for production
    and costs seconds per login in a suite that logs in constantly. Nothing
    here asserts on the hash algorithm: tests only create users and call
    check_password, which work with any configured hasher. This never touches
    mysite/settings.py, so production keeps the default.
    """
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def _allow_async_unsafe(monkeypatch):
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "1")


@pytest.fixture
def transactional_db(_allow_async_unsafe, transactional_db):  # pylint: disable=redefined-outer-name
    """``transactional_db``, with Django's async-safety guard lifted for its lifetime.

    Playwright's sync API keeps an asyncio loop running in the main thread for
    the rest of the session once a browser test has run, and Django refuses
    database calls from a thread with a running loop; tests/e2e/conftest.py
    explains why the opt-out is right there. Every browser test gets this,
    because ``live_server`` requests ``transactional_db`` by name
    (pytest_django/fixtures.py:660), and so does an integration test that
    names it (tests/integration/test_order_admin_race.py). The argument order
    is load-bearing: the variable is set before the original's setup and
    removed only after its teardown flush. A ``django_db`` mark bypasses this
    override -- pytest-django then sets the database up from an autouse fixture
    -- so a test that needs it names ``transactional_db`` and carries no mark.
    """
    return transactional_db
