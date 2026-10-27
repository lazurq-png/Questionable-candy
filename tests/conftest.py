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
