"""At most settings.SIGNUP_MAX_PER_DAY accounts a day from one address.

Login is throttled by django-axes; this is the same idea for sign-up, where a
script could otherwise create accounts without end. Counted in the database
(SignUpCount), not a cache: the site runs several workers, and each would keep
a count of its own.

The address is the one login throttling sees (mysite/client_ip.py behind a
proxy, REMOTE_ADDR otherwise). It is stored only as a keyed hash, and an IPv6
address is counted by its /64: one household has all of a /64, and could take
a new address for every sign-up.
"""

import ipaddress
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import salted_hmac

from mysite.client_ip import client_ip

from .models import SignUpCount

WINDOW = timedelta(days=1)


def _address(request: HttpRequest) -> str:
    if settings.CLIENT_IP_HEADER:
        return client_ip(request) or ""
    return request.META.get("REMOTE_ADDR", "")


def address_key(address: str) -> str:
    """What an address is counted under: a keyed hash of it, or of its /64."""
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        block = "unknown"
    else:
        mapped = getattr(parsed, "ipv4_mapped", None)
        if mapped is not None:
            block = str(mapped)
        elif parsed.version == 6:
            block = str(ipaddress.ip_network(f"{parsed}/64", strict=False))
        else:
            block = str(parsed)
    return salted_hmac("accounts.signup_limit", block, algorithm="sha256").hexdigest()


def claim_sign_up(request: HttpRequest) -> bool:
    """Count one sign-up for the request's address; False once it is over the limit.

    The row is locked while it is counted, so sign-ups sent at once each get a
    number of their own and cannot all fit under the limit. Rows whose day has
    passed are deleted on the way, so the table holds one day of addresses.
    """
    now = timezone.now()
    key = address_key(_address(request))
    with transaction.atomic():
        SignUpCount.objects.filter(window_start__lte=now - WINDOW).delete()
        counted, _ = SignUpCount.objects.select_for_update().get_or_create(
            key=key, defaults={"count": 0, "window_start": now}
        )
        counted.count += 1
        counted.save(update_fields=["count"])
    return counted.count <= settings.SIGNUP_MAX_PER_DAY
