# `.claude/` — Claude Code Steering Documents

This directory is what the Claude Code extension (VS Code) and CLI read when working in this repository. Copy this whole folder, plus the top-level `AGENTS.md` and `CLAUDE.md`, into a new project's root to bootstrap the same operating model there.

## How the pieces fit together

```text
AGENTS.md              engineering contract — architecture, testing, security, scope,
                        completion standards. Always relevant.
CLAUDE.md               Claude Code operating model — always loaded by the extension/CLI
.claude/
├── rules/              domain reference docs — NOT auto-loaded; CLAUDE.md tells the
│                        agent which one to open for a given task
├── skills/              reusable procedures invoked as slash commands
│                        (/code-review, /night-run)
├── docs/                 supporting human-readable process docs — workflow narrative,
│                          a task-request template, and ready-to-paste prompt patterns
└── settings.example.json       copy to settings.json and adjust permissions/hooks
                                 (not yet done here — settings.json does not exist)
```

This repository has **no single validation entry point.** `scripts/validate`,
`scripts/validate.cmd` and the `dev.py validate` task all existed once and were
removed; anything still telling you to run them is stale. Verification is two
commands, run separately:

```text
python scripts/dev.py test        # migrations + full suite + coverage
python scripts/adr_guards.py      # ADR 0003 / 0005 guards, no deps, seconds
```

`scripts/dev.py` is the task runner for everything else (`run`, `test:unit`,
`test:int`, `test:e2e`). Every task runs `makemigrations` and `migrate` first,
and none of them start PostgreSQL — the cluster must already be up.

There is no type checker, linter, formatter or build step here. CI
(`.github/workflows/ci.yml`) runs the ADR guards and the suite on push to
`master`/`dev`, plus a `makemigrations --check` drift gate that `dev.py`
deliberately omits.

### Why rules aren't auto-loaded

Only `CLAUDE.md` (and nested per-directory `CLAUDE.md` files, which *are* scoped by
location) load automatically. There's no built-in mechanism that opens a file based on
a glob match against whatever's being edited, so the rules in `.claude/rules/` are
reference material Claude opens on demand — `CLAUDE.md` §2 lists which file to read for
which kind of task (frontend, backend, database, testing, debugging, architecture,
review, security-review).

If a real project has stable directory boundaries (e.g. `src/frontend/`,
`src/backend/`), prefer dropping the matching rule file into a nested `CLAUDE.md`
there instead — Claude Code loads those automatically based on which files are being
touched, which scopes guidance by location more precisely than a flat `rules/` folder.

### Unattended operation

`.claude/skills/night-run/SKILL.md` is the protocol for running with no human
available — preflight, branch and commit cadence, durable state under
`docs/ai/<branch>/`, forbidden operations, and stop conditions. It is invoked
(`/night-run`) rather than auto-loaded, so it costs nothing during ordinary
supervised work. Unattended sessions run with permission prompts bypassed, which
means its guardrails are honoured by instruction, not enforced by the harness.

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
3. Copy `.claude/settings.example.json` to `.claude/settings.json` only if you
   want to pre-approve specific commands/permissions; otherwise omit it and let
   the extension prompt as usual. Note that a `deny` list there does **not**
   protect an unattended run started with permissions bypassed — in that mode
   nothing in `settings.json` is consulted, which is why `night-run`'s forbidden
   operations are written as instructions instead.
4. Trim `.claude/rules/*.md` and `.claude/docs/*.md` down to what the project
   actually needs — delete the domains that don't apply (e.g. `database.md` for
   a repo with no persistence layer).
5. Update the curated list in `CLAUDE.md`'s "Start With Repository Context"
   section if you remove or rename any rule file.
6. Rewrite `.claude/skills/night-run/SKILL.md`'s **Preflight** section for the
   new project. Everything else in that skill is portable; the preflight is not
   — it names this repository's PostgreSQL cluster, paths and commands.
7. Commit all of it — `CLAUDE.md`/`AGENTS.md` are meant to be checked into the
   repo so every contributor's agent sees the same contract, the same way a
   project's `CLAUDE.md` already works in this machine's other repos.
