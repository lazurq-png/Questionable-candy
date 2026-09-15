"""Configuration shared by the browser tests.

Playwright's *synchronous* API is not really synchronous: it drives a greenlet
over an asyncio event loop that stays running in the main thread for as long as
any Playwright fixture is alive. Django notices that loop and refuses every
database call from that thread -- `@async_unsafe` raises SynchronousOnlyOperation
-- so without the setting below, an e2e test fails before it reaches its body:

    django.core.exceptions.SynchronousOnlyOperation:
        You cannot call this from an async context - use a thread or sync_to_async

The guard exists to stop blocking code from stalling an event loop that is
serving other work. Here the loop belongs to Playwright, blocking it is how the
sync API is designed to work, and nothing else is being served -- so the
condition the guard protects against does not arise, and Django's documented
opt-out is the correct answer rather than a workaround.

Set at import time rather than in a fixture because the first thing to trip the
guard is the *session-scoped* creation of the test database, which happens
during fixture setup and cannot be wrapped from here. It reaches the whole test
session as a result, which is harmless: the guard only fires when an event loop
is running in the calling thread, and no suite outside tests/e2e/ starts one.
"""
import os

import pytest

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")


@pytest.fixture
def assert_page_is_fully_rendered():
    """Assert no template source survived into the page's visible text.

    Django's ``{# ... #}`` comment is single-line only -- ``tag_re`` in
    ``django/template/base.py`` is compiled without ``re.DOTALL`` -- so a
    comment that wraps onto a second line is not recognised as a tag and is
    emitted verbatim as page content. Nothing else catches it: the template
    still compiles, the view still returns 200, and an assertion on the text
    you *expect* still passes, because the junk sits alongside it rather than
    replacing it.

    A stray ``{{ candy.nmae }}`` renders as the empty string rather than as
    source, so this will not catch every template mistake -- only the class
    that reaches the user as literal syntax. That class shipped on every page
    of this site until the first browser test looked.

    Checks visible text via ``inner_text`` rather than the HTML, so the
    ``hx-headers`` attribute's JSON braces are not mistaken for a template tag.
    """
    def check(page):
        body = page.locator("body").inner_text()
        for marker in ("{#", "{%", "{{"):
            assert marker not in body, (
                f"unrendered template syntax {marker!r} is visible on "
                f"{page.url} -- the page is showing its own source:\n{body}"
            )

    return check
