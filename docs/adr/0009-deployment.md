---
status: "accepted"
date: "2026-10-28"
decision-makers: "Martin Larsson"
---

# 0009. Deploying on Render's free web service, with the database on Neon

## Context and Problem Statement

The shop had never been deployed: no WSGI server in `requirements.txt`, no
`STATIC_ROOT`, nothing to serve static files with `DEBUG` off, and django-axes
keyed on `REMOTE_ADDR`, which behind any proxy is the proxy's. The settings for
HTTPS, HSTS and secure cookies were already driven by the environment (the
2026-10-25 audit, S1), but nothing checked them. The budget is zero: the host
and the database must both be free, with no card on file. Where does it run,
and what does the code need for it?

## Decision Drivers

- Free, permanently, for both the web process and the database.
- PostgreSQL, not SQLite: `ArrayField` and `select_for_update` are relied on,
  and [ADR 0004](0004-database.md) runs PostgreSQL everywhere.
- A long-running Python process: Django with `psycopg` holding TCP connections.
- No new runtime platform knowledge in the code beyond what a setting can name.
- An existing Neon project (another of the owner's apps) must not be affected.

## Considered Options

- Render free web service + a new Neon project
- Vercel (serverless Python) + Neon
- PythonAnywhere free tier
- Render free web service + Render's free PostgreSQL

## Decision Outcome

Chosen option: "Render free web service + a new Neon project", because it is
the only combination found that is free without a card, runs Django as an
ordinary long-running process, and keeps a database that does not expire.
Neon's free limits (100 compute-hours and 0.5 GB per project) apply per
project, so a separate project leaves the other app's quota alone.

What the code needed for it, and has:

- **`gunicorn`** as the WSGI server (`render.yaml`'s start command), and
  **WhiteNoise** to serve `STATIC_ROOT`. With `DEBUG` off, static files get
  content-hashed, compressed copies (`CompressedManifestStaticFilesStorage`);
  `collectstatic` runs in the build. WhiteNoise is installed only with `DEBUG`
  off: with it on, Django serves the apps' static files itself.
- **A candy's `image` path must name a shipped static file**, checked in the
  candy admin form. With hashed names, `{% static %}` raises for a file that
  does not exist, so one mistyped path would make every page showing that
  candy a 500 in production, and nowhere else.
- **`RENDER_EXTERNAL_HOSTNAME`** joins `ALLOWED_HOSTS`: Render sets it to the
  service's `onrender.com` host, which is also what its health checks send.
- **The visitor's address for django-axes** comes from the header named by
  `DJANGO_CLIENT_IP_HEADER` (`mysite/client_ip.py`), set to `CF-Connecting-IP`
  in `render.yaml`. Cloudflare, in front of every Render public web service,
  overwrites that header; `X-Forwarded-For` is appended to, so its first entry
  is whatever the visitor sent. Unset, `REMOTE_ADDR` is used, which is the only
  safe reading when there is no proxy to overwrite the header.
- **HSTS covers subdomains**; **preload stays off**, with `security.W021`
  silenced, because the preload list takes only a registrable domain and
  `onrender.com` is shared.
- **Migrations run in the build command**: the free plan has no pre-deploy
  command, and no shell or one-off jobs. `createsuperuser` and `seed_candy` are
  therefore run from a developer's machine against the Neon database
  (README, "Deploying").
- **Python is pinned** by `.python-version` (3.13, as CI uses); Render's own
  default had moved to 3.14.

### Confirmation

- CI's Lint job runs `manage.py check --deploy --fail-level WARNING` with the
  production values `render.yaml` sets, so a change that weakens a deploy
  setting fails the build. It does not read `render.yaml`; the two lists are
  kept in step by hand, and the step says so.
- `tests/unit/test_settings.py` loads `settings.py` under controlled
  environments: the Render host joins `ALLOWED_HOSTS`, HSTS covers subdomains
  only while on, the client-IP header is used only when configured, WhiteNoise
  and hashed static names apply only with `DEBUG` off.
- `tests/integration/test_static_files.py` runs `collectstatic` with the
  production storage and fetches the hashed `site.css` through WhiteNoise.
- `tests/integration/test_login_throttling.py` shows two visitors behind the
  same proxy locked separately, and a forged `CF-Connecting-IP` ignored when no
  header is configured.
- **Not verified by anything here:** the deploy itself. Render and Neon run
  only on their own platforms; the first deploy is the check.

## Pros and Cons of the Options

### Render free web service + a new Neon project

- Good, because both are free without a card, and neither expires.
- Good, because Render runs a normal `gunicorn` process, so nothing about the
  app changes shape; `.env.example` already carried a Neon connection string,
  and `settings.py` already sets `conn_health_checks` for its pooler.
- Neutral, because a separate Neon project leaves the existing one untouched.
- Bad, because a free service sleeps after 15 minutes without traffic and the
  next request waits about a minute while it starts.
- Bad, because there is no shell and no pre-deploy step: migrations run at
  build time, before the new code is live, and admin tasks run from a laptop.
- Bad, because `requirements.lock` holds the test and lint tools too, so the
  build installs them; a runtime-only lock would trim it.

### Vercel (serverless Python) + Neon

- Good, because it is free for non-commercial use and has no idle sleep.
- Bad, because Django runs as a function per request, with cold starts on any
  request and static files to be routed separately.
- Bad, because it changes how the app is shaped for one host.

### PythonAnywhere free tier

- Good, because it is built for Python web apps and is always on.
- Bad, because it offers no PostgreSQL, and its free accounts restrict outbound
  connections, so an external database is not reachable either.

### Render free web service + Render's free PostgreSQL

- Good, because both would live on one platform.
- Bad, because Render deletes a free database 30 days after it is created.

## More Information

- `render.yaml` (the Blueprint), `.python-version`, `mysite/settings.py`
  ("HTTPS transport", "Login throttling", "Static files"), and README,
  "Deploying".
- Render: [Django on Render](https://render.com/docs/deploy-django),
  [free instances](https://render.com/docs/free),
  [Blueprint spec](https://render.com/docs/blueprint-spec),
  [health checks](https://render.com/docs/health-checks). Neon:
  [plans](https://neon.com/docs/introduction/plans).
- **Revisit** when: a custom domain is added (`ALLOWED_HOSTS`, and preload
  becomes possible); traffic or the database outgrows a free tier; payments are
  connected (they will need a webhook endpoint and a real mail backend); or the
  cold start becomes unacceptable.
