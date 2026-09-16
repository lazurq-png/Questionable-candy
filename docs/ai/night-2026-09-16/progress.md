# Progress — night-2026-09-16

## Session 1

### Preflight

- **Run type:** new. The only prior run, `night-2026-09-15`, has its morning
  report written.
- **Clock:** 2026-09-16 14:38 (machine clock; system zone confirmed
  `W. Europe Standard Time`). Deadline 08:00 on 2026-09-17.
- **Budget at session start:** 14,996,435 tokens. This session started ~17h
  before the deadline, so it reserves 10% (floor 60k) for a handoff (§8.6)
  unless it is still running after 07:30.
- **Database:** `pg_isready` exit 0.
- **Drift:** `makemigrations --check --dry-run --noinput` exit 0, "No changes
  detected".
- **Remote:** `origin` reachable; `git ls-remote --heads origin
  "night-2026-09-16*"` returned nothing.
- **Branch:** `night-2026-09-16` cut from `dev` @ `7681607`.
- **Pre-existing uncommitted changes:** none.
- **Baseline:**
  - `python scripts/adr_guards.py` exit 0 — "ok: no DRF, 5 test packages".
  - `python scripts/dev.py lint` exit 0 — **9.35/10**; full report in
    `lint-baseline.txt`.
  - `python scripts/dev.py test` exit 0 — **37 passed**, coverage 92%.
- **Candy rows in the dev database** (not in the repository; T2 seeds them):

  | id | name | description | flavor | price | stock | flaw |
  | -- | ---- | ----------- | ------ | ----- | ----- | ---- |
  | 1 | Sour Bricks | *(empty)* | sour | 12.50 | 10 | Chips a tooth on contact. |
  | 2 | Hollow Humbug | *(empty)* | mint | 9.00 | 3 | Entirely hollow inside. |

### T1 — Publication (UC-01 step 2, UC-03 ext. 2a) — complete

- **Branch:** `night-2026-09-16-t1-publication`. Clock at start 14:40; budget
  14,963,774.
- **Changed:**
  - `Candy.is_published` (default True), migration `0005`, and a `published()`
    queryset method used by the catalog, the detail page and add-to-cart.
  - `candy_unavailable.html`: "no longer available" plus a link to the catalog,
    status 404, for unpublished and deleted alike (decisions.md D1).
  - `data-model.md` §3.3 gap table: `is_published` moved from Missing to Present.
  - Answers night-2026-09-15 Q2 ("publication state is not modelled").
- **Tests added:** unit (default True; `published()` filter), integration
  (deleted and unpublished detail pages, catalog hides unpublished, unpublished
  cannot be added to the cart), e2e (hidden from the catalog, old link explains
  and leads back). The existing 404 test was replaced by the deleted-item test,
  which asserts the same status plus the new message and link.
- **Negative control:** with `published()` returning everything, 4 of the new
  tests failed; restored.
- **Verification:**
  - `python scripts/dev.py test` exit 0 — 43 passed, coverage 93%; `0005`
    applied to the dev database.
  - `python scripts/dev.py lint` exit 0 — 9.41/10; no messages beyond the
    baseline (the two new docstring warnings were fixed).
  - `python scripts/adr_guards.py` exit 0.
  - `makemigrations --check --dry-run --noinput` exit 0.
  - `lint:workflows` not run: no workflow changed.
- **Review:** reviewer subagent approved, no findings. Two observations, both
  already planned: a stale catalog page's add-to-cart silently 404s for a
  since-unpublished item (T3), and Candy has no admin yet (T4).

### T2 — Candy images and 20 new candies — complete

- **Branch:** `night-2026-09-16-t2-candy-images`. Clock at start 14:46; budget
  14,945,614.
- **Changed:**
  - `Candy.image` (`CharField(max_length=200, blank=True, default="")`),
    migration `0006`.
  - `python manage.py seed_candy` (`shop/management/commands/seed_candy.py`):
    22 candies, the two dev-database rows with their existing values plus 20
    new ones. Matches by name; fills only empty text fields.
  - 23 SVGs in `shop/static/shop/candy/` (22 candies + `placeholder.svg`),
    410–611 bytes each, one shared frame. Checked by eye on a rendered contact
    sheet; the green apple belt's overlay was toned down after that look.
  - Catalog and detail pages render `<img alt="{{ candy.name }}">` via
    `{% static %}`, falling back to the placeholder; the image sits outside the
    catalog link so the link's accessible name is unchanged.
  - README documents the seed command; `data-model.md` §3.3 and ADR 0004 record
    `image` as interim, pending the media-storage decision.
- **Tests added:**
  - Unit: every SVG parsed and scanned (no script, foreignObject, style,
    animate or set elements; no `on*` attributes; no non-fragment href or
    `url(`), each has `viewBox`, `role="img"`, a title and is ≤ 4 KB; placeholder
    exists; every seeded image resolves through staticfiles; no orphan SVGs;
    seeded names unique; flaws and descriptions non-blank.
  - Integration: seeding creates all 22; seeding twice creates nothing; an
    edited price and flaw survive a re-seed; an existing row gets only its
    empty fields filled.
  - e2e: catalog and detail images load (`complete` and `naturalWidth > 0`),
    and blank `image` gets the placeholder.
- **Negative controls:**
  - A planted `ONLOAD` attribute failed the scan (and the orphan test).
  - After the reviewer's finding, each of `fill="url(https://…)"`,
    `<style>@import url(…)`, and `<set attributeName="href">` failed the scan.
  - A seed that overwrote price and text fields failed both overwrite tests.
  - All restored.
- **Dev database:** `seed_candy` → "20 created, 2 filled in, 0 unchanged"; run
  again → "0 created, 0 filled in, 22 unchanged". Sour Bricks and Hollow Humbug
  kept price, stock and flaw; both gained a description and image. 22 rows, none
  without an image.
- **Verification:**
  - `python scripts/dev.py test` exit 0 — 121 passed, coverage 94%
    (`seed_candy.py` 100%); `0006` applied to the dev database.
  - `python scripts/dev.py lint` exit 0 — 9.53/10, no messages beyond the
    baseline (new docstring warnings and a mixed-line-ending warning fixed).
  - `python scripts/adr_guards.py` exit 0.
  - `makemigrations --check --dry-run --noinput` exit 0.
  - `lint:workflows` not run: no workflow changed.
- **Review:** reviewer subagent approved with two low findings, both acted on
  before committing:
  1. The SVG scan missed `url()`, `<style>` and `<animate>/<set>`; hardened, with
     a negative control for each.
  2. `image` had been written into the *target* Candy table and ADR 0004 still
     said no image field existed; moved to the gap table as interim, ADR
     sentence updated.

### T3 — Cart (UC-04) — complete

- **Branch:** `night-2026-09-16-t3-cart`. Clock at start 14:57; budget
  14,892,363.
- **Changed:**
  - `shop/cart.py`: the session cart's rules (decisions.md D3):
    - only published candy can be in the cart;
    - quantities are capped at stock;
    - entries deleted, unpublished or sold out since they were added are
      dropped or capped when the cart is viewed, with a notice;
    - corrupt session data is ignored.
  - `shop/forms.py`: `QuantityForm` validates the posted quantity.
  - Views and URLs: `shoppingcart/` (page), `shoppingcart/<pk>/update/`,
    `shoppingcart/<pk>/remove/`. POST only, CSRF enforced. htmx gets the cart
    partial; a plain form post redirects back with its notice (works without JS).
  - Add-to-cart:
    - refuses over-stock, out-of-stock and no-longer-available candy with 200
      and a message (D4);
    - the catalog shows a disabled "Out of stock" button;
    - the header cart count updates out of band.
  - `base.html`: `<header>`/`<nav>` with the cart link, `<main>`, and one
    persistent live region, filled out of band (D5).
  - `shop.context_processors.shoppingcart` in settings; ADR 0002's cart note
    updated.
- **Tests added:**
  - Integration (24, CSRF enforced, token from a real page): add within stock,
    over stock, out of stock; catalog out-of-stock button; cart lines, quantities,
    line totals and total; empty cart; set, cap, and five invalid quantities;
    update for a candy not in the cart; update after a sell-out; update after
    unpublishing (reported once); remove to empty with count 0; stale unpublished
    and deleted entries; stock lowered since; no-JS redirect with notice; 403
    without token; 405 on GET; corrupt session.
  - Plus a deleted-candy add test in `test_views.py`; T1's unpublished-add test
    now asserts 200 + message + unchanged session instead of 404 (D4).
  - e2e (5): add updates the header and fills the cart; quantity change updates
    totals, keeps focus on Update, caps at stock with the message visible and in
    the live region; remove to the empty state; refused add of the last one
    (message and live region); out-of-stock catalog button.
- **Negative controls:**
  - Disabling the cap failed 2 tests.
  - Disabling the add's stock check failed 1.
  - Disabling stale cleanup failed 1.
  - Removing the Update button's id failed the focus assertion.
  - All restored byte-for-byte.
- **Verification:**
  - `python scripts/dev.py test` exit 0 — 151 passed, coverage 96%
    (`cart.py`, `forms.py`, `views.py`, `context_processors.py` 100%).
  - `python scripts/dev.py lint` exit 0 — 9.72/10, no messages beyond the
    baseline; two baseline messages fixed along the way.
  - `python scripts/adr_guards.py` exit 0.
  - `makemigrations --check --dry-run --noinput` exit 0 (no model change).
  - `lint:workflows` not run: no workflow changed.
- **Review:** reviewer approved with four low findings, all acted on:
  1. A stale add did nothing visible; it now answers 200 with a message, and the
     double notice on update is gone.
  2. Announcements came from freshly swapped regions; replaced by one persistent
     live region, and focus is kept after Update.
  3. Hand-parsed input in `cart.py`; moved to `QuantityForm`, D3 recorded.
  4. One e2e test lacked `assert_page_is_fully_rendered`; added.

  Second review of the fixes: approved, no new defects, the test status change
  judged legitimate.
- **Remaining, known:** after Remove, keyboard focus falls back to the page
  (there is no button left to return to). Fixing it needs JavaScript or
  restructuring the swap, neither in this task's bounds. Whether a screen reader
  actually speaks the live region is unverified; only its text change is tested.

### T4 — Flaw on the admin side (UC-06 steps 1–2, ext. 2a) — complete

- **Branch:** `night-2026-09-16-t4-admin-flaw`. Clock at start 15:13; budget
  14,836,148.
- **Changed:** `shop/admin.py` registers `Candy`:
  - `CandyAdminForm` replaces the generic "This field is required." on `flaw`
    with a prompt that says why (`FLAW_REQUIRED`), and adds help text.
  - `CandyAdmin` lists name, price, stock and publication, filters by
    publication, searches name and flaw, and puts `flaw` second in the form.
  - The `candy_flaw_is_not_blank` database constraint still guards every
    non-form path.
  - Answers night-2026-09-15 Q4.
- **Tests added:**
  - Integration (`admin_client`): create with a flaw saves; a new candy with a
    flaw of `""`, `"   "` or `"\t\n"` is refused with the prompt and nothing
    saved; editing a flaw to blank is refused and keeps the old flaw; the
    changelist shows the publication column.
  - e2e: logs in through the real admin login form (CSRF enforced), a
    whitespace flaw is refused with the prompt visible, then a real flaw saves.
- **Negative controls:**
  - Without the custom error message, 4 integration tests failed.
  - Without `is_published` in `list_display`, the tightened changelist test
    failed.
  - Both restored.
- **Verification:**
  - `python scripts/dev.py test` exit 0 — 158 passed, coverage 97%
    (`shop/admin.py` 100%).
  - `python scripts/dev.py lint` exit 0 — no messages beyond the baseline.
  - `python scripts/adr_guards.py` exit 0.
  - `makemigrations --check --dry-run --noinput` exit 0.
  - `lint:workflows` not run: no workflow changed.
- **Review:** reviewer approved with one low finding: the changelist assertion
  matched the list filter's links too. Fixed and negative-controlled as above.

### T5 — Professional interface, light and dark themes (UC-01) — complete

**Built and measured, not reviewed by a person.** Nothing here says the pages
look good; that needs a human looking at the screenshots below.

- **Branch:** `night-2026-09-16-t5-interface-themes`. Clock at start 15:20;
  budget 14,821,220.
- **a. Research** (15:20–15:25, read-only): all Django storefront templates
  found need Bootstrap, Tailwind or a JS build. Pico CSS (MIT, plain CSS) chosen
  as the visual reference and re-implemented; no code copied (decisions.md D6).
- **b. Before screenshots:** `screenshots/before/` — catalog, detail, cart,
  empty cart, no-longer-available, at 375px and 1280px (10 JPEGs).
- **c. CSS:** `shop/static/shop/site.css`, hand-written:
  - custom properties for both themes, mobile-first;
  - catalog card grid, two across on phones;
  - detail page with a flaw callout;
  - cart lines, notices, empty states, sticky header.
  - Templates gained classes only, plus the additions listed in D7; nothing
    with a `data-testid`, role or heading moved.
- **d. Theme** (D7):
  - CSS follows `prefers-color-scheme` when nothing is stored.
  - `theme.js` toggle: a real button named "Dark theme", `aria-pressed`,
    `data-theme` on `<html>`, localStorage.
  - An inline `<head>` script applies a stored choice before paint.
  - The button is hidden without JS; icon-only on phones.
  - README's "No CSS has been written yet" corrected.
- **e. Tests** (`tests/e2e/test_theme.py`, 11):
  - The four measurable checks on the empty catalog, catalog, catalog after
    adding, detail, empty cart, cart with a notice, and no-longer-available, at
    375px:
    - no horizontal overflow;
    - the header on one row;
    - buttons, inputs and every link in the header and `main` ≥ 44×44;
    - text contrast ≥ 4.5:1 against the composited painted background;
    - fully rendered.
  - Those checks run for the system light and dark themes and for a stored
    override in each direction.
  - Theme behaviour: the system decides with nothing stored; an OS switch
    applies live; the toggle overrides and survives a reload both ways; the
    head script applies a stored choice even with `theme.js` blocked (and the
    toggle stays hidden); the icon is not part of the button's name.
  - The contrast checker reports a page with nothing painted behind the text.
- **f. After screenshots:** `screenshots/after/`, both themes, both widths (20
  JPEGs, retaken after the last CSS change).
- **g.** No ADR written; raised as Q2. Also raised: Q3 (no "back to system"
  control), Q4 (ADRs 0001 and 0006 and night-run §9 still say no CSS exists).
- **Negative controls:** each restored byte-for-byte afterwards.
  - Muted text at 1.37:1 failed contrast.
  - `--tap: 2rem` failed tap targets (139×40).
  - A 30rem card failed overflow (121px).
  - No painted background failed.
  - Allowing wrap failed the header check (3 rows).
  - The card name without its tap box failed ("Taffy" 138×25).
  - Low contrast in only the toggle-set dark copy failed (1.30:1).
  - A positive control that passed — hiding the phone label with `nowrap`
    kept — showed the label was not the cause of the wrap; the control was
    redone against the real cause.
- **Found by the tests during the task:**
  - `.theme-toggle`'s `display` overrode `[hidden]`, showing a dead button
    without JS.
  - The CSS glyph leaked into the button's accessible name.
  - The phone header wrapped "Cart (" / "0)".
  - All fixed.
- **Verification:**
  - `python scripts/dev.py test` exit 0 — 169 passed, coverage 97%.
  - `python scripts/dev.py lint` exit 0 — 9.77/10, no messages beyond the
    baseline (two new refactor messages from a six-argument test were fixed).
  - `python scripts/adr_guards.py` exit 0.
  - `makemigrations --check --dry-run --noinput` exit 0.
  - `lint:workflows` not run: no workflow changed.
- **Review:** the reviewer requested changes:
  1. **Medium:** body links (candy names, cart names, back links) measured
     about 24px high, and the tap check skipped them.
  2. **Low:** the phone icon margin rule was overridden.
  3. **Low:** the toggle-set theme was never measured.
  4. **Low:** the empty catalog was never measured.
  5. **Low:** no test of the checker's transparent-background refusal.

  All five fixed and negative-controlled where testable. The re-review
  approved, with one new low finding (a test picked "Add to cart" by position
  in an unordered catalog), fixed by selecting within the candy's card.
- **Not verifiable here:**
  - How it looks: taste, hierarchy, whether the flaw reads as a warning.
  - Whether a screen reader speaks the toggle state as intended.
  - Rendering in browsers other than Chromium.
  - Whether the `content: "..." / ""` alt syntax is honoured in Firefox
    versions that predate it (they would show the glyph's name).
- **Noticed for later:** `candy_list` has no ordering, so catalog order is
  whatever PostgreSQL returns.

### T6 — Enforce ADR 0002 and ADR 0004 — complete (derived)

- **Branch:** `night-2026-09-16-t6-enforce-adrs`. Clock at start 15:48; budget
  14,701,425.
- **Source:** ADR 0002 §Confirmation ("Nothing enforces this decision") and ADR
  0004 §Confirmation ("nothing checks the version of PostgreSQL"); README's
  false "`tests/e2e/` is empty" open item. `plan.md` gained the derived-task
  list (T6–T9) and what was logged instead of built.
- **Changed:**
  - `tests/unit/test_middleware.py`: six middleware present, and
    `SessionMiddleware` before authentication and messages.
  - `tests/integration/test_database_engine.py`: the test database is
    PostgreSQL, version ≥ 17.
  - ADR 0002 and 0004 confirmation sections now name exactly what is enforced
    and what is not.
  - README open item removed.
  - Questions Q5–Q8 logged: out-of-scope UC-07 fields, HTTPS redirect/HSTS,
    SRI for CDN scripts, coverage threshold.
- **Negative controls:**
  - With `CsrfViewMiddleware` removed from settings, the presence test failed.
  - With the minimum at 99, the version test failed (170002 < 990000).
  - Both restored.
- **Verification:**
  - `python scripts/dev.py test` exit 0 — 173 passed, coverage 97%.
  - `python scripts/dev.py lint` exit 0 — 9.78/10, no messages beyond the
    baseline (a trailing-newline warning fixed).
  - `python scripts/adr_guards.py` exit 0.
  - `makemigrations --check --dry-run --noinput` exit 0.
  - `lint:workflows` not run: no workflow changed.
- **Review:** reviewer approved with two low wording findings, both acted on:
  1. ADR 0004's new text implied the app itself is prevented from using
     another engine; reworded to "only the suite catches it".
  2. ADR 0002's text did not match the test; it now names the six middleware.
     A "security middleware first" test was removed, as ADR 0002 never chose
     that rule.

  The reviewer also spotted ADR 0005's stale "e2e is empty" line, added to Q4.
