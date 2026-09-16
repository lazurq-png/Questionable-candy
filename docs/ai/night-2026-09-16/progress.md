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
