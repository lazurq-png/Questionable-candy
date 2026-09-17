"""Every script loaded from another site carries a hash (night-2026-09-17 plan T10a).

ADR 0006 chose htmx and Alpine from a CDN and recorded the gap this closes: the
tags named a version but nothing checked what came back.
"""
import re

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

# Either quote style: a guard against an unrecorded script must not be escaped
# by writing the tag differently.
EXTERNAL_SCRIPT = re.compile(r"<script[^>]*\ssrc=[\"']?(https?://[^\"' >]+)[\"']?[^>]*>", re.IGNORECASE)


def script_tags(client):
    """Every external <script> tag on a real page, as a browser receives it."""
    page = client.get(reverse("candy_list")).content.decode()
    return [match.group(0) for match in EXTERNAL_SCRIPT.finditer(page)]


def test_the_page_loads_exactly_the_two_scripts_adr_0006_chose(client):
    """A third would be a dependency nobody recorded."""
    tags = script_tags(client)

    assert len(tags) == 2
    assert "htmx.org@2.0.3" in tags[0]
    assert "alpinejs@3.14.1" in tags[1]


def test_every_external_script_is_pinned_by_hash(client):
    """Without integrity, a swapped CDN response would run with the page's rights."""
    for tag in script_tags(client):
        assert re.search(r'integrity="sha384-[A-Za-z0-9+/]{64}"', tag), tag
        assert 'crossorigin="anonymous"' in tag, tag


def test_each_script_url_names_one_file_not_a_package(client):
    """A bare package URL redirects, and a redirect target can change under the hash."""
    for tag in script_tags(client):
        url = EXTERNAL_SCRIPT.search(tag).group(1)
        assert url.endswith(".js"), url
