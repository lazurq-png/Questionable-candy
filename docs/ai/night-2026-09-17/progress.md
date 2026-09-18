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

### T5 — UC-08 triple confirmation, one page — done

- **Branch:** `night-2026-09-17-t5-confirmation`. Clock at start 17:13;
  budget 14,748,013.
- **Changed:**
  - `shop/checkout.py`: `order_snapshot`, `show_for_confirmation` /
    `shown_for_confirmation`, `confirm` / `confirmed_order`. `acknowledge`
    still starts progress afresh.
  - `shop/forms.py` `ConfirmOrderForm` (D11).
  - `shop/views.py` `checkout_confirm` (`/checkout/confirm/`,
    `@login_required`):
    - an empty cart goes to the cart page;
    - without an acknowledged warning, back to the warning;
    - the shown order is remembered, and a POST for a changed order is refused
      with a notice;
    - a valid POST records the confirmation (post/redirect/get) and the page
      says "Confirmed. Placing orders is not built yet…".
  - `checkout_warning` now redirects to it (D11 supersedes D9).
  - Templates: `checkout_confirm.html` (the lines, total and the three
    controls unlocked by Alpine); the warning's acknowledged state links on.
  - `site.css`: confirmation line grid, step list, checkbox label, disabled
    field.
  - Tests: `tests/unit/test_confirm_order_form.py` (17 cases),
    `tests/integration/test_checkout_confirm.py` (13 cases),
    `tests/e2e/test_checkout_confirm.py` (3). Two T4 tests updated to the new
    next step.
- **Verification actually run:**
  - T5 and T4 tests: 43 unit and integration, 6 e2e, all passed. The first
    e2e Enter check could not fail (a disabled default button blocks implicit
    submission anyway), so it was moved to after the button unlocks.
  - Negative controls, each failed as it should, then restored:
    - Enter not prevented → e2e failed;
    - the button's `x-bind:disabled` removed → e2e failed;
    - any `place_order` value accepted → 1 unit failed;
    - no snapshot comparison → the price-change test failed;
    - the acknowledgment precondition removed → 2 failed.
  - First review: **request changes**. One Medium and two Low findings, all
    fixed and negative-controlled:
    1. Medium: a stock cap while confirming sent the customer to the warning
       without the reason. Notices now travel as messages; 2 tests, GET and
       POST. Control: 2 failed.
    2. Low: before or without Alpine, Enter placed the order. Now a hidden,
       disabled default submit button; new e2e test with JavaScript off.
       Control: 2 failed.
    3. Low: a POST was judged only against the session's last-shown order. The
       page now posts its fingerprint. Control: 1 failed.
  - T5 and T4 tests after the fixes: 54 passed.
  - **Re-review: approved.** All three findings confirmed resolved (the
    reviewer ran 358 passed itself). Its nit, closing the no-JavaScript
    browser context in a `finally`, was fixed.
  - Commit gate after the nit: `python scripts/dev.py test` exit 0, **358
    passed**, coverage 98%; lint exit 0, 9.91/10, no new messages beyond
    D1/D6; adr_guards exit 0; drift exit 0.

### T6 — Orders without payment — done

- **Branch:** `night-2026-09-17-t6-orders`. Clock at start 17:48; budget
  14,688,384.
- **Changed:**
  - `shop/models.py`:
    - `Order` (status choices, `user` PROTECT, a total ≥ 0 check);
    - `OrderItem` (`candy` PROTECT, quantity ≥ 1, and a subtotal = quantity ×
      unit price check);
    - `OrderManager.place()` and `OrderChanged` (D12).
  - Migration `shop 0010_orders`: creates the two tables and their
    constraints only.
  - `shop/views.py`: a valid confirmation calls `_place_order`. On
    `OrderChanged` it messages and redirects to the cart, keeping the cart;
    otherwise it clears the cart and redirects to `order_received`
    (`/orders/<pk>/`, login required, 404 for anyone but the owner).
  - `shop/cart.py` `clear()`; `shop/checkout.py` `acknowledged_at()`, with
    T5's interim confirm record removed.
  - `shop/admin.py`: `OrderAdmin`, view-only, with the items inline.
  - Templates: `order_received.html`; the confirm page's interim confirmed
    state removed.
  - `docs/data-model.md` §3: Order and OrderItem marked implemented.
  - Tests: `tests/integration/test_orders.py` (16), `tests/e2e/test_orders.py`
    (1, the whole checkout from an anonymous cart). T5's integration and e2e
    tests updated from "confirmed" to "order placed".
- **Verification actually run:**
  - T6 and T5 tests: 16 integration, 34 confirm and warning, 5 e2e, all
    passed.
  - Negative controls, each failed as it should, then restored:
    - price not re-checked → 1 failed;
    - stock not reduced → 1 failed;
    - cart not cleared → 2 failed;
    - receipt not scoped to its owner → 1 failed;
    - admin change permitted → 1 failed;
    - `select_for_update` removed → at first nothing failed, as predicted, so
      a test asserting the FOR UPDATE query was added, and it then failed.
  - Not tested: truly concurrent orders by two customers (D12).
  - First review: **request changes**. One Medium finding: a double-click
    placed two orders. Fixed with a per-page confirmation token (D14),
    `Order.confirmation_token` (migrations `0011` and `0012`, additive; probed
    with existing rows) and an already-placed check in `place()`. New tests:
    - the same token placed twice gives one order, with stock taken once;
    - the same cart from two showings gives two orders;
    - the database refuses a duplicate token;
    - the double-click race, reproduced by restoring the pre-submit session;
    - an older page's token is refused.

    Controls: without the already-placed check, 2 failed; with the posted
    token ignored, 1 failed. The other T6 and confirmation tests: 38 passed.
  - Migration test for 0011-0012 with pre-existing orders: passed. Control:
    without 0011's data step, NOT NULL violation. Its first version failed
    for real on PostgreSQL's pending deferred-trigger rule, which is the
    reason for the split (D14).
  - `place()` reuses `order` for the already-placed lookup, which clears a new
    R0914 (too many locals).
  - Commit gate (code unchanged since): `python scripts/dev.py test` exit 0,
    **381 passed**, coverage 99%; lint exit 0, 9.92/10, new messages only
    D1/D6/D13; adr_guards exit 0; drift exit 0. Dev database: 0010-0012
    applied.
  - **Re-review: approved**, no findings. One non-blocking note: if the second
    request of a double-click loads the old session but reads stock after the
    first order used up a candy, `cart.lines()` writes the old cart back. The
    customer lands on the warning or cart page with the ordered items in the
    cart again, not on the receipt. No duplicate order and no stock lost;
    session last-write-wins, not introduced here.

### T7 — Slug URLs and unique names — done

- **Branch:** `night-2026-09-17-t7-slugs`. Clock at start 18:39; budget
  14,611,569.
- **Precondition checked first:** the dev database holds 22 candies with no
  duplicate names (case-insensitively either), no colliding slugs and no empty
  or all-digit ones. So the task proceeded rather than stopping.
- **Changed:** `Candy.slug` and a unique `name`; `unique_candy_slug`;
  `ensure_slug` from `clean()` and `save()`; `get_absolute_url`; the
  `candy_slug_is_not_all_digits` check; `candy_detail(slug)` and
  `candy_detail_by_pk` with its 301; `candy_link.html`; the admin (slug field,
  prepopulated on add, read-only afterwards); `docs/data-model.md`;
  migrations `0013`, `0014` (hand-written) and `0015`.
- **Verification actually run:**
  - T7's tests: 35 passed after the review fixes (unit, integration, admin,
    e2e).
  - Negative controls, each failed as it should, then restored:
    - the old URL not redirecting → 2 failed;
    - the redirect not permanent → 1 failed;
    - digit slugs not prefixed → 1 failed;
    - collisions not resolved → 2 failed;
    - the migration ignoring collisions → 1 failed;
    - links still using the number → 1 failed;
    - the slug editable after creation → 1 failed;
    - `prepopulated_fields` removed → 1 failed;
    - the slug check constraint removed (fresh database) → 1 failed.
  - Migration test with pre-existing candy, including two names that slugify
    alike, an unnameable one and an all-digits one: passed.
  - Existing tests updated from `pk` to `slug` for the detail URL (15 in
    `test_views.py`, 1 in `test_shoppingcart.py`), and one test deleted whose
    premise is now impossible (D15).
  - `python scripts/dev.py test`: exit 0, **403 passed**, coverage 99% (before
    the review fixes; re-run below).
  - `python scripts/dev.py lint`: exit 0, 9.92/10, no new messages beyond
    D1/D6/D13. A first run had 12 missing docstrings, an unused import, mixed
    line endings and a second duplicate-code pair; the duplicated migration
    helper became `tests/integration/migration_helpers.py`.
  - `python scripts/adr_guards.py`: exit 0. `makemigrations --check`: exit 0.
- **Review:** approved, with four Low findings and a nit, all acted on (D15).
  Two follow-on problems the fixes exposed, both fixed: the admin looks up
  `prepopulated_fields` on the change form (hence `get_prepopulated_fields`),
  and `full_clean` validates the new constraint before `save()` fills the slug
  (hence filling it in `clean()`).
- **Re-review: approved.** It mutation-checked each new behaviour and found
  each pinned by a test that fails without it. Two remaining Low items, both
  documentation, both done: the slug has no admin correction path once set
  (said so in `get_readonly_fields` and D15 -- it is a shell or
  data-migration operation), and the new constraint is now named in
  `docs/data-model.md` and explained in `0015`'s header, with the query to
  find offending rows, as migration `0003` does.
  Its note, not a finding: `test_the_admin_refuses_a_slug_of_digits_alone`
  would still pass without the field validator, because the constraint's
  message is the same string.
- **Commit gate:** `python scripts/dev.py test` exit 0, **405 passed**,
  coverage 99%; lint exit 0, 9.92/10, only D1/D6/D13 extras; adr_guards
  exit 0; drift exit 0. The documentation fixes after it touched no code
  path; the slug and migration tests were re-run: 19 passed.

### T8 — The theme toggle can return to the system setting — done

- **Branch:** `night-2026-09-17-t8-theme-reset`. Clock at start 21:12; budget
  14,536,791.
- **Changed:** `theme.js` clears the stored choice and the `data-theme`
  attribute when a click lands on the system's own theme (D16); two e2e tests.
- **Verification actually run:**
  - `tests/e2e/test_theme.py`: 13 passed (11 before).
  - Negative controls, each failed as it should, then restored:
    - the attribute kept on the way back → 2 failed;
    - the choice still stored on the way back → 2 failed;
    - `aria-pressed` read from the attribute instead of what is shown → 2
      failed.
  - `python scripts/dev.py test`: exit 0, **407 passed**, coverage 99%.
  - `python scripts/dev.py lint`: exit 0, 9.92/10, no new messages beyond
    D1/D6/D13 (one mixed-line-ending fix). pylint does not read JavaScript, so
    it says nothing about `theme.js`.
  - `python scripts/adr_guards.py`: exit 0. `makemigrations --check`: exit 0.
- **Review:** approved with four Low findings, all four fixed: the `catch`
  comment now covers clearing as well as storing, both new tests call
  `assert_page_is_fully_rendered`, the clearing-into-dark click now asserts
  `aria-pressed` (with the control above), and `shown()` reuses
  `systemTheme()` instead of repeating it.

### T9 — Correct outdated records, propose ADR 0008 — done

- **Branch:** `night-2026-09-17-t9-records`. Clock at start 21:35; budget
  14,519,176.
- **The five sentences changed**, quoted:
  1. `docs/adr/0001-frontend.md`: "The choice of **Django Templates** stands
     unchanged, and the hand-written-CSS half of this decision is still
     unexercised — no CSS exists yet." → now says that half was unexercised
     **until 2026-09-16**, names `shop/static/shop/site.css` and links ADR
     0008.
  2. `docs/adr/0006-frontend-htmx-alpine.md`: "its hand-written-CSS decision
     stands as still-unexercised — no CSS of any kind exists yet, so nothing
     about styling is settled here." → "was still unexercised **when this ADR
     was written**, so nothing about styling **was** settled here. CSS arrived
     on 2026-09-16; ADR 0008 proposes the conventions it set."
  3. `docs/adr/0005-testing.md`: "`pytest-playwright` is installed and
     `tests/e2e/` exists but is still empty" → past tense, plus a new
     "**Update 2026-09-17 — `tests/e2e/` is no longer empty**" paragraph
     listing what it now covers and noting CI runs it.
  4. `.claude/skills/night-run/SKILL.md` §9's premise: "…is still unexercised
     — no CSS of any kind exists in this project." → a paragraph saying CSS
     has existed since 2026-09-16, that §9.4's three assertable checks run in
     `tests/e2e/test_theme.py` (the screenshots are a run's own step), and
     that what remains unlooked-at is how the pages appear. **§9.1-§9.6's
     rules are untouched** (the reviewer confirmed byte-identical).
  5. Not on the list, changed for coherence with 3: `docs/adr/0005-testing.md`
     "There **is** a concrete first case waiting for it" → "There **was**".
- **Added:** `docs/adr/0008-hand-written-css-themes.md`, status **proposed**,
  following `0000-adr-template.md`; and a line for it in README's ADR index.
- **Proof:** `grep -rn "no CSS exists yet\|no CSS of any kind exists\|exists but
  is still empty" docs/ .claude/` matches only the run records that quote them
  (night-2026-09-16 `questions.md`, this run's `plan.md`, and this entry).
  `python scripts/adr_guards.py` exit 0. `python scripts/dev.py lint` exit 0,
  9.92/10, unchanged. `python scripts/dev.py test` exit 0, **407 passed**
  (documentation only; nothing could move it). Drift 0.
- **Review:** **request changes**, then fixed. It checked every claim against
  the code and found two the ADR had invented, which is the very fault this
  task exists to remove:
  1. Medium: the ADR said the CDN scripts are "pinned with integrity hashes".
     They are not — that is T10a, unbuilt. Rewritten to say they were pinned
     by version alone when written. **T10a must correct this clause and ADR
     0006's equivalent line once SRI lands.**
  2. Medium: it said `adr_guards.py` would fail on a Tailwind dependency. It
     would not; the guards read `requirements.txt` only. Rewritten, and it now
     agrees with the ADR's own Confirmation section.
  3. Medium: the README's ADR index did not list ADR 0008. Added.
  4. Low: no `progress.md` entry yet, and the fifth (tense) edit unrecorded.
     This entry.
  5. Low: "1000-line stylesheet" — it is 1320. Now "1300-line".
  6. Low: `templates/500.html` repeats the stylesheet link and the inline theme
     script, so "one stylesheet, loaded from base.html" was incomplete. Said
     so, with why.
  7. Low: §9.4 has four checks, only three of them assertions. Corrected.
  Its out-of-scope observations became questions.md Q4.

### T10a — Subresource integrity for the CDN scripts — done

- **Branch:** `night-2026-09-17-t10a-sri`. Clock at start 21:53; budget
  14,480,359.
- **The granted network access, used exactly as granted:** two GETs, one per
  script, to the unpkg URLs already in `templates/base.html`, following their
  redirects (D17 has the URLs, sizes and hashes). Nothing else was fetched and
  nothing downloaded was committed.
- **Changed:** both `<script>` tags in `base.html` now name one exact file and
  carry `integrity="sha384-…" crossorigin="anonymous"`; htmx's URL is the file
  its package URL redirects to. New `tests/integration/test_script_integrity.py`
  (3) and one e2e check that htmx and Alpine actually load.
- **Also:** the two record nits the T9 reviewer left and T9's own polish script
  did not reach before its commit (the grep parenthetical in T9's entry, and
  Q4's missing "In the meantime" label).
- **Verification actually run:**
  - T10a's tests plus the catalog e2e suite: 12 passed.
  - Negative controls, each failed as it should, then restored:
    - htmx's hash altered by one character → the browser refused the script and
      the e2e check failed;
    - Alpine's `integrity` removed → the markup test failed;
    - htmx's URL put back to the bare package → the one-file test failed.
  - `python scripts/dev.py test`: exit 0, **411 passed**, coverage 99%.
  - `python scripts/dev.py lint`: exit 0, 9.92/10, no new messages beyond
    D1/D6/D13 (one mixed-line-ending fix).
  - `python scripts/adr_guards.py`: exit 0. `makemigrations --check`: exit 0.
- **Review:** approved, with five Low findings, all fixed:
  1. the entry said "Full gate: below" with nothing below -- the numbers above
     replace it;
  2. Q5 missed a third stale paragraph (ADR 0006's Confirmation section) --
     added;
  3. T9's entry told T10a to correct the ADRs; that is superseded by the
     plan's T9-only grant, and the record now says so;
  4. the new browser test did not call `assert_page_is_fully_rendered`,
     although this change added a comment block to `base.html`'s head -- it
     does now;
  5. the script-tag guard only matched a double-quoted `src`, so a
     single-quoted third script would have slipped past "exactly two". It now
     matches either quote style: with Alpine's tag rewritten single-quoted,
     all three tests still pass, and removing its `integrity` then fails one.
- **A mistake worth recording:** cleaning up after a control, I restored
  `templates/base.html` with `git checkout`, which restores from the last
  commit -- so it silently discarded T10a's own tag change. Caught by reading
  the file straight afterwards, and restored from the copy taken before the
  controls. The other controls used `cp` from a backup, which is what this one
  should have done. Nothing outside this task's own uncommitted work was
  touched.
- **Not fixed here:** ADR 0006 and ADR 0008 still say the scripts have no
  integrity hash. T9's entry above says "T10a must correct this clause and ADR
  0006's equivalent line once SRI lands" -- that was the T9 reviewer's
  instruction, and it is **superseded by the plan**, which grants editing a
  decision record to T9 alone. So the correction moved to questions.md Q5,
  with the exact wording to use, rather than being done or dropped.

### T10b — A coverage floor of 95% — done

- **Branch:** `night-2026-09-17-t10b-coverage-floor`. Clock at start 22:20;
  budget 14,451,949. The last of the plan's requested tasks.
- **Changed:** `scripts/dev.py` gains `COVERAGE_FLOOR = 95` and passes
  `--cov-fail-under` to the full `test` task only (D18); its comment now says
  what the number is for and that lowering it is not a way to pass. ADR 0005's
  "Not enforced: there is no coverage threshold" became a dated update saying
  the threshold exists, what it is and why -- the plan directs this task to
  make that edit.
- **Verification actually run:**
  - `python scripts/dev.py test`: exit 0, **411 passed**, "Required test
    coverage of 95% reached. Total coverage: 98.78%".
  - Control: the floor temporarily at 100 → exit 1, "Required test coverage of
    100% not reached", with all 411 tests still passing. Restored; the change
    was not committed.
  - `python scripts/dev.py test:unit`: 139 passed, no coverage requirement
    reported, confirming single suites stay ungated.
  - Coverage was already 98.78%, so no tests had to be written to reach the
    floor.
- **Review:** approved, with three Low informational findings, all taken as
  comments rather than code: narrowing `dev.py test` with `-k` now fails on
  coverage (use the per-suite tasks; `--no-cov` is for looking at a failure,
  not a passing run), the rounding that makes the effective floor 94.5%, and
  migrations sitting in the measured denominator. The reviewer reproduced the
  gate's behaviour independently, including that a filtered run, an empty
  suite and a partial suite all fail closed.

### T11 — Exploration survey — done

- **Branch:** `night-2026-09-17-t11-survey`. Clock at start 22:43; budget
  14,439,941. All ten requested tasks were complete, verified, reviewed,
  merged and pushed; the run branch was green and clean; well before 07:15.
- **Produced:** `findings.md` — five findings, ranked, each with evidence, the
  proof a fix would need, and a size; plus what was checked and found sound.
- **Probes run** (throwaway tests, deleted afterwards):
  - query counts per page: catalog 1 at 12 and at 24 candies, detail 1, cart 2,
    checkout 2, warning 3, admin order list 5 — no N+1 anywhere;
  - whether a candy can end up with a blank slug: it cannot, because the T7
    check constraint rejects the empty string;
  - `Cache-Control` on every customer-specific page: absent except where
    Django or T3 added `never_cache` (**F1**);
  - how form errors render: Django's own fields carry `aria-invalid` and
    `aria-describedby`, but the confirmation page's hand-written controls do
    not (**F2**).
- **The plan's discretionary section** now lists the tasks the survey produced.

### T12 — F1: customer-specific pages are never cached — done

- **Branch:** `night-2026-09-17-t12-never-cache`. Clock at start 22:46; budget
  14,423,430. First task of the exploration phase.
- **Changed:** `@never_cache` on `shoppingcart`, `shoppingcart_panel`,
  `checkout`, `checkout_warning`, `checkout_confirm`, `order_received` and
  `accounts.my_allergies`, with the reason on the first of them. The catalog
  and detail pages are deliberately left cacheable.
- **Verification actually run:**
  - `tests/integration/test_no_cache.py`: 8 passed.
  - Negative controls, each failed as it should, then restored: `never_cache`
    removed from the cart dropdown → 1 failed; removed from My allergies → 1
    failed. The reviewer additionally neutralised `never_cache` wholesale from
    a scratchpad plugin and got 7 failed, 1 passed — the catalog control test
    being the one that passes either way, as intended.
  - `python scripts/dev.py test`: exit 0, **419 passed**, coverage 98.80%,
    above the new floor.
  - `python scripts/dev.py lint`: exit 0, 9.93/10, no new messages (one
    docstring added). `adr_guards` exit 0. Drift 0.
- **Review:** approved, two Low findings, both fixed: `order_received` had
  `@login_required` outermost, so its redirect for an anonymous visitor
  escaped `never_cache` (swapped, matching the other three); and the
  docstring justified leaving the catalog cacheable with `Vary`, the very
  thing it had just said does not address a browser's own history cache. The
  reasoning is corrected, and the residual it names — the header shows the
  signed-in customer's username on those pages — is now **findings.md F6**,
  ranked last because closing it trades caching on the main pages.

### T13 — F2: the confirmation page's controls are linked to their errors — done

- **Branch:** `night-2026-09-17-t13-confirm-a11y`. Clock at start 23:07;
  budget 14,405,890.
- **Changed:** `ConfirmOrderForm` renders the tick and the typed total as
  widgets (carrying the Alpine bindings as widget attributes) instead of the
  template writing raw `<input>`s, so Django marks a refused control
  `aria-invalid` and points `aria-describedby` at its own error list. The
  template uses the form's own ids for its labels. The form sets
  `use_required_attribute = False`, and the Place my order button points at
  its message only when it has one -- both from the review, below.
- **Verification actually run:**
  - `tests/integration/test_checkout_confirm.py`: 23 passed, including four new
    tests — the aria attributes on each refused control; that the typed value,
    the ticked state, the Alpine bindings and `inputmode` survive; that neither
    control gets a browser `required`; and that the button points at its
    message only when it has one.
  - Controls, each failed as it should, then restored: the tick written by hand
    again → 2 failed (the aria test and the ticked-state one); the `required`
    suppression removed → 1 failed; the button's conditional attribute removed
    → 1 failed.
  - `tests/e2e/test_checkout_confirm.py` and `test_orders.py`: 5 passed, so the
    unlock order, the no-JavaScript path and the whole checkout still work.
  - `python scripts/dev.py test`: exit 0, **424 passed**, coverage 98.80%.
  - `python scripts/dev.py lint`: exit 0, no new messages (one trailing-newline
    fix). `adr_guards` exit 0. Drift 0.
- **Interrupted:** at about 23:15 the session hit its own rate limit (reset
  01:10 Europe/Stockholm) while the `reviewer` was running; the agent was
  terminated after four tool calls and delivered no report. **Nothing was
  committed**, because an unattended commit needs that review (night-run §2
  step 3), and the work sat uncommitted on its branch until the session could
  run the review again at 01:19. Three hourly loop firings arrived during the
  gap; each is the same session resuming this run.
- **Review:** request changes, then approved on re-review. Three Low findings,
  all acted on:
  1. rendering through the form also added `required`, which a browser would
     act on before the server could -- changing what a customer without
     JavaScript sees, and putting the very refusals this task is about out of
     reach. Fixed with `use_required_attribute = False`, so the markup is what
     the hand-written inputs produced plus the aria pair;
  2. `assert "checked" in tick` could not fail ("checked" is also in `name=`
     and `x-model=`). It now asserts the attribute;
  3. the Place my order button is not a form field, so its error list had
     nothing pointing at it. It now does, conditionally, so the attribute can
     never name an id that is not on the page.
  The re-review's own two Low items are done: the button assertion is anchored
  to the button's tag rather than the whole page, and this entry was refreshed
  to match the diff it describes.

### T14 — F4: the README describes the site as it now is — done

- **Branch:** `night-2026-09-17-t14-readme`. Clock at start 01:49; budget
  14,378,090.
- **Changed:** `README.md` only. The Status section said most of the
  specification was unbuilt and named one app; it now says what is built, per
  use case, and what is not (payment, Google sign-in, order history). Also: the
  95% coverage gate and the browser suite, CI's three jobs and its `night-**`
  trigger, the narrowed `shop.Candy` difference, and two more open items
  (payment never leaving `pending`, ADR 0008 awaiting a decision).
- **Verification actually run:** `python scripts/dev.py test` exit 0, **424
  passed**, coverage 98.80%; lint exit 0 with no new messages; `adr_guards`
  exit 0; drift 0. A documentation change cannot move any of them; they were
  run because the commit gate asks for them.
- **Review:** request changes, then all five corrections made. It checked every
  claim against the code and found the new text wrong in four places and silent
  in a fifth:
  1. "UC-05 steps 1-4 and 7" — step 7 says the order is created **as Paid**
     and **links to order tracking**, neither of which exists. Now "step 7 in
     part", spelled out.
  2. "no way to look back at an order once they leave its receipt" — the
     receipt has a stable URL scoped to its owner, so this denied access the
     code grants. The real gap is that nothing lists or links to past orders.
  3. UC-09 was in neither list, although sign-up and login implement it bar the
     email verification. Added.
  4. The `shop.Candy` item dropped the extra `flavor` and `image` fields the
     data model names — `image` being what the media-storage open item above it
     will replace. Restored.
  5. A sentence the diff passed over said CI runs the guards and the suite on
     `master` and `dev`; it runs three jobs including lint, and on `night-**`
     pushes too — which is what checks this run's own branches.

### T15 — F3: the deployment entry points and the settings guards are tested — done

- **Branch:** `night-2026-09-17-t15-entry-points`. Clock at start 01:59; budget
  14,364,869.
- **Changed:** `tests/unit/test_deployment_entry_points.py` (4 tests) and a
  `without=` parameter on `tests/unit/test_settings.py`'s existing
  `load_settings`, which runs `settings.py` under a throwaway module name.
- **Verification actually run:**
  - `python scripts/dev.py test`: exit 0, **428 passed**, coverage **100.00%**
    — these were the last uncovered lines in the project.
  - Controls, each failed as it should, then restored: the secret-key guard
    removed → 1 failed; `wsgi.application` broken → 1 failed; the `load_dotenv`
    stub removed, letting `.env` put the variable back → 2 failed.
  - `python scripts/dev.py lint`: exit 0, no new messages. `adr_guards` exit 0.
    Drift 0.
- **Review:** request changes, then approved after a rewrite. The first version
  reloaded the live `mysite.settings` module and undid itself with a
  `try/finally` and an environment restore — while the repository already had
  a loader written so that testing `settings.py` leaves the configured settings
  alone. Rewritten on that loader: the reload, the `finally`, the env restore
  and a doubled `pytest.raises` all went away, and the reviewer confirmed the
  helper's extension is inert for its three existing callers, that no
  environment or module state leaks, and that removing either guard makes the
  test fail.
- **A mistake, the same one as in T10a:** cleaning up after a control I used
  `git checkout tests/unit/test_settings.py`, which restores from the last
  commit and so discarded the helper extension this task had just written. Spotted
  immediately (the control's own grep showed the parameter gone) and rewritten.
  Every control in this run should use `cp` from a copy taken first; two did
  not.
- **Also:** the plan's `## Discretionary (added by the run)` section now lists
  T13, T14 and T15, which the Exploration section asks for and which the
  previous three tasks had skipped.
