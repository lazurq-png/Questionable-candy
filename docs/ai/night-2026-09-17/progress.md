# Progress — night-2026-09-17

## Session 1

### Preflight (§1)

- **Run type:** new. The §1 detection loop printed nothing: `night-2026-09-15`
  and `night-2026-09-16` both have `## Morning report` committed on their own
  branches.
- **Clock at start:** 2026-09-17 15:57 (machine clock; system zone
  `W. Europe Standard Time` confirmed with PowerShell).
- **Deadline: 2026-09-18 08:00.**
- **Budget at start:** 14,999,689 tokens (the harness figure at skill launch).
  Roundup threshold (30%, final session): 4,499,907. Handoff reserve (10%):
  1,499,969. Ceiling (4%): 599,988.
- **Plan:** `docs/ai/night-2026-09-17/plan.md`, written by the human, already
  committed on `dev` (`7274677`). It is not an untracked file, so the first
  task has nothing extra to commit for it.
- **Database (§1.1):** `pg_isready` exit 0; accepting connections.
- **Migration drift (§1.2):** `makemigrations --check --dry-run` exit 0,
  "No changes detected". No drift before the run.
- **Branch (§1.3):** `night-2026-09-17` cut from `dev` at `7274677`. Working
  tree was clean; no pre-existing uncommitted changes to carry.
- **Remote (§1.4):** `origin` = `https://github.com/lazurq-png/Questionable-candy.git`,
  reachable; `git ls-remote --heads origin "night-2026-09-17*"` returned
  nothing. Pushes enabled.
- **Session loop:** the human queued `/loop 1h …` in this session. It is
  scheduled as cron job `66cd9536` (hourly at :07, session-only). It resumes
  this run when the session is idle, and is to be deleted with CronDelete once
  the morning report is written. It was scheduled without asking the loop
  skill's "cloud or this session" question: nobody is available, and a cloud
  agent cannot reach this machine's database or repository.

### Baseline (§1.6), on `night-2026-09-17` at `7274677`

- `python scripts/adr_guards.py` → exit 0 ("ok: no DRF, 5 test packages").
- `python scripts/dev.py lint` → exit 0, **9.87/10**. Report saved as
  `lint-baseline.txt`: conventions (missing docstrings, final newlines) and two
  `W1510 subprocess-run-check` warnings in `scripts/dev.py`. No errors.
- `python scripts/dev.py test` → exit 0, **233 passed** in 77.6 s, coverage
  **98%** (misses: `mysite/asgi.py`, `mysite/wsgi.py`, `settings.py` 38 and 116,
  the two `ImproperlyConfigured` raises).

Green. Requested work starts.

### T1 — Error pages: 404, 500, CSRF 403 — done

- **Branch:** `night-2026-09-17-t1-error-pages`. Clock at start 16:00; budget
  14,949,146.
- **Changed:**
  - `templates/404.html` and `templates/403_csrf.html` extend `base.html`:
    Django renders both with the request (checked in Django 6.1.1's
    `views/defaults.py` and `views/csrf.py`). The CSRF page does not show
    Django's `reason`.
  - `templates/500.html` stands alone: `server_error` renders it with no
    context and no request. It repeats base.html's outline, stylesheet and
    inline stored-theme script, and uses only `static` and `url`.
  - Wording: "This page melted away", "Our candy machine jammed", "That form
    went stale". Each page links back to the catalog.
  - Tests: `tests/integration/test_error_pages.py` (3), the test-only URLconf
    `tests/integration/error_urls.py` (a `/boom/` view that raises, used only
    through `@pytest.mark.urls`), and `tests/e2e/test_error_pages.py` (7).
- **Verification actually run:**
  - New tests: 10 passed.
  - Negative controls:
    - with the three templates moved aside, all 7 tests that existed then
      failed (3 integration, 4 e2e);
    - with the theme script removed from `500.html`, only the stored-dark 500
      case failed;
    - with `403_csrf.html` moved aside, the browser CSRF test failed.
  - Not controlled: the 500 test's `django_assert_num_queries(0)`. No template
    tag available here queries the database, so there was no realistic way to
    make it fail.
  - `python scripts/dev.py test`: exit 0, **243 passed** (baseline 233),
    coverage 98%.
  - `python scripts/dev.py lint`: exit 0, 9.87/10. One new message, R0801
    duplicate-code, between `test_error_pages.py` and `test_theme.py`
    (decisions.md D1).
  - `python scripts/adr_guards.py`: exit 0. Migration drift: exit 0.
- **Review:** `reviewer` approved with two Low findings, both fixed:
  1. The CSRF page had no browser test. Added one, a native `form.submit()`
     after clearing cookies.
  2. `500.html` ignored a stored theme choice. Copied base.html's inline
     script, and added a stored-dark e2e case.
- **Remaining, known:** with JavaScript on, a stale CSRF token on an htmx post
  still does nothing visible, because htmx does not swap a 403. That predates
  this task and is out of T1's scope; see questions.md Q1.
