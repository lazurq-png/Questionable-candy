# CLAUDE.md

How Claude Code works in this repository. The engineering contract is
`AGENTS.md`, imported here so it always loads; this file adds only what is
specific to Claude or to this repository, and does not repeat it.

@AGENTS.md

---

## 1. Working loop

**Explore → Plan → Implement → Verify → Review**; when verification fails,
**Repair → Verify → Review**. Match the depth of each step to the risk of the
task: no long plan for a trivial change, no skipped exploration for one that
touches unfamiliar or interconnected code.

## 2. Where to look first

- **Recorded decisions:** `docs/README.md`, one row per ADR. Open a full ADR
  only when the task touches its decision. `docs/overview.html` is the human
  version; do not read it for facts.
- **Domain rules** in `.claude/rules/`, read before implementing in that area:
  - `architecture.md`: boundaries, layering, refactors
  - `frontend.md`: UI, accessibility, state, browser-facing work
  - `backend.md`: APIs, services, validation, errors, transactions
  - `database.md`: schemas, migrations, persistence, data integrity
  - `testing.md`: coverage strategy, flaky tests, definition of done
  - `debugging.md`: evidence-driven failure diagnosis
  - `review.md`: adversarial review of a finished diff
  - `security-review.md`: authn/authz, secrets, payments, external input

  `frontend.md`, `backend.md` and `database.md` carry `paths:` frontmatter and
  load only when matching files are read; the others load at launch. Open any
  rule yourself when the task touches its domain.
- **Nested instructions:** a more specific instruction file in a subdirectory
  governs the files in its scope.

## 3. Verification

In this repository the checks that exist are:

| Check                       | Command                                                     |
| --------------------------- | ----------------------------------------------------------- |
| Targeted tests              | `python scripts/dev.py test:unit` / `test:int` / `test:e2e` |
| Full suite (+ coverage)     | `python scripts/dev.py test`                                |
| Lint                        | `python scripts/dev.py lint`                                |
| Workflow lint (conditional) | `python scripts/dev.py lint:workflows`                      |
| ADR guards                  | `python scripts/adr_guards.py`                              |
| Browser                     | `python scripts/dev.py run`, then open the page             |

Every `dev.py` task runs `makemigrations` and `migrate` first, so the database
always matches the models. Before that, it starts the local cluster
(`~/Binaries/pgsql`, or `PGSQL_HOME`) if `pg_isready` reports it down, and
says so in its output; it never stops it. Under CI, or with no local install,
that step is skipped. The exceptions are the two `lint` tasks, which read
source only and run with the cluster down.

`lint:workflows` is actionlint over `.github/workflows/`, with shellcheck for
the shell in `run:` steps and pyflakes for `shell: python` steps. They are
standalone tools under `%USERPROFILE%\Binaries\`, not Python requirements, and
CI does not run them. Run it **only** when the change touches
`.github/workflows/`, or when a workflow run is known to have failed. Otherwise
skip it and don't list it as verification. It fails with exit 2 if any of the
three is missing rather than running with fewer rules — actionlint on its own
quietly skips a rule whose tool it cannot find and still reports clean.

`lint` runs `ruff check`, `ruff format --check` (`ruff.toml`) and then pylint
with the Django plugin (`.pylintrc`). Any ruff finding, and any file the
formatter would change, fails. `python -m ruff format` and `python -m ruff
check --fix` repair most of them. For pylint, **errors fail; warnings,
refactors and conventions print without failing**, so a clean exit does not
mean an empty report. Read the output; do not report "lint passed" as though it
found nothing.

There is still **no** type checker or build step. Do not claim to have run one.

CI exists as of 2026-09-15 (`.github/workflows/ci.yml`): ADR-guards, lint, and a
test job with a PostgreSQL service and a Playwright browser, so `tests/e2e/`
runs there too. It triggers on pull requests to `master` and `dev`, and on
pushes to `master` and `dev`. It runs on GitHub, not on your machine — you
cannot observe its result from here, so never report a CI run as evidence.
CI also checks migration drift with `makemigrations --check`, which `dev.py`
deliberately does not, and runs `check --deploy --fail-level WARNING` against
the production values in `render.yaml` (ADR 0009).

Browser verification is not interchangeable with the test suite: `django.test.Client`
does not enforce CSRF, so a green suite has already coexisted with a page that
403'd on every interaction. See `.claude/rules/frontend.md`.

Start with the narrowest useful check and widen it with the change's reach.
Never report a result that was not actually observed.

**There is no `scripts/validate` and no `dev.py validate` task.** Both were
removed; `dev.py validate` now exits 2 with `Unknown task`. Verification is the
commands in the table above, run separately.

## 4. Durable task state

Keep what a long task knows in the repository, not only in the conversation:
objective, current understanding, decisions, files changed, remaining work,
verification status, open risks. For a branch, that is `docs/ai/<branch>/` —
`plan.md`, `progress.md`, `decisions.md`, `questions.md` (see
`docs/ai/README.md`), committed on the branch it describes so the reasoning
stays with the diff. Leave enough there that another agent can continue
without redoing the investigation.

## 5. Review and subagents

Before declaring substantial work complete, review the final diff, not just the
edits as they were made: does it solve the request, follow the architecture,
preserve contracts and security boundaries, test what matters, and touch
nothing unrelated?

- `.claude/skills/code-review/` is the adversarial review pass over a diff.
- `.claude/agents/reviewer.md` is the standing independent reviewer: dispatch
  it by name, ideally for any high-risk change. It has no Edit or Write tool,
  follows the `code-review` skill, and knows this repository's recurring
  failure modes.

Use subagents for independent investigation (exploration, test analysis,
security review, isolated research), each with a narrow objective, and
synthesize their results before implementing. Do not delegate tiny tasks. Never
let two agents edit the same files; parallel implementation needs isolated
worktrees. Add further specialized agents only if the task mix justifies them;
a security reviewer is the likeliest next one.

## 6. The `.claude/` directory

```text
.claude/
├── agents/     — specialized subagents dispatched by name (reviewer)
├── rules/      — domain-specific reference docs (see §2); three are path-scoped
├── skills/     — reusable procedural workflows, invoked as slash commands
│                 (code-review)
├── docs/       — supporting human-readable process docs (workflow, task
│                 template, prompt patterns) — not auto-loaded
├── launch.json — the desktop app's preview server: `dev.py run` on port 8000
└── settings.json — shared allow-list (dev.py tests/lint, read-only git) and denies
                    (force/delete push, rm -rf, reading .env); no hooks
```

Keep these complementary to `AGENTS.md`; do not copy the contract into them.
