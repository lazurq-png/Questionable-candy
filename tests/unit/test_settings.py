"""Settings that must hold for a deployment, checked without deploying.

docs/requirements.md section 3 requires session cookies to be secure and
HTTPS-only. Nothing else enforces that: `manage.py check --deploy` reports it
only as a WARNING, and `manage.py check` -- which `dev validate` runs -- exits 0
on warnings, so a stage built on it would pass without checking anything.

These tests import mysite/settings.py under a controlled environment instead, so
hardcoding either flag to False breaks the suite.
"""
import importlib.util
import os
from contextlib import nullcontext
from pathlib import Path
from unittest import mock

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "mysite" / "settings.py"


def load_settings(*, without=(), **env):
    """Import settings.py fresh under `env`, and return it as a module.

    Loaded under a throwaway module name so the django.conf.settings already
    configured for this test run is left alone.

    `without` names variables to remove instead of supplying -- for testing what
    settings.py does when one is missing. Removing one also stubs out
    `load_dotenv`, since otherwise the `.env` on a developer's machine would put
    it straight back.

    DJANGO_SECRET_KEY and DATABASE_URL are supplied because settings.py raises
    ImproperlyConfigured without them; passing them here keeps the test from
    depending on the developer having a .env. DJANGO_SECURE_COOKIES is removed
    for the opposite reason: load_dotenv does not override variables already in
    os.environ, but it does import ones that are absent, so a developer with
    that key in their .env would otherwise be testing their machine rather than
    the DEBUG-derived default.
    """
    missing = (without,) if isinstance(without, str) else tuple(without)
    environment = {
        "DJANGO_SECRET_KEY": "not-a-real-key-" + "x" * 40,
        "DATABASE_URL": "postgresql://user@localhost:5432/example",
        **env,
    }
    for name in missing:
        environment.pop(name, None)

    with mock.patch.dict(os.environ, environment, clear=False):
        if "DJANGO_SECURE_COOKIES" not in env:
            os.environ.pop("DJANGO_SECURE_COOKIES", None)
        for name in missing:
            os.environ.pop(name, None)

        spec = importlib.util.spec_from_file_location("_settings_probe", SETTINGS_PATH)
        module = importlib.util.module_from_spec(spec)
        with mock.patch("dotenv.load_dotenv", return_value=False) if missing else nullcontext():
            spec.loader.exec_module(module)

    return module


def test_cookies_are_secure_when_debug_is_off():
    """Turning DEBUG off must secure the cookies without a second setting."""
    settings = load_settings(DJANGO_DEBUG="False")

    assert settings.SESSION_COOKIE_SECURE is True
    assert settings.CSRF_COOKIE_SECURE is True


def test_cookies_are_usable_over_http_in_development():
    """Local development is plain HTTP; secure cookies would never be sent."""
    settings = load_settings(DJANGO_DEBUG="True")

    assert settings.SESSION_COOKIE_SECURE is False
    assert settings.CSRF_COOKIE_SECURE is False


def test_the_override_can_force_insecure_cookies_with_debug_off():
    """A staging box behind plain HTTP is the only reason this override exists."""
    settings = load_settings(DJANGO_DEBUG="False", DJANGO_SECURE_COOKIES="False")

    assert settings.SESSION_COOKIE_SECURE is False
