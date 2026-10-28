"""The site enforces a Content-Security-Policy (audit finding S2).

It was report-only until a click-through left the console clean
(2026-10-27). These tests pin what must stay true: the enforcing header is
there and the report-only one is gone, the policy names only the origins the
page loads from, the one inline script carries the matching nonce, and the
500 page, which has no request to take a nonce from, has no inline script.
"""

import re

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_pages_send_an_enforcing_policy_and_no_report_only_one(client):
    response = client.get(reverse("candy_list"))

    assert "Content-Security-Policy" in response.headers
    assert "Content-Security-Policy-Report-Only" not in response.headers


def test_the_policy_allows_only_the_origins_the_page_loads_from(client):
    policy = client.get(reverse("candy_list")).headers["Content-Security-Policy"]

    assert "default-src 'self'" in policy
    assert "https://unpkg.com" in policy
    assert "object-src 'none'" in policy
    assert "frame-ancestors 'none'" in policy


def test_the_inline_theme_script_carries_the_nonce_from_the_header(client):
    response = client.get(reverse("candy_list"))
    header_nonce = re.search(r"'nonce-([^']+)'", response.headers["Content-Security-Policy"])
    tag_nonce = re.search(r'<script nonce="([^"]+)">', response.content.decode())

    assert header_nonce and tag_nonce
    assert header_nonce.group(1) == tag_nonce.group(1)


@pytest.mark.urls("tests.integration.error_urls")
def test_the_500_page_is_enforced_and_has_no_inline_script(settings):
    settings.DEBUG = False
    response = Client(raise_request_exception=False).get("/boom/")

    assert response.status_code == 500
    assert "Content-Security-Policy" in response.headers
    assert not re.search(r"<script(?![^>]*\ssrc=)[^>]*>", response.content.decode())
