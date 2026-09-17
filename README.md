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

Styling is one hand-written stylesheet, `shop/static/shop/site.css`, with light
and dark themes that follow the system setting and a toggle to override it;
no CSS framework or build step. CI runs the ADR guards and the test suite on every
push and pull request to `master` and `dev` ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Running it

Requires Python 3.13 and a PostgreSQL 17 server.

```sh
pip install -r requirements.txt
cp .env.example .env          # then fill in DJANGO_SECRET_KEY and DATABASE_URL

# Start your PostgreSQL cluster first -- scripts/dev.py does not start it.
# For a portable install, e.g.:
#   pg_ctl start -D "%USERPROFILE%\Binaries\pgsql\data" -l "%USERPROFILE%\Binaries\pgsql\server.log"
createdb -U postgres questionable_candy
python scripts/dev.py run             # http://127.0.0.1:8000/
```

`dev.py` applies migrations itself before every task, so no separate
`manage.py migrate` step is needed.

To fill an empty catalog with the shop's candy, pictures included:

```sh
python manage.py seed_candy
```

It is safe to run again: it creates only candy that is missing, and on candy
that exists it fills in empty fields without overwriting anything.

There is no SQLite fallback — a missing `DATABASE_URL` fails at startup by
design. See [ADR 0004](docs/adr/0004-database.md).

## Tasks

`scripts/dev.py` is the task runner (`dev.cmd` wraps it on Windows):

| Task                                        | Does                                       |
| ------------------------------------------- | ------------------------------------------ |
| `run`                                       | Start the dev server                       |
| `lint`                                      | pylint; errors fail, the rest is advisory  |
| `lint:workflows`                            | actionlint + shellcheck + pyflakes         |
| `test`                                      | Whole suite, with coverage                 |
| `test:unit`, `test:int`, `test:e2e`         | Run one suite                              |

Every task runs `makemigrations` and `migrate` first, so the database always
matches the models. No task starts or stops PostgreSQL — the cluster must
already be accepting connections. The `lint` tasks are the exception: they read source, so
they need no database and run with the cluster down.

Verification is three commands, plus a fourth when workflows are involved, run separately:

```sh
python scripts/dev.py test        # migrations + full suite + coverage
python scripts/dev.py lint        # pylint; needs `pip install -r requirements-dev.txt`
python scripts/dev.py lint:workflows  # only when .github/workflows/ changed or a workflow failed
python scripts/adr_guards.py      # ADR guards; no database, no dependencies
```

Together these are what `AGENTS.md` §13 and `CLAUDE.md` §9 mean by verification.
There is no type checker, formatter or build step. CI additionally runs
`makemigrations --check`, which `dev.py` deliberately does not — `dev.py` writes
a missing migration rather than failing on it.

### Lint

`pylint` with `pylint-django`, configured in [`.pylintrc`](.pylintrc) and pinned
in [`requirements-dev.txt`](requirements-dev.txt). **Errors fail the build;
warnings, refactors and conventions are reported but do not.** Generated
migrations are excluded. The plugin calls `django.setup()`, so `DATABASE_URL`
and `DJANGO_SECRET_KEY` must be set — no database is contacted, the URL is only
parsed.

### Workflow lint

`lint:workflows` runs [actionlint](https://github.com/rhysd/actionlint) over
`.github/workflows/`, with [shellcheck](https://github.com/koalaman/shellcheck)
for the shell in `run:` steps and [pyflakes](https://pypi.org/project/pyflakes/)
for `shell: python` steps. They are standalone tools, not Python requirements,
so `pip install` does not provide them, and CI does not run them. The task looks
for each on `PATH`, then under `%USERPROFILE%\Binaries\`:

```text
Binaries\actionlint\actionlint.exe        release zip (checksums file published)
Binaries\shellcheck\shellcheck.exe        release zip
Binaries\pyflakes\Scripts\pyflakes.exe    python -m venv Binaries\pyflakes, then pip install pyflakes
```

Run it when a change touches `.github/workflows/`, or when a workflow run has
failed. Other changes don't need it. If any of the three is missing it exits 2 without running: actionlint alone
silently skips a rule whose tool it cannot find and still reports clean.

### ADR guards

Two decisions are enforced rather than merely recorded. `python scripts/adr_guards.py`
fails if
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
- [ADR 0007 — Custom user model](docs/adr/0007-custom-user-model.md)

New decisions start from [the ADR template](docs/adr/0000-adr-template.md).

## Known open items

- Media storage for candy pictures is undecided — [ADR 0004](docs/adr/0004-database.md)
- No login method is currently a *Must have*, while placing an order is — [requirements §5](docs/requirements.md)
- `shop.Candy` is a partial implementation of the target `Candy` entity — [data model §3.3](docs/data-model.md)
