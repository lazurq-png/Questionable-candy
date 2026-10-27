# `.claude/` — Claude Code Steering Documents

This directory is what the Claude Code extension (VS Code) and CLI read when working in this repository. Copy this whole folder, plus the top-level `AGENTS.md` and `CLAUDE.md`, into a new project's root to bootstrap the same operating model there.

## How the pieces fit together

```text
AGENTS.md              engineering contract — architecture, testing, security, scope,
                        completion standards. Always relevant.
CLAUDE.md               Claude Code operating model — always loaded by the extension/CLI
.claude/
├── rules/              domain reference docs — frontend/backend/database are
│                        path-scoped (`paths:` frontmatter), the rest load at launch
├── skills/              reusable procedures invoked as slash commands
│                        (/code-review)
├── docs/                 supporting human-readable process docs — workflow narrative,
│                          a task-request template, and ready-to-paste prompt patterns
└── settings.json               shared permissions: allow-list and deny rules, no hooks
```

This repository has **no single validation entry point.** `scripts/validate`,
`scripts/validate.cmd` and the `dev.py validate` task all existed once and were
removed; anything still telling you to run them is stale. Verification is three
commands, plus a fourth when workflows changed, run separately:

```text
python scripts/dev.py test        # migrations + full suite + coverage
python scripts/dev.py lint        # ruff check + format --check, then pylint
python scripts/dev.py lint:workflows  # only if .github/workflows/ changed or a workflow failed
python scripts/adr_guards.py      # ADR 0003 guard, no deps, seconds
```

`scripts/dev.py` is the task runner for everything else (`run`, `test:unit`,
`test:int`, `test:e2e`). Every task runs `makemigrations` and `migrate` first,
starting the local PostgreSQL cluster first if it is down (skipped under CI).
`lint` is the exception: source-only, so it needs no database.

There is no type checker or build step here. Lint is ruff (`ruff.toml`: any
finding or unformatted file fails) followed by pylint with the Django plugin
(`.pylintrc`), gated on the error class only. pylint's warnings print without
failing, so a zero exit is not an empty report.

CI (`.github/workflows/ci.yml`) runs three jobs on push to `master` and `dev`:
the ADR guards, lint, and the suite — plus a `makemigrations
--check` drift gate that `dev.py` deliberately omits.

### How rules load

A rule file in `.claude/rules/` with no `paths:` frontmatter loads at launch, like
`CLAUDE.md`. One with `paths:` loads only when Claude reads a matching file. Here,
`frontend.md`, `backend.md` and `database.md` are path-scoped; the other five load
every session. `CLAUDE.md` §2 lists which file covers which kind of task.

If a real project has stable directory boundaries (e.g. `src/frontend/`,
`src/backend/`), prefer dropping the matching rule file into a nested `CLAUDE.md`
there instead — Claude Code loads those automatically based on which files are being
touched, which scopes guidance by location more precisely than a flat `rules/` folder.

### Code review

`.claude/skills/code-review/SKILL.md` is an adversarial-review checklist (correctness,
security, data integrity, compatibility, concurrency, error handling, tests,
performance) — invoke it with `/code-review` or by asking Claude to review the current
diff.

## Setting this up in a new repo

1. Copy `AGENTS.md`, `CLAUDE.md`, and this `.claude/` folder into the repo root.
2. Give the repo a real verification command and name it in `CLAUDE.md` §9 —
   that table is what `AGENTS.md` §13 expects agents to run for "verification."
   Whether it is one script or two commands matters less than that every stage
   runs a real check. A stage that echoes a heading and prints success without
   checking anything is worse than no stage at all: it manufactures the evidence
   those sections exist to require. (This repo learned that the other way round
   too — a `validate` wrapper was removed and three documents went on citing it
   for weeks.)
3. Adapt `.claude/settings.json` to the new repo: pre-approve the commands
   agents run constantly and deny dangerous ones (force-pushes, `rm -rf`,
   reading `.env`). A `deny` rule is enforced by the harness, unlike a sentence
   in `CLAUDE.md`, so put anything that must never happen there.
4. Trim `.claude/rules/*.md` and `.claude/docs/*.md` down to what the project
   actually needs — delete the domains that don't apply (e.g. `database.md` for
   a repo with no persistence layer).
5. Update the curated list in `CLAUDE.md`'s "Start With Repository Context"
   section if you remove or rename any rule file.
6. Commit all of it — `CLAUDE.md`/`AGENTS.md` are meant to be checked into the
   repo so every contributor's agent sees the same contract, the same way a
   project's `CLAUDE.md` already works in this machine's other repos.
