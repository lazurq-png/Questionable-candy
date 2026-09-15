# Questions — night-2026-09-15

Parked ambiguities, most consequential first. Each states what was done in the
meantime so the run could continue (`night-run` §4).

---

## Q1. The acceptance criteria for tasks 2 and 3 were elided from the request

**Question.** The run request reads "2. UC-03 candy detail page. Acceptance: ...
3. UC-06 flaw disclosure on the detail page. Acceptance: ...". The criteria
themselves did not survive into the prompt.

**Options.**

- (a) Stop and ask. Costs the whole run; two of three tasks are blocked.
- (b) Take the acceptance criteria from `docs/requirements.md` §4, which
  specifies UC-03 and UC-06 in numbered steps with extensions and constraints.
- (c) Invent criteria.

**Recommendation and what was done.** (b). The use cases are written as
acceptance criteria already, and the request names them by number, so the
elided text is most likely a restatement of them. Every acceptance line in
`plan.md` cites the UC step it comes from, so any divergence from what was
intended is visible rather than buried. (c) was never a candidate.

**If this was wrong:** the tests encode the criteria, so correcting them means
correcting `tests/e2e/test_detail.py` and `tests/integration/test_views.py`
rather than re-reading the implementation.

---

## Q2. Publication state is not modelled, so "published" and "unpublished" are untestable

**Question.** UC-01 step 2 says "System retrieves the **published** Candy
items", and UC-03 extension 2a says "Item **unpublished** or deleted: System
shows 'no longer available' and returns to the catalog".
`shop.CandyProduct` has no `is_published` field — `docs/data-model.md` §3.4
lists it under "Missing" on the target `Candy` entity. So:

- "published items" currently means "all items";
- of extension 2a's two triggers, only *deleted* is representable.

**Options.**

- (a) Add `is_published = BooleanField(default=True)` now. Additive and
  reversible, but it is a data-model change nobody asked for, and the
  data-model doc says the `CandyProduct` → `Candy` fill-out "is a migration, not
  an edit; it has not been scheduled."
- (b) Treat every row as published. The catalog's empty state then means "no
  candy exists at all", which is still UC-01 extension 2a's observable outcome
  for the only case that can occur today.
- (c) Add the field *and* the "no longer available" page, taking a slice of the
  unscheduled migration.

**Recommendation and what was done.** (b) — the smallest reversible reading.
`candy_list` keeps `objects.all()`, and the detail view returns 404 for a
missing item. Adopting (a) later is one additive migration plus a `.filter()`,
and the e2e empty-state test keeps passing either way because it asserts on the
rendered state, not on how the queryset was built.

**Still open for a human:** extension 2a asks for "no longer available" copy and
a return to the catalog; a bare 404 is neither. Doing that properly wants either
a project-level `404.html` or a publication flag with a dedicated view, and both
are larger than this task. `tests/integration/test_views.py` asserts the 404
status, so whichever is chosen has a test to change.

---

## Q3. Detail URLs use the primary key; the data model specifies a slug

**Question.** `docs/data-model.md` §3.4 gives the target `Candy` a `slug`
"used in catalog/detail URLs", and lists it as missing from `CandyProduct`.

**Options.** (a) Add `slug` now — a unique field, so the migration must backfill
existing rows before the uniqueness constraint applies; not a one-liner.
(b) Route on `<int:pk>`.

**Recommendation and what was done.** (b). It matches the existing
`candy/<int:pk>/add-to-shoppingcart/` route, needs no migration, and the switch
to a slug later is a URLconf change plus that backfill — which is work that
belongs with the rest of the `Candy` fill-out, not smuggled into a detail page.

---

## Q4. UC-06 step 1 — the administrator's side — has no interface

**Question.** UC-06 step 1 is "Administrator records a Flaw when creating or
editing a Candy item", and extension 2a is "Saved with no Flaw: System rejects
the save and prompts for one". `shop/admin.py` registers nothing, so there is no
screen on which either happens.

**Options.** (a) Register `CandyProduct` in the admin. One line, but exercising
it needs a superuser and a login — and authentication is a stated non-goal of
this run, so it would ship untested by anything but the suite's own client.
(b) Leave it; implement the model-level guarantee that makes extension 2a true
whatever the interface.

**Recommendation and what was done.** (b). Task 3b's `CheckConstraint` rejects a
blank flaw from *any* save path, which is what UC-06's Constraint asks for
("Required at the data-model level, not only in the form"). Registering the
admin afterwards inherits that rejection for free. Flagged for supervised work
because verifying an admin screen means logging into one.
