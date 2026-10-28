"""The visitor's IP address, for django-axes (settings: AXES_CLIENT_IP_CALLABLE)."""

from django.conf import settings
from django.http import HttpRequest


def client_ip(request: HttpRequest) -> str | None:
    """The address in DJANGO_CLIENT_IP_HEADER, else REMOTE_ADDR.

    Only wired up when that header is configured, i.e. behind a proxy that
    overwrites it on every request (settings.py, "Login throttling"). A request
    without it -- one that did not come through that proxy -- falls back to the
    address the connection came from.
    """
    meta_key = "HTTP_" + settings.CLIENT_IP_HEADER.upper().replace("-", "_")
    return request.META.get(meta_key) or request.META.get("REMOTE_ADDR")
