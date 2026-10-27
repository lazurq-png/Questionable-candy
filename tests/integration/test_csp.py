"""The site sends a report-only Content-Security-Policy (audit finding S2).

Report-only so a violation is logged in the browser console and nothing is
blocked; the policy is tightened against real pages before it is enforced.
These tests pin what must stay true meanwhile: the header is there, it is not
the enforcing one, and the one inline script carries the matching nonce.
"""
import re

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_pages_send_a_report_only_policy_and_no_enforcing_one(client):
    response = client.get(reverse("candy_list"))

    assert "Content-Security-Policy-Report-Only" in response.headers
    assert "Content-Security-Policy" not in response.headers


def test_the_policy_allows_only_the_origins_the_page_loads_from(client):
    policy = client.get(reverse("candy_list")).headers["Content-Security-Policy-Report-Only"]

    assert "default-src 'self'" in policy
    assert "https://unpkg.com" in policy
    assert "object-src 'none'" in policy
    assert "frame-ancestors 'none'" in policy


def test_the_inline_theme_script_carries_the_nonce_from_the_header(client):
    response = client.get(reverse("candy_list"))
    header_nonce = re.search(r"'nonce-([^']+)'", response.headers["Content-Security-Policy-Report-Only"])
    tag_nonce = re.search(r'<script nonce="([^"]+)">', response.content.decode())

    assert header_nonce and tag_nonce
    assert header_nonce.group(1) == tag_nonce.group(1)
