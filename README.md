# Questionable Candy

A candy ordering website — a professional storefront with a dash of satire, where
every product is required to disclose a significant flaw and checkout
triple-confirms that you really do want to buy candy.

## Status

A customer can browse the catalog, read a candy's disclosed flaw, fill a
session-backed cart and place an order. Two apps: `shop` (catalog, cart,
checkout, orders) and `accounts` (a custom user model, sign-up, login, and the
allergies the checkout warning matches against).

Built: the catalog and detail pages (UC-01, UC-03), the cart (UC-04), the flaw
disclosure (UC-06), the health warning (UC-07), the triple confirmation
(UC-08), username/password sign-up and login (UC-09, without the email
verification its step 3 describes), and orders up to — but not including —
payment (UC-05 steps 1-4, and step 7 in part: the order is created and the cart
cleared, but as `pending` and with nothing to track it from).

Also built: a **My orders** page at `/accounts/orders/` listing the signed-in
customer's past orders.

Not built: **payment**, so an order stays `pending` and nothing is ever
charged; and Google sign-in (UC-02).

[`docs/data-model.md`](docs/data-model.md) §3 marks which entities exist.

The specification documents are drafts: requirements at version 0.3, data model
at 0.2.

## Stack

| Layer    | Choice                                                             |
| -------- | ------------------------------------------------------------------ |
| Backend  | Django 6.1 monolith, server-rendered (MVT, no API layer)           |
| Frontend | Django Templates + htmx + Alpine.js via CDN, no build step         |
| Auth     | Django built-in session authentication                             |
| Database | PostgreSQL                                                         |
| Tests    | pytest + pytest-django, factory_boy, pytest-cov, pytest-playwright |

The suite is gated at 95% coverage (`scripts/dev.py`), and `tests/e2e/` drives
a real browser over every customer-facing page.

Styling is one hand-written stylesheet, `shop/static/shop/site.css`, with light
and dark themes that follow the system setting and a toggle to override it;
no CSS framework or build step. CI runs the ADR guards, lint and the test suite
on every pull request to `master` and `dev`, and on every push to `master` and
`dev` ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Running it

Requires Python 3.13 and a PostgreSQL 17 server.

```sh
python -m venv .venv
.venv\Scripts\activate                # macOS/Linux: source .venv/bin/activate
pip install -r requirements.lock
python -m playwright install chromium   # the browser tests/e2e/ drives
cp .env.example .env          # then fill in DJANGO_SECRET_KEY and DATABASE_URL
createdb -h localhost -U postgres questionable_candy
python scripts/dev.py run             # http://127.0.0.1:8000/
```

Any PostgreSQL 17 server works: a system service, Homebrew, a container, or a
hosted one. Point `DATABASE_URL` in `.env` at it:

```sh
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/questionable_candy
```

- Percent-encode special characters in the password: `@` is `%40`, `:` is
  `%3A`, `/` is `%2F`.
- The user needs `CREATEDB`, because the test suite creates and drops its own
  `test_questionable_candy`. To make a role just for this project, run in `psql`:
  `CREATE ROLE candy LOGIN PASSWORD '...' CREATEDB;`, then
  `createdb -h localhost -U candy questionable_candy`.
- `scripts/dev.py` starts a cluster only if it finds one at
  `%USERPROFILE%\Binaries\pgsql`, or at `PGSQL_HOME`. With any other install it
  leaves the server alone, so the server must already be running. To use such a
  cluster, start it once yourself before creating the database:
  `pg_ctl start -D "%USERPROFILE%\Binaries\pgsql\data" -l "%USERPROFILE%\Binaries\pgsql\server.log"`.

`dev.py` applies migrations itself before every task, so no separate
`manage.py migrate` step is needed.

`requirements.lock` pins every package, with hashes, so a laptop and CI install
the same versions. `requirements.txt` and `requirements-dev.txt` stay the
inputs; after changing either, regenerate it, then install it again and rerun
`playwright install chromium` — a new Playwright needs its matching browser:

```sh
pip install pip-tools
pip-compile --generate-hashes --strip-extras -o requirements.lock requirements.txt requirements-dev.txt
```

CI's test job runs in Playwright's container image, which carries the browser
for one Playwright version. If the lock's `playwright==` changes, update the
image tag, its digest and `PLAYWRIGHT_IMAGE_VERSION` in
[`ci.yml`](.github/workflows/ci.yml) to match. Until then the job stops at its
"Playwright matches the image" step.

Dependabot bumps the ranges in the two inputs but does not regenerate the lock,
so after merging one of its PRs, run the command above and commit the result.

To fill an empty catalog with the shop's candy, pictures included:

```sh
python manage.py seed_candy
```

It is safe to run again: it creates only candy that is missing, and on candy
that exists it fills in empty fields without overwriting anything.

There is no SQLite fallback — a missing `DATABASE_URL` fails at startup by
design. See [ADR 0004](docs/adr/0004-database.md).

## Deploying

The site runs on Render's free web service, with its data in its own Neon
project ([ADR 0009](docs/adr/0009-deployment.md)). [`render.yaml`](render.yaml)
describes the service; Render builds it from `master`, and only once CI has
passed on a commit.

1. **Database.** In Neon, create a **new project** for the shop, in AWS
   Frankfurt (`eu-central-1`), next to the Render service. Keep it separate from
   any other app's project: the free limits are per project, and a second
   database inside another project would share its quota and suspend with it.
   If **New project** is greyed out, the organization you are in is managed by
   Vercel, which creates Neon projects only from its own dashboard: choose
   **Create organization** in Neon's organization switcher and make the project
   there. Copy its **pooled** connection string (Neon labels it
   `DATABASE_URL_POOLED`): the host ends in `-pooler`, and it carries
   `?sslmode=require`. On Render it still goes under the name `DATABASE_URL`.
2. **Service.** In Render, choose **New → Blueprint** and connect this
   repository. Render reads `render.yaml`, generates `DJANGO_SECRET_KEY`, and
   asks once for `DATABASE_URL`: paste the Neon string.
3. **First build.** It installs `requirements.lock`, runs `collectstatic`, and
   runs `migrate` against Neon. The free plan has no pre-deploy step, so
   migrations run in the build, before the new code goes live.
4. **Admin user and candy.** The free plan has no shell either, so run these from
   your own machine, against the Neon database:

   ```sh
   DATABASE_URL='<the Neon string>' python manage.py createsuperuser
   DATABASE_URL='<the Neon string>' python manage.py seed_candy
   ```

   An environment variable wins over `.env`, so these reach Neon, not your local
   database. Use `manage.py`, not `dev.py`, which would also run
   `makemigrations` and `migrate` against it.

Once it is up:

- **It sleeps.** After 15 minutes without a visit, the next request takes about
  a minute while the service starts.
- **Behind Render's proxy**, `render.yaml` turns on `DJANGO_PROXY_SSL_HEADER`, so
  the HTTPS redirect does not loop. It also sets `DJANGO_CLIENT_IP_HEADER=CF-Connecting-IP`,
  so login throttling keys on each visitor's own address rather than the
  proxy's. CI's Lint job runs `manage.py check --deploy --fail-level WARNING`
  with those values. Change one, and change the other to match.
- **No mail is sent.** Nothing in the shop sends any yet; when something does,
  set the `DJANGO_EMAIL_*` variables (`.env.example`).
- **A custom domain** goes in `DJANGO_ALLOWED_HOSTS`. The service's own
  `onrender.com` host is added automatically.
- If `migrate` ever fails on the pooled connection, run it once against Neon's
  direct (non-`-pooler`) string, from your machine as in step 4.

## Tasks

`scripts/dev.py` is the task runner (`dev.cmd` wraps it on Windows):

| Task                                | Does                                      |
| ----------------------------------- | ----------------------------------------- |
| `run`                               | Start the dev server                      |
| `lint`                              | ruff check + format check, then pylint; ruff findings and pylint errors fail |
| `lint:workflows`                    | actionlint + shellcheck + pyflakes        |
| `test`                              | Whole suite, with coverage                |
| `test:unit`, `test:int`, `test:e2e` | Run one suite                             |

Every task runs `makemigrations` and `migrate` first, so the database always
matches the models. Before that, a task starts the local cluster if
`pg_isready` reports it down (never stopping it; skipped under CI or with no
local install). The `lint` tasks are the exception: they read source, so
they need no database and run with the cluster down.

Verification is three commands, plus a fourth when workflows are involved, run separately:

```sh
python scripts/dev.py test        # migrations + full suite + coverage
python scripts/dev.py lint        # ruff + pylint; installed by requirements.lock
python scripts/dev.py lint:workflows  # only when .github/workflows/ changed or a workflow failed
python scripts/adr_guards.py      # ADR guards; no database, no dependencies
```

Together these are what `AGENTS.md` §10 and `CLAUDE.md` §3 mean by verification.
There is no type checker or build step. CI additionally runs
`makemigrations --check`, which `dev.py` deliberately does not — `dev.py` writes
a missing migration rather than failing on it.

### Lint

First `ruff check` and `ruff format --check`, configured in
[`ruff.toml`](ruff.toml): any finding, or any file the formatter would change,
fails. `python -m ruff format` and `python -m ruff check --fix` repair most of
them. [`.git-blame-ignore-revs`](.git-blame-ignore-revs) lists the commit that
first formatted the codebase, so `git blame` can skip it.

Then `pylint` with `pylint-django`, configured in [`.pylintrc`](.pylintrc) and pinned
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

One decision is enforced rather than merely recorded. `python scripts/adr_guards.py`
fails if `djangorestframework` appears in `requirements.txt`
([ADR 0003](docs/adr/0003-backend.md) defers it). It also fails when a record in
`docs/` has changed since [`docs/overview.html`](docs/overview.html), the
plain-language summary, was last brought up to date. Everything else in
`docs/adr/` is unenforced, and each ADR's Confirmation section says so plainly.

## Documentation

- [Requirements specification](docs/requirements.md) — use cases in Cockburn fully-dressed format
- [Data model](docs/data-model.md) — entity-relationship model, with implementation status per entity

### Architecture decision records

- [ADR 0001 — Frontend stack](docs/adr/0001-frontend.md) — _superseded in part by 0006_
- [ADR 0002 — Middleware: authentication, session and cart handling](docs/adr/0002-middleware.md)
- [ADR 0003 — Backend architecture](docs/adr/0003-backend.md)
- [ADR 0004 — Database engine](docs/adr/0004-database.md)
- [ADR 0005 — Test frameworks](docs/adr/0005-testing.md)
- [ADR 0006 — htmx and Alpine.js](docs/adr/0006-frontend-htmx-alpine.md)
- [ADR 0007 — Custom user model](docs/adr/0007-custom-user-model.md)
- [ADR 0008 — Hand-written CSS with light and dark themes](docs/adr/0008-hand-written-css-themes.md)
- [ADR 0009 — Deploying on Render, with the database on Neon](docs/adr/0009-deployment.md)

New decisions start from [the ADR template](docs/adr/0000-adr-template.md).

## Known open items

- Media storage for candy pictures is undecided — [ADR 0004](docs/adr/0004-database.md)
- No login method is currently a _Must have_, while placing an order is — [requirements §5](docs/requirements.md). Sign-up and login exist; the specification has not been updated to say whether they are the launch path
- `shop.Candy` differs from the target `Candy` entity in what it calls `stock`, in the type of `flaw`, and in the extra `flavor` and `image` fields — [data model §3.3](docs/data-model.md)
- Payment is not connected, so `Order.status` never leaves `pending`
