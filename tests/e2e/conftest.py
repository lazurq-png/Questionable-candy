"""Configuration shared by the browser tests.

Playwright's *synchronous* API is not really synchronous: it drives a greenlet
over an asyncio event loop that stays running in the main thread for as long as
the session-scoped ``playwright`` fixture is alive. Django notices that loop and
refuses every database call from that thread -- ``@async_unsafe`` raises

    django.core.exceptions.SynchronousOnlyOperation:
        You cannot call this from an async context - use a thread or sync_to_async

The guard exists to stop blocking code from stalling an event loop that is
serving other work. Playwright's loop serves only the test, and blocking it is
how the sync API is designed to work, so Django's documented opt-out,
``DJANGO_ALLOW_ASYNC_UNSAFE``, is correct here -- but only here. It is set by
the two fixtures below, for exactly the stretch of each e2e test that touches
the database with the loop running, and is unset again afterwards so the guard
stays armed for every other suite, async tests included.

Two separate fixtures, because the database work falls into two lifetimes:

* The test database is created and destroyed once per session.
  ``django_db_setup`` is session-scoped but *lazy*: ``live_server`` pulls it in
  from a function-scoped autouse fixture, after ``playwright`` has already
  started its loop -- which is where the original failure came from.
  ``_test_database_before_browser`` requests it up front instead, so creation
  happens before the loop exists and, by fixture teardown order, destruction
  after it has stopped. No opt-out is needed for either.

* Each test's own database work -- factories in the test body, and the flush
  ``transactional_db`` runs on teardown -- happens with the loop running. The
  ``transactional_db`` override lists ``_allow_async_unsafe`` *before* the
  original, so the variable is set before the original's setup and, fixtures
  being torn down in reverse, removed only after its flush.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def _test_database_before_browser(django_db_setup):  # pylint: disable=unused-argument
    """Create the test database before Playwright's loop starts.

    Session-scoped autouse fixtures are set up before the session fixtures a
    test merely names, so this runs ahead of ``playwright``. Without it, running
    ``tests/e2e`` on its own still *passes* -- creation happens inside
    ``transactional_db``'s opt-out -- but destroying the database at session end
    runs with the loop alive and the variable gone. pytest-django reports that
    as a mere warning and leaves the test database behind.
    """


@pytest.fixture
def _allow_async_unsafe(monkeypatch):
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "1")


@pytest.fixture
def transactional_db(_allow_async_unsafe, transactional_db):  # pylint: disable=redefined-outer-name
    """``transactional_db``, with the async-safety guard lifted for its lifetime.

    Every browser test gets this: ``live_server`` requests ``transactional_db``
    by name (pytest_django/fixtures.py:660) and resolves to this override. The
    argument order is load-bearing -- see the module docstring.
    """
    return transactional_db


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
