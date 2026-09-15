# Plan — night-2026-09-15

## Objective

Give the catalog a real-browser test suite, then build the candy detail page
(UC-03) and the flaw disclosure it carries (UC-06).

Source of truth for acceptance: [`docs/requirements.md`](../../requirements.md)
§4 and [`docs/data-model.md`](../../data-model.md) §3.4. The run request elided
the acceptance criteria for tasks 2 and 3 ("Acceptance: ..."), so they are taken
from the use cases themselves — see `questions.md` Q1.

## Non-goals (stated by the request)

- styling
- authentication
- payment

## Additional scope exclusions (derived, see `questions.md`)

- `is_published` on the Candy model — UC-01 step 2 and UC-03 extension 2a both
  reference publication state that the model does not have (Q2).
- `slug` URLs — the detail route uses `<int:pk>`, matching the existing
  add-to-cart route (Q3).
- Admin registration for the Site Administrator half of UC-06 step 1 (Q4).
- The `CandyProduct` → `Candy` rename and the rest of the data-model gap table.

## Tasks

### Task 1 — `tests/e2e/` stands up, covering UC-01 and add-to-cart

`tests/e2e/` exists and is empty. `pytest-playwright` is in `requirements.txt`
and chromium 151.0.7922.34 is installed. `pytest-django`'s `live_server` fixture
pulls in `transactional_db` automatically (`pytest_django/fixtures.py:641`), so
tests need no `django_db` marker.

Acceptance:

- A real browser loads the catalog and sees candy created by the test.
- The catalog shows an explicit empty state when nothing is published
  (UC-01 extension 2a). **The template has no `{% empty %}` today**, so this
  task implements it as well as tests it.
- Clicking "Add to cart" in a real browser swaps the button to its "Added!"
  state — the htmx round trip, with CSRF enforced the way a browser enforces it.
  This is the check `django.test.Client` cannot make.

### Task 2 — UC-03 candy detail page

Acceptance, from UC-03:

- A detail route renders the item's name, description and price (step 2; the
  flaw is task 3).
- The catalog links to it, so "Customer selects a Candy item" is reachable
  (step 1).
- The page offers a route back to the catalog and an add-to-cart control
  (step 3), reusing `shop/templates/shop/partials/cart_button.html`.
- A deleted or nonexistent item does not render (extension 2a) — 404 via
  `get_object_or_404`, matching `add_to_shoppingcart`. See Q2 for the gap
  between that and the "no longer available" copy the extension describes.

`CandyProduct` has no `description` field; `docs/data-model.md` §3.4 lists it as
target-but-missing. This task adds it — an additive, non-destructive migration —
and updates that gap table.

### Task 3 — UC-06 flaw disclosure

Acceptance, from UC-06:

- 3a: the detail view renders the flaw alongside the description, labelled as a
  flaw rather than shown as unmarked prose (step 3). Covered e2e.
- 3b, separate commit: the flaw cannot be silently omitted **at the data-model
  level, not only in the form** (UC-06's Constraint, and `data-model.md` §5).
  `flaw` is already NOT NULL, so the remaining hole is the empty string. A
  `CheckConstraint` closes it.

3b is split out because the request scoped task 3 to "the detail page"; it is
separable if a reviewer judges it out of scope.

## Verification strategy

Per task, before its commit: `python scripts/dev.py test`, `python scripts/dev.py
lint` diffed against `lint-baseline.txt`, `python scripts/adr_guards.py`. Any
task touching `shop/models.py` re-checks `manage.py makemigrations --check`.
The `reviewer` subagent reviews each non-trivial diff before it is committed.
