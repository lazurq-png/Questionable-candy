# Plan — night-2026-09-17

Written by the human before the run (night-run §1.0). Read-only to the run,
except for the `## Discretionary (added by the run)` section at the end.

**Deadline: 2026-09-18 08:00.**

## Objective

Take the shop from "cart and checkout review" to "a logged-in customer can place
an order": error pages, health data, login with sign-up, the UC-07 health warning,
the UC-08 triple confirmation, and orders without payment. Then slug URLs, the
theme reset, outdated records and two safeguards. After that, explore the code
for improvements until 07:15 (see Exploration).

Sources of truth: [`docs/requirements.md`](../../requirements.md) §4,
[`docs/data-model.md`](../../data-model.md) §3, the ADRs in
[`docs/adr/`](../../adr/), and the open questions in
[`night-2026-09-16/questions.md`](../night-2026-09-16/questions.md).

## Scope

In: tasks T1–T10b below, then Exploration.

Out. Log anything that depends on these in `questions.md`, and do not build it
provisionally:

- UC-02 Google login, and any login provider other than username and password
- Anything that sends email: verification, password reset
- Guest checkout
- Real payment, a payment processor, and any "paid" state an order can reach
- An order-tracking or "My orders" page for customers
- Pagination or search in the catalog
- Edits to `docs/requirements.md`. Instead, the morning report lists which §5
  open issues this plan settled, for the human to record.
- §9 visual work. Exploration replaces it tonight. Do not start §9.

## Settled by the human (not ambiguities)

1. Error pages use playful candy wording, and always link back to the catalog.
2. Login is required only to go past the checkout review page. The catalog,
   cart and checkout review stay open to everyone. There is no guest checkout.
3. Customers can sign up with a username and password. No email is involved.
4. Sign-up has an optional allergy picker from the EU 14 list. A small
   "My allergies" page lets a logged-in customer change their allergies later.
5. Sugar is `sugar_content_g` per 100 g. Allergens come from one fixed
   vocabulary, the EU's 14 major allergens, shared by `Candy.allergens` and
   `User.allergies`.
6. The UC-07 warning is built from the cart's contents, not fixed text.
7. UC-08 is three distinct controls on one page, not three screens.
8. Orders stop at `pending`. The page says payment is not connected yet.
9. Placing an order reduces stock, in the same transaction that creates it.
10. Candy gets slug URLs and unique names. Old `/candy/<pk>/` links redirect
    with 301.
11. Toggling the theme back to the system's own theme clears the stored choice.
12. ADR 0008 is written with status `proposed`, never `accepted`.
13. The htmx and Alpine script tags get SRI hashes.
14. `dev.py test` enforces at least 95% coverage.

## Granted exceptions to night-run

Each covers exactly what it names (§1.0).

- **§3 "Contacting any external service"**, for **T10a only**: exactly two
  HTTP GETs, one per script, to the unpkg URLs already in
  `templates/base.html`, following their redirects. The only purpose is to
  compute the sha384 hashes. Nothing else may be fetched, and nothing
  downloaded is committed.
- **§9.6 and the Q4 restriction on editing decision records**, for **T9 only**:
  the named false sentences in ADRs 0001, 0005 and 0006 and in night-run §9 may
  be corrected, and ADR 0008 may be written as `proposed`.
- **§6 "do not invent work"**, for **Exploration only**, within the bounds of
  that section.

Tech stack, unchanged: Django 6.1 templates, hand-written CSS in
`shop/static/shop/`, htmx 2.0.3 and Alpine 3.14.1, and PostgreSQL. No new
packages, CDN resources, Node or build step.

## Tasks

The order matters: T4 needs T2 and T3, T5 needs T4, and T6 needs T5. If a task
in that chain is parked or abandoned, every later task in the chain is too
(§4). T7–T10b do not depend on the chain.

### T1 — Error pages: 404, 500, CSRF 403

- `templates/404.html`, `templates/500.html` and `templates/403_csrf.html`, in
  playful candy wording. Examples:
  - 404: "This page melted away."
  - 500: "Our candy machine jammed."
  - CSRF: "That form went stale. Reload the page and try again."
- Each page links back to the catalog.
- `500.html` stands alone. It does not extend `base.html`, and it needs no
  database, no context processor and no request context, so it renders while
  the site is broken.
- The existing `candy_unavailable.html` (UC-03 ext. 2a) is left as it is.
- Integration tests use `override_settings(DEBUG=False)`:
  - an unknown URL gives 404 with the new page;
  - a view that raises gives 500 with the new page, through a client built with
    `raise_request_exception=False`;
  - a POST with `enforce_csrf_checks=True` and no token gives 403 with the CSRF
    page.

### T2 — Health data on Candy (data-model §3.3)

- The EU 14 allergens are defined **once**, as a constant that both apps use.
  Record where it lives, and why, in `decisions.md`.
- Add `Candy.sugar_content_g = DecimalField(null=True, blank=True)`, grams per
  100 g. Null means unknown, not zero.
- Add `Candy.allergens = ArrayField(CharField, blank=True, default=list)`,
  limited to the vocabulary.
- `User.allergies` is limited to the same vocabulary. Validate in forms and
  in `full_clean`. A choices-only `AlterField` migration is acceptable.
- Additive migrations only. Existing rows get null sugar and no allergens.
- Admin: both fields on the Candy form, with allergens as checkboxes.
- `seed_candy` fills plausible values for all 22 candies, and still fills only
  empty fields on existing rows.
- The detail page (and popup) shows sugar per 100 g ("unknown" when null) and
  the allergens.
- Tests:
  - an unknown allergen is rejected by form and model validation;
  - running the seed twice keeps its values and overwrites nothing;
  - the detail page shows both fields, and shows "unknown";
  - migration drift is 0.

### T3 — Log in, log out, sign up, "My allergies" (UC-09 subset; requirements §5)

- Use Django's built-in `LoginView` and `LogoutView`, with logout as a POST. No
  new package.
- URLs under `/accounts/`. `LOGIN_URL`, `LOGIN_REDIRECT_URL` and
  `LOGOUT_REDIRECT_URL` are set.
- `next` is honoured only for same-site URLs. Django's
  `url_has_allowed_host_and_scheme` handles this; add a test that an external
  `next` is refused.
- Sign-up: username, password twice (Django's password validators), and an
  optional allergy checkbox list from the vocabulary. Sign-up logs the new
  customer straight in.
- "My allergies": a page, login required, that edits the current user's
  allergies and nobody else's.
- Header, logged out: "Log in" and "Sign up". Logged in: the username, a link
  to "My allergies", and a "Log out" button.
- Styling and 44×44 tap targets match the existing header (site.css).
- Checkout review stays open to everyone. The login requirement starts at T4's
  step.
- Tests:
  - integration tests with `enforce_csrf_checks=True`: login, a wrong password,
    logout by POST (GET does not log out), sign-up with and without allergies,
    a duplicate username, "My allergies" requiring login and changing only
    your own record, and an external `next`;
  - e2e tests: sign up → return to the page → header shows the username → log
    out.

### T4 — UC-07 health warning (needs T2, T3)

- The checkout review gets a "Continue" control that leads to the warning.
  Not logged in → the login page, then back to the warning.
- The warning page is built from the cart:
  - total sugar in grams (sum of quantity × sugar per 100 g; each bag counts as
    100 g, so say so on the page). Candies with unknown sugar are named, not
    counted as zero;
  - every allergen in the cart, with the candies containing it;
  - allergens that match the customer's own allergies, marked distinctly, and
    not by colour alone.
- Acknowledgment needs a ticked checkbox plus a submit button. It is validated
  server-side, and it cannot be dismissed by accident: no toast and no
  auto-close.
- The acknowledgment is stored in the session together with a fingerprint of
  the cart. Any change to the cart invalidates it.
- An empty cart goes back to the cart page.
- Tests:
  - the sums, unknown sugar and allergy matches, as unit or integration tests;
  - submitting without the tick is refused;
  - a cart change after acknowledging requires acknowledging again;
  - the login requirement;
  - e2e: tick, continue.

### T5 — UC-08 triple confirmation, one page, three controls (needs T4)

- Reachable only with a valid acknowledgment for the current cart; otherwise
  the page redirects to the warning.
- Three distinct controls, each worded differently. Each one is unlocked only
  once the previous is done (Alpine), and **all three are validated
  server-side** on the final POST:
  1. a checkbox: "I have checked my order: 3 items, $12.40";
  2. a text field: "Type the total to confirm", which must equal the total
     shown;
  3. a button: "Place my order".
- The page shows the exact lines, prices and total being confirmed, and stores
  that snapshot (per-line price and quantity, plus the total) in the session.
  T6 compares against it.
- Declining or leaving at any step changes nothing, and the cart is kept.
- Until T6 lands, a valid final POST shows "Confirmed. Ordering is not built
  yet." T6 replaces that.
- Tests:
  - each missing or wrong control is refused server-side, even when the other
    two are right;
  - a wrong typed total is refused;
  - no valid acknowledgment → redirect;
  - a cart change → back to the warning;
  - e2e: the controls unlock in order and the page submits.

### T6 — Orders without payment (UC-05 steps 4 and 7; data-model §3.6–3.7) (needs T5)

- `Order`: user (required), status (`pending`, `paid`, `cancelled`,
  `fulfilled`; only `pending` is ever set tonight), `total_amount`,
  `warning_acknowledged_at`, `purchase_confirmed_at`, `created_at`, and
  `paid_at` (null).
- `OrderItem`: order, candy (`on_delete=PROTECT`), quantity, `unit_price`,
  `subtotal`.
- On the valid final POST from T5, inside one `transaction.atomic()`:
  1. lock the cart's candies with `select_for_update()`;
  2. re-check each one: still published, stock covers the quantity, and the
     price equals the confirmed snapshot (UC-05 step 4);
  3. anything changed → stop with nothing written. Name the affected items,
     keep the cart, and return to the cart page (ext. 4a);
  4. otherwise create the Order and its OrderItems with price snapshots, and
     reduce stock.
- After the commit: clear the cart and the session acknowledgment and
  confirmation, then redirect to "Order #N received. Payment isn't connected
  yet, so nothing has been charged."
- The receipt page shows only the logged-in owner's order. Another user's order
  number gives 404.
- Submitting twice creates one order: the second submit finds an empty cart
  and redirects.
- Admin: Order with inline OrderItems, read-only.
- Tests:
  - a successful order: rows, snapshots, stock reduced, cart cleared;
  - a stock change, a price change and an unpublished candy each stop the order
    with nothing written;
  - a double submit gives one order;
  - another user's receipt gives 404;
  - e2e through the whole flow: cart → review → login → warning → three
    controls → receipt.

### T7 — Slug URLs and unique names (data-model §3.3)

- First check the dev database for duplicate names. If any exist, **stop the
  task**. Record the duplicates in `questions.md` and do not rename rows.
- Migrations, in this order:
  1. add `slug = SlugField(null=True)`;
  2. a data migration that fills the slug with `slugify(name)`;
  3. make the slug unique and not null, and `name` unique.
- `seed_candy` and the admin (`prepopulated_fields`) set the slug.
- The detail page moves to `/candy/<slug>/`. `/candy/<int:pk>/` redirects with
  301 for a published candy. An unpublished or deleted candy gets the existing
  unavailable response, without a redirect, so its existence is not revealed.
- `candy_link.html` and the popup's `hx-get` use the slug. The cart and stepper
  POST endpoints keep using `pk`.
- Tests: the slug page, the 301 from the old URL, the unavailable candy under
  both URL forms, duplicate names rejected by the database, and existing
  tests updated rather than weakened.

### T8 — Theme toggle can return to the system setting (night-2026-09-16 Q3)

- In `theme.js`: when the click results in the same theme the system already
  uses, remove the stored choice and the `data-theme` attribute instead of
  storing them.
- e2e with emulated `prefers-color-scheme`, both ways:
  - toggle away from the system theme → the choice is stored and survives a
    reload;
  - toggle back → nothing is stored, and a later change of the system scheme is
    followed again.
- `aria-pressed` stays correct.

### T9 — Correct outdated records, propose ADR 0008 (night-2026-09-16 Q2, Q4)

- Correct only these sentences, quoting each change in `progress.md`:
  - `docs/adr/0001-frontend.md`: "no CSS exists yet";
  - `docs/adr/0006-frontend-htmx-alpine.md`: "no CSS of any kind exists yet";
  - `docs/adr/0005-testing.md`: "`tests/e2e/` exists but is still empty";
  - `.claude/skills/night-run/SKILL.md` §9: the premise that no CSS exists.
    Fix the false statements only. Leave §9's rules as they are.
- Write `docs/adr/0008-…` using `0000-adr-template.md`, with status
  **`proposed`**. It covers one hand-written stylesheet, custom-property light
  and dark themes, and `theme.js`, drawing on night-2026-09-16 `decisions.md`
  D6 and D7 and the code as it now stands.
- Proof: grep shows none of the quoted sentences remain, and `adr_guards.py`
  exits 0.

### T10a — SRI hashes on the CDN scripts (night-2026-09-16 Q7)

- Change each `<script src>` to its fully resolved, versioned file URL (e.g.
  `…/htmx.org@2.0.3/dist/htmx.min.js`), so the hash always refers to one fixed
  file. Then add `integrity="sha384-…" crossorigin="anonymous"`.
- The hashes come from the granted fetch only, using Python's `hashlib`, or
  `curl` plus `openssl`.
- Tests:
  - a unit or integration test that every external `<script>` in `base.html`
    has `integrity` and `crossorigin`;
  - the existing e2e suite still passes. That is the proof both scripts still
    load, but add an explicit e2e check that `window.htmx` and `window.Alpine`
    are defined.

### T10b — Coverage floor of 95% (night-2026-09-16 Q8)

- Last of the requested tasks, so it measures tonight's final code.
- Add `--cov-fail-under=95` to `COV_ARGS` in `scripts/dev.py`, and update the
  comment there and ADR 0005's mention of a missing target. CI runs
  `dev.py test`, so the floor applies there too.
- If coverage is below 95%, write the missing tests within this task. **Never
  set a lower number.**
- Proof: `dev.py test` passes. Temporarily raising the floor to 100 locally
  makes it fail. Do not commit that change.

## Exploration (after T1–T10b)

Starts only when every task above is complete, parked or abandoned, the run
branch is green and clean, and it is before **2026-09-18 07:15**.

**No cap on count.** The limits are 07:15, the budget (§8.6) and the quality
bar below.

1. **Survey.** Read the code and tests, and write `findings.md` in this
   directory. Each finding has: a category, `file:line` evidence, why it
   matters, the command that will prove the fix, a size estimate, and a rank.
   Commit the survey as its own task.
2. **Build from the top.** Each finding becomes a task T11, T12, … Append it
   under `## Discretionary (added by the run)` below, with the finding it comes
   from. It gets its own branch, reviewer and commit, like any other task.
3. **Re-rank after each task**, because the code has changed. Remove findings a
   previous task already fixed.
4. **Stop** at 07:15, or when no remaining finding meets the bar.

**Allowed categories:**

- **Bugs.** Wrong behaviour, shown by a test that fails before the fix.
- **Test gaps.** Existing behaviour without a test (the `term-missing` lines).
- **Accessibility.** Measurable defects: missing labels or accessible names,
  lost focus, tap targets under 44×44, contrast under 4.5:1.
- **Docs, dead code, queries.**
  - documentation that contradicts the code;
  - unused or duplicated code, removed with the tests still green;
  - excess database queries, proven with a query-count assertion
    (`django_assert_num_queries`).

**The bar.** Every change has proof that fails before the fix and passes
after, or for documentation, the quoted contradiction. A finding without that
is logged in `findings.md` and not built.

**Not allowed in exploration:**

- migrations: a finding that needs one goes to `questions.md`;
- new packages;
- new features or behaviour changes a customer would notice, except fixing a
  bug;
- changed URLs;
- visual redesign or restyling;
- edits to `docs/requirements.md`, `docs/data-model.md` or any ADR;
- edits to `.claude/`;
- product decisions: those go to `questions.md`.

## Last — Morning report (§7)

In addition to §7:

- the requirements §5 open issues this plan settled: authentication timing,
  guest checkout, warning content, confirmation layout, and alternative login
  methods for launch;
- `findings.md` findings that were logged but not built, and why.

## Discretionary (added by the run)

The exploration phase's survey is `findings.md`; the tasks it produced, in the
order they were built:

### T11 — The survey itself (`findings.md`)

### T12 — F1: customer-specific pages must not be cached
Acceptance: `Cache-Control` contains `no-store` on the cart, cart panel,
checkout, warning, confirmation, receipt and allergies pages; a control
failing without the decorator.

