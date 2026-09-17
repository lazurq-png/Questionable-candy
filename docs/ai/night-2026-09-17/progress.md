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

### T2 — Health data on Candy — done

- **Branch:** `night-2026-09-17-t2-health-data`. Clock at start 16:13; budget
  14,911,182.
- **Changed:**
  - `shop/allergens.py`: the EU 14 as `(key, label)` pairs, with `names()`
    (decisions.md D3).
  - `Candy.sugar_content_g`: `Decimal(4,1)`, null means unknown, validators
    0-100, and the check constraint `candy_sugar_per_100g_in_range`.
  - `Candy.allergens`: `ArrayField` of vocabulary keys, default `[]`.
  - `User.allergies`: choices from the same vocabulary.
  - Migrations: `shop 0009_candy_health_data` (two ADD COLUMNs and one ADD
    CONSTRAINT, all additive) and `accounts 0002_user_allergies_vocabulary`
    (`sqlmigrate`: no-op).
  - Admin: both fields on the Candy form, with allergens as 14 checkboxes;
    `UserAdminChangeForm` with allergies as 14 checkboxes.
  - `seed_candy`: sugar and allergens for all 22 candies. The emptiness check
    is now `is_empty()` (None, "" or []), so 0 g sugar is kept, not refilled.
  - Detail partial (page and popup): "Sugar and allergens" after the flaw,
    showing "N g per 100 g" or "Unknown", and allergen names or "None listed".
    Styled in `site.css`.
  - `docs/data-model.md` §3.1 and §3.3 updated: `sugar_content_g` and
    `allergens` are no longer "Missing".
  - Dev database: migrated by `dev.py`, then `seed_candy` run twice (22
    unchanged, 22 filled; then all unchanged). 0 candies with null sugar, 9
    with allergens (corrected in T3's commit; this entry first said 8).
- **Verification actually run:**
  - T2's tests: 77 passed. With a fresh database (`--create-db`), the health,
    view and detail tests: 51 passed.
  - Negative controls, each failed as it should, then restored:
    - seed emptiness back to falsiness → 1 seed test failed;
    - the `AddConstraint` removed from migration 0009 (fresh test database) →
      2 database tests failed;
    - choices removed from `Candy.allergens` → 1 failed;
    - choices removed from `User.allergies` → 1 failed;
    - the health section removed from the template → 4 failed (3
      integration, 1 e2e).
  - Two earlier controls were invalid and were redone: one broke the
    migration's syntax, and one left the section's text in place.
  - `python scripts/dev.py test`: exit 0, **272 passed**, coverage 98%.
  - `python scripts/dev.py lint`: exit 0, **9.88/10**. Against the baseline:
    one message fixed (the final newline in `shop/models.py`); still only
    T1's R0801 extra. Along the way, a first run showed mixed line endings
    from heredoc appends and 17 missing docstrings; all fixed.
  - `python scripts/adr_guards.py`: exit 0. `makemigrations --check`: exit 0.
- **Review:** `reviewer` approved with one Low finding: the user admin silently
  drops legacy free-text allergies. Not fixed in code, for the reason in
  decisions.md D4; raised as questions.md Q2. The comment nit on `KEY_LENGTH`
  was fixed.

### T3 — Log in, log out, sign up, "My allergies" — done

- **Branch:** `night-2026-09-17-t3-accounts`. Clock at start 16:28; budget
  14,857,912.
- **Changed:**
  - `accounts/urls.py` (namespace `accounts`, under `/accounts/`): Django's
    `LoginView` and `LogoutView` (POST only), `SignUpView` and `my_allergies`.
  - `mysite/settings.py`: `LOGIN_URL`, `LOGIN_REDIRECT_URL`,
    `LOGOUT_REDIRECT_URL`. `mysite/urls.py` includes the accounts URLs.
  - `accounts/forms.py`: `SignUpForm` (Django's `UserCreationForm` plus
    optional allergy checkboxes) and `AllergiesForm` (bound to the current
    user).
  - `accounts/views.py`:
    - `SignUpView`: `FormView` plus Django's `RedirectURLMixin` for safe
      `next`, logs straight in, and has LoginView's decorators (D7).
    - `my_allergies`: `@login_required`, form bound to `request.user`, no id
      in the URL.
  - Templates: `accounts/login.html`, `signup.html`, `my_allergies.html`, and
    `partials/account_nav.html`, included in `base.html`'s header (layout in
    D5, question Q3).
  - `site.css`: the header account control and menu, account form styles
    (inputs, help text, errors, a fieldset of 44px checkbox labels), and
    `.page-actions a` gets `min-width: var(--tap)`, because the e2e check
    found the sign-up page's "Log in" link just under 44px wide.
  - Tests: `tests/integration/test_accounts.py` (21) and
    `tests/e2e/test_accounts.py` (4).
- **Verification actually run:**
  - Accounts tests: 25 passed.
  - Found on the way:
    - Django rotates the CSRF token at login, so tests that post after login
      must re-read it, as a browser does from the next page. Fixed in the
      tests; not a product defect.
    - The browser's `required` check blocks an empty login submit, so the
      error-state e2e test uses a wrong password instead.
  - Negative controls, each failed as it should, then restored:
    - username not truncated → header overflow at 375px (2 failed);
    - "Sign up" shown on phones → overflow in test_theme and the accounts
      checks;
    - sign-up following any `next` → the external-next test failed;
    - SignUpView's decorators removed → the masking test failed.
  - `python scripts/dev.py test` (before the review fixes): exit 0, **296
    passed**, coverage 98%, `accounts/*` at 100%. Re-run after them:
    exit 0, **297 passed**, coverage 98%; lint 9.89 with the same two extras;
    adr_guards 0; drift 0.
  - `python scripts/dev.py lint`: exit 0, 9.89/10. New against the baseline:
    R0901 on `accounts/forms.py` (D6); T1's R0801 remains.
  - `python scripts/adr_guards.py`: exit 0. `makemigrations --check`: exit 0.
- **Review:** `reviewer` approved with three Low findings, all acted on:
  1. Sign-up did not mask passwords in error reports: decorators added and
     tested (D7).
  2. The header departs from the plan's wording, unrecorded: now D5 and Q3.
  3. The account menu was named only by the username: a visually hidden ",
     account menu" was added, and the e2e assertion updated.

### T4 — UC-07 health warning — done

- **Branch:** `night-2026-09-17-t4-health-warning`. Clock at start 16:52;
  budget 14,794,616.
- **Changed:**
  - `shop/checkout.py` (D8): `health_warning(lines, user)` builds the sugar
    lines, the total (each bag counts as 100 g), candies with unknown sugar by
    name, the allergens in vocabulary order with their candies, and the
    customer's matches, plus a sha256 fingerprint of all of it.
    `acknowledge()` stores the fingerprint and when; `is_acknowledged()`
    compares.
  - `shop/views.py` `checkout_warning` (`/checkout/warning/`,
    `@login_required`):
    - an empty cart redirects to the cart page, carrying the cart's notices;
    - a POST with a stale fingerprint gets a notice and the current warning;
    - otherwise the form needs the tick, then post/redirect/get (D9).
  - `shop/forms.py` `HealthWarningForm`: a required checkbox plus the
    fingerprint.
  - `shop/cart.py` `_save` clears `session["checkout"]` on every cart write
    (D10).
  - Templates: Continue on `checkout.html`; `checkout_warning.html` (sugar
    table, allergen list with a "You listed this allergy" badge and a summary
    line, the acknowledgment form).
  - `site.css`: warning styles. The sugar table scrolls inside its own box on
    a phone.
  - Tests: `tests/unit/test_checkout_warning.py` (7),
    `tests/integration/test_checkout_warning.py` (13),
    `tests/e2e/test_checkout_warning.py` (3).
- **Verification actually run:**
  - T4's tests: 23 passed, plus the cart integration suite. Found on the
    way: the inline "Change my allergies" link was a 125x19 tap target, so it
    became a standalone link.
  - Negative controls, each failed as it should, then restored:
    - stale fingerprint accepted → 1 failed;
    - the customer's allergies left out of the fingerprint → 1 failed;
    - unknown sugar counted as zero → 1 failed;
    - `@login_required` removed → 1 failed;
    - the "You listed this allergy" badge removed → 2 failed (integration and
      e2e);
    - after the review fixes: the cart write keeping the acknowledgment → 1
      failed; the old tick-first order → 1 failed.
  - One control first selected no tests (a shell-split `-k`) and was rerun.
  - `python scripts/dev.py test` (before the review fixes): exit 0, **318
    passed**, coverage 98%, `shop/checkout.py` 100%. Re-run after them:
    exit 0, **320 passed**, coverage 98%; lint 9.90 with only D1/D6 extras;
    adr_guards 0; drift 0.
  - `python scripts/dev.py lint`: exit 0, 9.90/10, no new messages beyond D1
    and D6. A first run found a trailing newline, 9 docstrings and 2 style
    notes, all fixed.
  - `python scripts/adr_guards.py`: exit 0. `makemigrations --check`: exit 0.
- **Review:** `reviewer` approved with two Low findings, both fixed and
  negative-controlled:
  1. An undone cart change re-validated the acknowledgment (D10).
  2. An unticked submit of a changed warning gave no notice and kept the stale
     fingerprint: the fingerprint is now checked first.
