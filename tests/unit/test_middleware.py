"""ADR 0002: Django's session authentication and CSRF middleware stay in place.

The ADR's confirmation section said nothing enforced this. These tests make the
stack a checked invariant: removing or reordering these entries fails the suite
rather than quietly disabling login, sessions (and so the cart) or CSRF.
"""
from django.conf import settings

SESSION = "django.contrib.sessions.middleware.SessionMiddleware"
CSRF = "django.middleware.csrf.CsrfViewMiddleware"
AUTH = "django.contrib.auth.middleware.AuthenticationMiddleware"
MESSAGES = "django.contrib.messages.middleware.MessageMiddleware"
CLICKJACKING = "django.middleware.clickjacking.XFrameOptionsMiddleware"
SECURITY = "django.middleware.security.SecurityMiddleware"


def test_the_middleware_adr_0002_chose_is_installed():
    """Sessions, authentication and CSRF -- plus the protections that ship with them."""
    for middleware in (SESSION, CSRF, AUTH, MESSAGES, CLICKJACKING, SECURITY):
        assert middleware in settings.MIDDLEWARE, f"{middleware} missing"


def test_sessions_come_before_what_depends_on_them():
    """Authentication and messages read the session; Django requires this order."""
    order = settings.MIDDLEWARE
    assert order.index(SESSION) < order.index(AUTH)
    assert order.index(SESSION) < order.index(MESSAGES)
