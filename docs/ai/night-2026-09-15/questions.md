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

---

## Q5. Migration `0003` has no in-file guard for existing blank-flaw rows

**Question.** The reviewer's Finding 1: `AddConstraint` compiles to
`ALTER TABLE ... ADD CONSTRAINT ... CHECK ("flaw"::text ~ E'\S')`, which
PostgreSQL validates against every existing row. A row with `flaw = ''` was
legal until this commit — that is exactly what
`test_a_candy_cannot_be_saved_without_a_flaw` proves. On a database holding
one, `migrate` aborts with a Postgres error that names no row.

It is transactional, so nothing is corrupted and the application stays on the
old schema. But the deployment stops, and whoever is looking at it gets no
guidance. The dev database has 2 rows and 0 violations, so a clean local
`migrate` is evidence of nothing — `.claude/rules/database.md` is explicit that
development data does not stand in for production.

**What was needed, and why the rule blocked it.** The legible fix is a
`RunPython` guard ahead of the `AddConstraint`, raising with the offending ids.
`night-run` §3 forbids "deleting or **editing** an existing migration file", and
the reviewer's cheaper alternative — a comment inside `0003` — is the same
edit. The file is one this run generated and has not committed, so the rule's
intent (do not rewrite schema history) arguably does not reach it; that is
exactly the judgement call an unattended run should not be making on its own.

**The diff not applied**, for a human to approve verbatim — inserted into
`shop/migrations/0003_candyproduct_candyproduct_flaw_is_not_blank.py` before
the existing `AddConstraint` operation:

```python
def reject_blank_flaws(apps, schema_editor):
    """Fail with the offending rows rather than with Postgres's bare error."""
    CandyProduct = apps.get_model("shop", "CandyProduct")
    offenders = [
        (c.pk, c.name) for c in CandyProduct.objects.all() if not c.flaw.strip()
    ]
    if offenders:
        raise RuntimeError(
            "These candies have no flaw recorded and must be given one before "
            f"UC-06's constraint can apply: {offenders}. Do not backfill a "
            "placeholder -- a fabricated disclosure is what UC-06 prevents."
        )


operations = [
    migrations.RunPython(reject_blank_flaws, migrations.RunPython.noop),
    migrations.AddConstraint(...),   # unchanged
]
```

**What was done instead.** The precondition and the triage query
(`SELECT id, name FROM shop_candyproduct WHERE flaw !~ '\S';`) are written into
`docs/data-model.md` §3.4, where the rest of the `Candy` gap analysis lives, and
into this run's `progress.md`. That informs a reader; it does not stop a
deployment. **Recommendation: apply the diff above.**

**Not a candidate:** a data migration that writes placeholder flaw text. A
fabricated disclosure is the exact failure UC-06 exists to prevent, so those
rows need a person, not a default.
