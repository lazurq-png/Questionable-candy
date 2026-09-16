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
