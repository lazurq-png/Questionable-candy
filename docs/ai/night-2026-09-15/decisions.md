# Decisions — night-2026-09-15

Choices with consequences, and the options that lost. Obvious choices are
omitted.

## D1. `DJANGO_ALLOW_ASYNC_UNSAFE` is set at conftest import, not in a fixture

**Context.** The first e2e run failed at setup, before any test body:

```
django.core.exceptions.SynchronousOnlyOperation:
    You cannot call this from an async context - use a thread or sync_to_async
```

raised from `_nodb_cursor` — the creation of the test database. Playwright's
"sync" API drives a greenlet over an asyncio event loop that stays running in
the main thread, and Django's `@async_unsafe` decorator refuses database access
from a thread with a live loop.

**Options.**

- (a) Set `DJANGO_ALLOW_ASYNC_UNSAFE` at `tests/e2e/conftest.py` import time.
- (b) Set it from an autouse fixture scoped to `tests/e2e/`.
- (c) Restructure so database work happens off the loop-bearing thread.

**Chosen: (a).** (b) cannot work: the first thing to trip the guard is the
*session-scoped* creation of the test database, which happens during fixture
setup, so no function-scoped fixture can wrap it. (c) means reimplementing what
`live_server` already does.

**Consequence, stated plainly.** Because pytest imports every collected conftest
during collection, the variable is set for the whole session, including the unit
and integration suites. That is harmless today — `async_unsafe` only raises when
an event loop is running in the calling thread, and nothing outside `tests/e2e/`
starts one — but it is a genuinely wider blast radius than it looks, and it will
stop being harmless the day this repository gains async tests. Written up in
`tests/e2e/conftest.py`'s docstring so it is found there rather than here.

The guard protects against blocking an event loop that is serving other work.
Playwright's loop is serving only this test, and blocking it is how the sync API
is designed to work, so the condition does not arise.

## D2. Multi-line `{# ... #}` comments were rendering to the page

Found by the `reviewer` subagent, then confirmed directly: Django compiles
`tag_re` in `django/template/base.py` without `re.DOTALL`, so `{# ... #}` is
**single-line only**. A comment that wraps is not recognised as a tag and is
emitted as page text.

This run introduced one in `candy_list.html` — on the empty-state branch, whose
whole purpose is that the page not look broken. `templates/base.html` has had
one since `2935aac`, so the site has been printing four lines of its own source
above `<body>` on **every page**.

Both are now `{% comment %}`. `base.html` was not part of this task; it is
fixed here because these are the first tests in the repository's history to look
at a rendered page, and shipping them while walking past the defect they exist
to catch would be the wrong trade.

The real fix is the test, not the template: `assert_page_is_fully_rendered` in
`tests/e2e/conftest.py`, called by every browser test. The original assertions
all passed with the junk on screen, because they asserted that what should be
there *was* there and never that nothing else was.

## D3. CI gained a `playwright install` step

Also from the reviewer. `pip install -r requirements.txt` installs
`pytest-playwright`; it does not install a browser, and the runner image has
none. This was invisible while `tests/e2e/` was empty — no test, no `browser`
fixture, no launch — and this commit is what puts it on the critical path.

Not verifiable from here: CI runs on GitHub (`CLAUDE.md` §9), and PyYAML is not
installed, so the workflow file was checked by eye against the indentation of
the steps around it, not parsed. **The first push is the test of D3.**
