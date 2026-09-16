# Plan — night-2026-09-16

## Objective

Build the in-scope customer-facing use cases (UC-01, UC-03, UC-04, UC-06) to
completion, give every candy an image and seed 20 new ones, and give the site a
professional interface with light and dark themes. Then keep deriving work from
the documentation, within the same scope.

Source of truth: the run request (reproduced in intent below),
[`docs/requirements.md`](../../requirements.md) §4 and
[`docs/data-model.md`](../../data-model.md) §3.3.

## Scope

In: UC-01 Browse, UC-03 View description, UC-04 Manage cart, UC-06 Disclose flaw.

Out, by the request — and anything existing only to serve them:

- UC-02 (Google login), UC-09 (other login/registration)
- UC-05 (place order and pay), and so UC-07 and UC-08, which are steps inside
  UC-05's checkout
- Order, OrderItem, ShoppingCart and ShoppingCartItem tables; any payment code

A documented task that depends on these is logged in `questions.md` as out of
scope, not parked and not built provisionally.

## Settled by the human (not ambiguities)

1. Candy data via `python manage.py seed_candy` — idempotent, get-or-create by
   name, only fills empty fields on existing rows.
2. The cart stays in `request.session["shoppingcart"]` (ADR 0002).
3. Theme follows `prefers-color-scheme`, with a toggle to override it.
4. Candy images are static SVGs in `shop/static/shop/candy/`, referenced by a
   `CharField(blank=True)` holding the static path; placeholder when blank. No
   ImageField/FileField/MEDIA (ADR 0004 is open on media storage).

## Granted exceptions to night-run

- Read-only web research for task 5 only, ~30 minutes, reference only, no code
  copied in; every candidate recorded in `decisions.md`.
- Task 5 is requested visual work, not §9 discretionary; §9.3 bounds apply
  except that JavaScript is allowed for the theme toggle only.
- After tasks 1–5, derive further tasks from documentation, before any §9 work.

Tech stack, exclusively: Django 6.1 templates; hand-written CSS in
`shop/static/shop/` via `{% static %}`; htmx 2.0.3 and Alpine 3.14.1 via the
existing CDN tags; PostgreSQL. No new packages, CDN resources, external fonts,
Node or build step.

## Tasks

### T1 — Publication (UC-01 step 2, UC-03 ext. 2a)

- `Candy.is_published = BooleanField(default=True)`; existing rows stay visible.
- Catalog lists only published candy.
- Detail page for an unpublished or deleted candy says it is no longer
  available and links back to the catalog; status code chosen and tested.
- Unit test of the filter; integration tests for unpublished and deleted; e2e
  test.

### T2 — Candy images and 20 new candies

- Image-path `CharField(blank=True)` on Candy.
- `seed_candy`: the two dev-database rows (Sour Bricks, Hollow Humbug — values
  recorded in `progress.md`) plus 20 new, uniquely named candies, each with a
  real description, price, stock, flavor and a specific flaw.
- One hand-written SVG per candy plus a placeholder: `viewBox`, `role="img"`,
  `<title>`, small; no `<script>`, `on*`, `<foreignObject>`, external hrefs.
- Tests: SVG safety scan; every seeded image file exists; seeding twice keeps
  the row count and does not overwrite an edited value.
- `<img src alt="{{ candy.name }}">` on catalog and detail; e2e test that
  images load (`naturalWidth > 0`).
- Seed the dev database (for screenshots only).

### T3 — Cart (UC-04)

- Cart page: items, quantities, line totals, overall total.
- Add, change quantity, remove — each validated against stock; cap or reject
  with a visible message (ext. 2a).
- Empty-cart state (ext. 4a).
- Entries whose candy was deleted or unpublished are handled.
- htmx POST with the base.html CSRF header; integration tests with
  `Client(enforce_csrf_checks=True)`; an e2e test per interaction.

### T4 — Flaw on the admin side (UC-06 steps 1–2, ext. 2a)

- Candy registered in the admin; a blank or whitespace-only flaw is rejected
  with a message. Integration test with `admin_client`. Answers
  night-2026-09-15 Q4.

### T5 — Professional interface, light and dark themes (UC-01)

a. Web research; one reference that fits the stack; recorded.
b. Before screenshots, every page, 375px and 1280px.
c. Hand-written CSS with custom properties for both themes, mobile-first;
   classes added, no `data-testid`/role/heading element moved.
d. Theme: CSS follows `prefers-color-scheme` with no stored choice; toggle
   `<button>` with accessible name and `aria-pressed`, sets `data-theme` on
   `<html>`, stores in localStorage; inline head script applies a stored choice
   before paint; override wins until toggled again.
e. e2e: system dark/light honoured with no stored choice; toggle overrides and
   survives reload; both themes: no overflow at 375px, tap targets ≥ 44×44,
   body-text contrast ≥ 4.5:1 against the real painted background; every page
   still fully rendered.
f. After screenshots, both themes, both widths.
g. No accepted ADR; decisions.md + ADR raised in questions.md.

### T6+ — Derived from documentation

Only after T1–T5 are complete, parked or abandoned. Each derived task cites the
document line it comes from, and stays within Scope. Renaming or dropping a
column is forbidden (§3) and goes to `questions.md`; open product decisions are
parked (§4).

### Last — Morning report (§7)

## Derived tasks (added in T6, after T1–T5 completed)

Each is traced to the line it comes from and stays within Scope.

### T6 — Enforce two decisions whose ADRs say nothing checks them

- ADR 0002 §Confirmation: "**Nothing enforces this decision.** `MIDDLEWARE` …
  no test or check asserts that". → Unit test of the middleware stack and the
  order Django requires.
- ADR 0004 §Confirmation: "Not enforced: nothing checks the *version* of
  PostgreSQL". → Integration test: vendor is PostgreSQL, version ≥ 17.
- README "Known open items": "`tests/e2e/` is empty" is false. → Remove it.

### T7 — Keyboard focus after removing a cart line

- `progress.md` T3 "Remaining, known": focus falls back to the page after
  Remove; `.claude/rules/frontend.md` §Accessibility lists focus restoration.
- Without new JavaScript (the grant was for the theme toggle only): htmx
  focuses an `autofocus` element in swapped content.

### T8 — A deterministic catalog order

- UC-01 step 3 renders the published items; the query has no ordering, so
  their order is whatever PostgreSQL returns (found in T5's review).
- Smallest reversible: order by name.

### T9 — Candy timestamps

- `data-model.md` §3.3 gap table, Missing: "timestamps".
- Additive columns are allowed by the run request. Rows that exist get NULL
  (unknown) rather than an invented date.

### Logged, not built

- `sugar_content_g`, `allergens` (data-model §3.3): exist to feed the UC-07
  checkout warning, which is out of scope.
- HTTPS redirect / HSTS (requirements §3): depend on how the site is deployed.
- Subresource integrity for the CDN scripts (ADR 0006): needs fetching from the
  CDN, which the run may not contact.
- A coverage threshold (ADR 0005): "once a target is agreed", by a human.
