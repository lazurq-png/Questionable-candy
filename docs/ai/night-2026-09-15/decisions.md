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

**Revised 2026-09-16 (supervised): (a) replaced by a fixture-scoped opt-out.**
The reason for rejecting (b) was wrong. `django_db_setup` is session-scoped but
*lazy*: `live_server`'s function-scoped `_live_server_helper` pulls it in
(pytest_django/fixtures.py:660), after the session-scoped `playwright` fixture
has already started its loop. The failure was a fixture-*ordering* problem, not
proof that the work can't be wrapped. `tests/e2e/conftest.py` now:

- requests `django_db_setup` from a session-scoped autouse fixture, so the
  database is created before the loop starts and destroyed after it stops;
- overrides `transactional_db` to set the variable (via `monkeypatch`) for its
  lifetime, covering factories in the test body and the teardown flush.

Checked with a probe plugin, running `tests/e2e tests/unit tests/integration`
in that order: the variable was `'1'` during all 7 e2e tests, `None` during all
24 unit and integration tests, and `None` at session end. Removing each fixture
in turn: without the setenv, 7 failed and 7 errored with
`SynchronousOnlyOperation`; without the ordering fixture the run still passed,
but pytest-django warned that it could not tear down the test database. That
failure mode is silent enough to be recorded in the fixture's docstring.

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

**Update 2026-09-16 (supervised):** `actionlint` 1.7.12 (release binary,
checksum verified, not added to the repo) reports 0 errors on `ci.yml`. It
flagged a deliberately broken copy (`run:` → `runs:` on this step), so the clean
result is not vacuous. Its `shellcheck` and `pyflakes` rules were skipped
because neither tool was installed, so the shell inside `run:` blocks was not
checked. (Both are now installed and enforced; see D10.) The workflow's
syntax and schema are now verified. Whether `playwright install --with-deps`
succeeds on the runner is still only testable by pushing.

## D4. `description` is not null but not mandatory

Added as `TextField(blank=True, default="")`. `docs/data-model.md` §3.4 specifies
`description` as "not null", which a `TextField` without `null=True` already is;
`blank=True` makes it non-mandatory at the form level.

`default=""` is load-bearing rather than decorative: without a default, adding a
non-nullable field to a table with rows makes `makemigrations` **prompt
interactively** for what to do about them — which in an unattended run is a
hang, not a question. With it, the migration is a metadata-only `AddField` on
PostgreSQL, with no table rewrite and no backfill.

Not mandatory because UC-06 singles out `flaw` as the field that may never be
omitted, and says so at the data-model level. Holding `description` to the same
bar would be a constraint nobody specified, and tightening it later is one
migration.

## D5. The initial add-to-cart button became a shared partial

The detail page needs the same button the catalog has. `cart_button.html`
could not be reused — despite the name it is the *response* to the hx-post, the
disabled "Added!" state, not the button in its initial state.

Options: duplicate the three lines into `candy_detail.html`, or extract the
initial state into `partials/add_to_cart_button.html` and include it from both.

**Chosen: extract.** The two copies would have to keep the same URL name, the
same `hx-swap` target and the same `type="button"` as `cart_button.html`, and
nothing would notice if one drifted. It is deduplication of markup with two
call sites, not a new abstraction — `.claude/rules/frontend.md` says not to
create duplicate primitives, which is this case exactly.

`cart_button.html` was deliberately **not** renamed to match, even though the
pairing would read better as `add_to_cart_button` / `added_to_cart_button`. A
rename is a delete of a file this run did not create, which `night-run` §3
forbids. The relationship is documented in both files instead.

## D6. A test that could not fail

The reviewer found `assert reverse("candy_list").encode() in response.content`
in `test_candy_detail_offers_both_ways_out`. The catalog is mounted at `""`, so
`reverse("candy_list")` is `"/"` — confirmed in a Django shell — and the
assertion reduces to `b"/" in response.content`, which `</html>` alone
satisfies. Deleting the back-link from the template left it green.

Now asserted as `href="/"`, which the rendered page contains exactly once. The
browser test `test_the_detail_page_returns_to_the_catalog` was covering the
actual click throughout, so nothing was ever unverified — but the integration
test claimed a guard it did not provide, and the idiom was sitting in the file
to be copied to the next root-mounted route.

## D7. The flaw is labelled, and sits above the add-to-cart button

UC-06 step 3 says the flaw "renders alongside the description". Rendered as an
unlabelled paragraph it would be indistinguishable from the sales copy, and a
disclosure the reader cannot identify as one has not disclosed anything — so it
is a `<section data-testid="candy-flaw">` with a "Known flaw" heading.

Placed *before* the add-to-cart button rather than after it. UC-06's success
guarantee is that every detail view shows a flaw; a flaw below the button is
one the customer can act without ever reaching. No styling was added (stated
non-goal), so this is document order doing the work.

## D8. `\S`, not `!= ""`

The constraint is `Q(flaw__regex=r"\S")` — at least one non-whitespace
character — rather than `~Q(flaw="")`.

Not extra strictness. Django's form field strips whitespace before testing
`blank`, so a submitted `"   "` is already rejected at the form. With
`~Q(flaw="")` the database would have been the *more permissive* of the two,
and "has a flaw" would mean two different things depending on the write path.
Verified by the reviewer against PostgreSQL that `~ '\S'` treats `\xa0` and
` ` the same way Python's `str.strip()` does, so the two agree on the
unicode edges as well.

`violation_error_message` is set because a constraint is not attached to a
field: the error surfaces under `__all__`, and without the message the user
would be shown Django's generic text naming a constraint they have never heard
of.

## D9. Migration `0003` was left without an in-file guard — see `questions.md` Q5

The reviewer's Finding 1 is correct: `AddConstraint` validates against existing
rows, and a database holding a blank-flaw row will abort `migrate` with a
Postgres error that names nothing. The fix is a `RunPython` guard inside the
migration.

`night-run` §3 forbids editing an existing migration file. The file is one this
run generated and has not yet committed, so the rule's *intent* — do not
rewrite schema history — plausibly does not reach it. Deciding that on my own
is the kind of judgement the rule exists to take away from an unattended run,
so the diff is written out verbatim in `questions.md` Q5 for approval instead,
and the precondition plus its triage query went into `docs/data-model.md` §3.4.

That informs a reader. It does not stop a deployment. **This is the most
consequential thing left undone in this run.**

## D10. Workflow lint is a local verification gate, not a CI job (supervised, 2026-09-16)

**Context.** D3's `ci.yml` change could only be checked by eye. actionlint then
checked it (see D3's update), but with its shellcheck and pyflakes rules
disabled because neither tool was installed.

**Decision.** `python scripts/dev.py lint:workflows` runs actionlint 1.7.12 with
shellcheck 0.11.0 and pyflakes 3.4.0, all installed under
`%USERPROFILE%\Binaries\` (the two release zips checksum-verified; pyflakes in
its own venv). It is part of the verification that must pass before a task is
done, **when it applies**: `CLAUDE.md` §9 and night-run §2 step 1.

- **Always resolved and passed explicitly, never left to actionlint.** Given a
  missing `shellcheck` or `pyflakes`, actionlint disables that rule and still
  exits 0. The task exits 2 instead, so a clean result always means all three
  checks ran. Unattended, a missing tool abandons the task that needed it,
  because installing software is forbidden (night-run §3).
- **Not folded into `lint`.** CI's lint job runs `dev.py lint` and has none of
  these tools, so adding them there would break CI. Adding them to CI as well
  was not asked for, and it changes what a push to GitHub runs, so that is left
  as a human decision.
- **Conditional, by the user's instruction.** It runs only when the change
  touches `.github/workflows/` (night-run decides this from `git diff` against
  the run branch plus untracked files, not from memory), or when a workflow run
  is known to have failed. It is not in the §1.6 baseline, so on a machine
  without the tools the run can still proceed, and only a task that needs the
  check is abandoned. An earlier draft ran it on every task; that was replaced.

**Evidence.** On the real `ci.yml`: exit 0. On a scratch workflow with an
unquoted `rm $files` and a `shell: python` step using an undefined name: SC2035,
SC2086 and pyflakes' `undefined name`, exit 1. With the tools unavailable
(`USERPROFILE` pointed elsewhere): `not found: actionlint, shellcheck,
pyflakes`, exit 2.

`ci.yml` has no `shell: python` step today, so pyflakes currently checks
nothing. It is included so that such a step cannot be added unchecked.
