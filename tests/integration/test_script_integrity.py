"""The page runs no script from another site, and exactly the two it vendors.

ADR 0006 chose htmx and Alpine from a CDN, pinned by hash (night-2026-09-17
plan T10a). Since 2026-11-10 the same two files are served from
shop/static/shop/vendor/ instead, so the Content-Security-Policy names no
other origin. The hash stays on each tag: it now guards the committed file
against an edit or a line-ending conversion rather than against a CDN.
"""

import base64
import hashlib
import re

import pytest
from django.contrib.staticfiles import finders
from django.urls import reverse

pytestmark = pytest.mark.django_db

# Either quote style: a guard against an unrecorded script must not be escaped
# by writing the tag differently.
SCRIPT_WITH_SRC = re.compile(r"<script[^>]*\ssrc=[\"']?([^\"' >]+)[\"']?[^>]*>", re.IGNORECASE)
VENDORED = "/static/shop/vendor/"


def script_tags(client):
    """Every <script src> tag on a real page, as (tag, src), as a browser receives it."""
    page = client.get(reverse("candy_list")).content.decode()
    return [(match.group(0), match.group(1)) for match in SCRIPT_WITH_SRC.finditer(page)]


def test_no_script_is_loaded_from_another_site(client):
    """The policy would refuse one; this says so before a browser has to."""
    for _tag, src in script_tags(client):
        assert src.startswith("/static/"), src


def test_the_page_loads_exactly_the_two_scripts_adr_0006_chose(client):
    """A third would be a dependency nobody recorded."""
    vendored = [src for _tag, src in script_tags(client) if src.startswith(VENDORED)]

    assert len(vendored) == 2
    assert vendored[0].endswith("htmx-2.0.11.min.js")
    assert vendored[1].endswith("alpine-3.15.12.min.js")


def test_each_vendored_script_matches_the_hash_on_its_tag(client):
    """A file that differs from its hash is refused by the browser, silently."""
    vendored = [(tag, src) for tag, src in script_tags(client) if src.startswith(VENDORED)]
    assert vendored

    for tag, src in vendored:
        declared = re.search(r'integrity="sha384-([A-Za-z0-9+/]{64})"', tag)
        assert declared, tag
        with open(finders.find(src.removeprefix("/static/")), "rb") as file:
            actual = base64.b64encode(hashlib.sha384(file.read()).digest()).decode()
        assert declared.group(1) == actual, src
