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
├── skills/              reusable procedures invoked as slash commands (e.g. /code-review)
├── docs/                 supporting human-readable process docs — workflow narrative,
│                          a task-request template, and ready-to-paste prompt patterns
├── scripts/validate.example   copy to scripts/validate and fill in this repo's real
│                                format/lint/typecheck/test/build commands
└── settings.example.json       copy to settings.json and adjust permissions/hooks
```

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

### Code review

`.claude/skills/code-review/SKILL.md` is an adversarial-review checklist (correctness,
security, data integrity, compatibility, concurrency, error handling, tests,
performance) — invoke it with `/code-review` or by asking Claude to review the current
diff.

## Setting this up in a new repo

1. Copy `AGENTS.md`, `CLAUDE.md`, and this `.claude/` folder into the repo root.
2. Copy `.claude/scripts/validate.example` to `scripts/validate` and fill in the
   real commands — this is what `AGENTS.md` §13 and `CLAUDE.md` §9 expect agents
   to be able to run for "verification."
3. Copy `.claude/settings.example.json` to `.claude/settings.json` only if you
   want to pre-approve specific commands/permissions; otherwise omit it and let
   the extension prompt as usual.
4. Trim `.claude/rules/*.md` and `.claude/docs/*.md` down to what the project
   actually needs — delete the domains that don't apply (e.g. `database.md` for
   a repo with no persistence layer).
5. Update the curated list in `CLAUDE.md`'s "Start With Repository Context"
   section if you remove or rename any rule file.
6. Commit all of it — `CLAUDE.md`/`AGENTS.md` are meant to be checked into the
   repo so every contributor's agent sees the same contract, the same way a
   project's `CLAUDE.md` already works in this machine's other repos.
