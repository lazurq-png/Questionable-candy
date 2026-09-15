# Questionable Candy

A candy ordering website — a professional storefront with a dash of satire, where
every product is required to disclose a significant flaw and checkout
triple-confirms that you really do want to buy candy.

## Status

Early. A Django project runs, with one app (`shop`) serving a catalog page and a
session-backed cart. Most of what the specification describes — accounts, orders,
payment, the health warning and the triple-confirmation gate — is not built yet.
[`docs/data-model.md`](docs/data-model.md) §3 marks which entities exist.

The specification documents are drafts: requirements at version 0.3, data model
at 0.2.

## Stack

| Layer         | Choice                                                    |
| ------------- | --------------------------------------------------------- |
| Backend       | Django 6.1 monolith, server-rendered (MVT, no API layer)   |
| Frontend      | Django Templates + htmx + Alpine.js via CDN, no build step |
| Auth          | Django built-in session authentication                     |
| Database      | PostgreSQL                                                 |
| Tests         | pytest + pytest-django, factory_boy, pytest-cov, pytest-playwright |

No CSS has been written yet, and there is no CI.

## Running it

Requires Python 3.13 and a PostgreSQL 17 server.

```sh
pip install -r requirements.txt
cp .env.example .env          # then fill in DJANGO_SECRET_KEY and DATABASE_URL

python scripts/dev.py db:start        # starts a local PostgreSQL cluster
createdb -U postgres questionable_candy
python manage.py migrate
python scripts/dev.py run             # http://127.0.0.1:8000/
```

There is no SQLite fallback — a missing `DATABASE_URL` fails at startup by
design. See [ADR 0004](docs/adr/0004-database.md).

## Tasks

`scripts/dev.py` is the task runner (`dev.cmd` wraps it on Windows):

| Task                            | Does                                                  |
| ------------------------------- | ----------------------------------------------------- |
| `run`                           | Generate + apply migrations, then start the server     |
| `validate`                      | The full verification sequence — see below             |
| `test`, `test:unit`, `test:integration`, `test:e2e` | Run a suite              |
| `migrations`, `migrations:check`| Generate migrations / fail if any are missing          |
| `db:start`, `db:stop`, `db:status` | Drive the local PostgreSQL cluster                  |

`python scripts/dev.py validate` (also `scripts/validate` / `scripts/validate.cmd`)
runs Django's system checks, fails on migration drift, enforces the ADR guards
described below, and runs the suite with coverage. It is what `AGENTS.md` §13 and
`CLAUDE.md` §9 mean by verification.

Set `PGSQL_HOME` if your PostgreSQL lives somewhere other than the default the
script assumes.

### ADR guards

Two decisions are enforced rather than merely recorded. `validate` fails if
`djangorestframework` appears in `requirements.txt` ([ADR 0003](docs/adr/0003-backend.md)
defers it) or if the test stack exceeds five packages ([ADR 0005](docs/adr/0005-testing.md)
budgets 3–5). Everything else in `docs/adr/` is unenforced, and each ADR's
Confirmation section says so plainly.

## Documentation

- [Requirements specification](docs/requirements.md) — use cases in Cockburn fully-dressed format
- [Data model](docs/data-model.md) — entity-relationship model, with implementation status per entity

### Architecture decision records

- [ADR 0001 — Frontend stack](docs/adr/0001-frontend.md) — *superseded in part by 0006*
- [ADR 0002 — Middleware: authentication, session and cart handling](docs/adr/0002-middleware.md)
- [ADR 0003 — Backend architecture](docs/adr/0003-backend.md)
- [ADR 0004 — Database engine](docs/adr/0004-database.md)
- [ADR 0005 — Test frameworks](docs/adr/0005-testing.md)
- [ADR 0006 — htmx and Alpine.js](docs/adr/0006-frontend-htmx-alpine.md)

New decisions start from [the ADR template](docs/adr/0000-adr-template.md).

## Known open items

- Media storage for candy pictures is undecided — [ADR 0004](docs/adr/0004-database.md)
- No login method is currently a *Must have*, while placing an order is — [requirements §5](docs/requirements.md)
- `shop.CandyProduct` is a partial implementation of the target `Candy` entity — [data model §3.4](docs/data-model.md)
- `tests/e2e/` is empty; Playwright is installed and unblocked, but no browser test has been written yet — [ADR 0006](docs/adr/0006-frontend-htmx-alpine.md)
