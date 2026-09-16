# Frontend Engineering Rules

Open this for frontend and UI work (components, styles, browser-facing state).

---

## Existing Design System

Before creating UI primitives, inspect the existing design system.

Reuse existing:

- buttons
- inputs
- modals
- dialogs
- cards
- tables
- menus
- typography
- layout primitives
- form components

Do not create duplicate primitives.

---

## Component Design

Keep components focused.

Prefer composition over giant components with many unrelated responsibilities.

Follow existing component boundaries.

Do not introduce a new component architecture for an isolated feature.

---

## State

Use the repository's existing state-management pattern.

Before introducing local/global state, determine:

- where the source of truth belongs
- whether the state can be derived
- whether server state already provides the value
- whether existing hooks/utilities solve the problem

Do not introduce a state-management dependency for a small isolated requirement.

---

## Data Fetching

Follow the existing data-fetching architecture.

Consider:

- loading
- success
- empty
- error
- retry
- stale data
- cancellation
- optimistic updates where relevant

Do not create ad-hoc fetch behavior when the application already has a standard mechanism.

---

## Accessibility

Preserve or improve:

- semantic HTML
- labels
- accessible names
- keyboard navigation
- focus behavior
- focus restoration
- error announcements
- disabled states
- appropriate ARIA usage

Do not use ARIA to compensate for avoidable semantic HTML problems.

---

## Responsive Behavior

For meaningful UI changes, consider:

- mobile
- tablet
- desktop
- long content
- empty states
- narrow containers
- keyboard interaction

Do not assume desktop-only behavior unless the product explicitly is desktop-only.

---

## UI Verification

After significant UI work:

1. run relevant tests — `python scripts/dev.py test:int`
2. run the full suite with coverage — `python scripts/dev.py test`
3. start the application — `python scripts/dev.py run`
4. inspect the actual rendered UI in a browser
5. test important interactions

There is no typecheck or build step in this repository. Do not report having run one. `python scripts/dev.py lint` does exist, but it tells you nothing about a page: pylint reads Python, and the UI here lives in templates, htmx attributes and Alpine directives it never parses. A green lint is not UI evidence.

CI (`.github/workflows/ci.yml`) runs the suite, lint and the ADR guards on push to `master`, `dev` and any `night-**` branch. Since `tests/e2e/` was filled and CI gained a `playwright install` step, that suite **does** include real-browser tests — but it still runs on GitHub, so it is never something you can observe or report from a local session. Say what you ran here; do not speak for CI.

**Step 4 is not optional here, and this repository has already paid for skipping it.** The add-to-cart button returned 403 in every real browser for two commits while the test suite stayed green, because `django.test.Client` does not enforce CSRF. A passing suite is not evidence that a page works.

Where a browser check finds something the suite missed, add the test that would have caught it — for that case, a client built with `enforce_csrf_checks=True`.

### Unattended: Playwright instead of your eyes

Steps 3-5 need a human looking at a page. When no human is available, the
substitute is a real browser driven by a test — **not** a waiver of step 4, and
not `django.test.Client`, which is the thing that let the 403 through.

`pytest-playwright` is already in `requirements.txt` (ADR 0006 unblocked it) and
the browser binaries are installed. `tests/e2e/` holds the catalog and detail
tests; follow their shape rather than inventing a second one.

Two things there are load-bearing and easy to lose. `tests/e2e/conftest.py` sets
`DJANGO_ALLOW_ASYNC_UNSAFE` — without it Playwright's event loop makes Django
refuse every database call in the test thread. And every browser test calls the
`assert_page_is_fully_rendered` fixture, because Django's `{# ... #}` comment is
single-line only: a multi-line one is printed to the page as text, and an
assertion on what you expect to see passes straight over it.

Use `pytest-django`'s `live_server` fixture. It starts a real server on a real
port for the test, so no separate `dev.py run` is needed and there is no stray
process to clean up:

```python
def test_add_to_cart(live_server, page):
    page.goto(f"{live_server.url}/")
    page.get_by_role("button", name="Add to cart").click()
    expect(page.get_by_test_id("cart-count")).to_have_text("1")
```

An unattended UI change is verified when an e2e test exercises the actual
interaction the change affects — the click, the form submit, the HTMX swap —
and passes. Asserting that a template renders is not that.

What this still does not catch: layout, spacing, contrast, and anything you would
only notice by looking. Say so in the completion report rather than implying the
UI was seen. If a change is primarily visual, it is a poor unattended task — log
it for supervised review instead.

---

## Visual Consistency

Match existing:

- spacing
- typography
- colors
- borders
- shadows
- interaction states
- motion
- responsive behavior

Do not invent a second design language.

---

## Performance

Avoid unnecessary:

- rerenders
- expensive computations
- network requests
- large client bundles
- event listeners
- DOM work

Do not optimize prematurely.

Measure or identify a concrete reason before introducing complex optimization.
