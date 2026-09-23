# `docs/`: index for agents

The files in `docs/` are the canonical record, written for agents. **Read this
index first. Open a full record only when the task touches its decision.** Humans
read [`overview.html`](overview.html) instead: a short plain-language page
derived from these files.

If you change a record, update its row below **and** `overview.html`, then run
`python scripts/adr_guards.py --stamp`. `adr_guards.py` fails in CI while any
record is newer than the page (`overview.sources`). The stamp also copies every
record into the page, whose "Full record" links show them formatted. Never edit
that generated block by hand.

## Decisions (`adr/`)

| ADR | Status | Decision | Constraint on your change | Enforced by |
| --- | ------ | -------- | ------------------------- | ----------- |
| [0001](adr/0001-frontend.md) | partially superseded by 0006 | Django Templates + hand-written CSS | Server-rendered templates only. No SPA, no `package.json`, no Tailwind | nothing |
| [0002](adr/0002-middleware.md) | accepted | Django's built-in session auth; stock middleware | Keep the stock middleware. django-allauth is deferred. Cart state lives in `request.session["shoppingcart"]` (`shop/cart.py`) plus a context processor, not middleware. A changed stored session format needs a read-compat shim | `tests/unit/test_middleware.py`, `tests/unit/test_settings.py` (secure cookies), CSRF test in `tests/integration/test_views.py` |
| [0003](adr/0003-backend.md) | accepted | Django MVT monolith, no API layer | No DRF, no JSON API, no service/repository layer. Logic goes in models and forms, not views | `adr_guards.py` (the DRF dependency only) |
| [0004](adr/0004-database.md) | accepted | PostgreSQL everywhere, via `DATABASE_URL` | No SQLite fallback. `ArrayField` is allowed. Media storage is still **undecided** (`Candy.image` is an interim static path) | settings raise `ImproperlyConfigured`; `tests/integration/test_database_engine.py` (PG ≥ 17) |
| [0005](adr/0005-testing.md) | accepted | pytest-django, pytest-cov, factory_boy, pytest-playwright | Keep the test stack small, but that is a preference, not a cap: add a package when it earns its place. Coverage floor 95% on `dev.py test`. Browser tests in `tests/e2e/` for UI interactions | `--cov-fail-under=95`; nothing counts packages |
| [0006](adr/0006-frontend-htmx-alpine.md) | accepted | htmx + Alpine.js from a CDN, no build step | Interactivity works against HTML responses. CDN scripts keep `sha384` `integrity`. Vendoring is the fallback. No Tailwind | `tests/integration/test_script_integrity.py`, `tests/e2e/test_catalog.py` |
| [0007](adr/0007-custom-user-model.md) | accepted | `accounts.User(AbstractUser)` + `allergies` | Do not change `AUTH_USER_MODEL`. `allergies` is a non-null list of EU-14 keys (`shop/allergens.py`). Which stock fields to drop is open | `tests/unit/test_user_model.py` |
| [0008](adr/0008-hand-written-css-themes.md) | accepted | One stylesheet `shop/static/shop/site.css`; colours as `:root` custom properties; light + dark via `prefers-color-scheme` and `data-theme`; `theme.js` toggle | Do not add a second stylesheet, an external font or a CDN stylesheet. Mobile-first | `tests/e2e/test_theme.py` (overflow, 44×44 targets, 4.5:1 contrast); nothing checks the one-stylesheet rule |

Unattended runs may not write or accept an ADR (`.claude/skills/night-run/SKILL.md` §9.6).

## Requirements ([`requirements.md`](requirements.md))

Use cases UC-01…UC-09 are specified there, with priorities, in Cockburn format. The built state, as of the 2026-09-17 run:

| UC | Feature | State |
| -- | ------- | ----- |
| 01 | Browse catalog | built |
| 02 | Google login | **deferred** (Should have; needs django-allauth, ADR 0002) |
| 03 | Candy detail | built (`/candy/<slug>/`; `/candy/<pk>/` redirects) |
| 04 | Cart | built (session-based, no `ShoppingCart` table) |
| 05 | Order and pay | orders placed as `pending`; **payment not connected**, no processor chosen |
| 06 | Flaw disclosure | built; DB check constraint on non-blank `flaw` |
| 07 | Health warning | built; derived from sugar and allergens in the cart |
| 08 | Triple confirmation | built as three distinct controls on one page |
| 09 | Alternative login | username/password log in and sign up built |

§5 lists the open issues. Several are settled in code but not yet recorded in §5.

## Data model ([`data-model.md`](data-model.md))

A target model, not a description of the code. **`shop/models.py` and
`accounts/models.py` are the truth.** The status table in data-model §3 marks
the gap: User and Order/OrderItem are implemented, Candy is partial (`stock`
not `stock_quantity`, `flaw` is `CharField(200)`, extra `flavor`/`image`),
ShoppingCart/ShoppingCartItem are not started, and SocialAccount is deferred.
The diagram is `erd.png`, with its source in `erd.excalidraw`.

## Agent run state (`ai/`)

Per-run working state. See [`ai/README.md`](ai/README.md). Not summarised on the human page.
