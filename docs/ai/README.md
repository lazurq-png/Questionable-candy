# `docs/ai/` — durable agent task state

Working state for agent runs that outlive a single conversation. This is the
artifact a human reads afterwards to find out what happened and why.

`.claude/docs/ai-workflow.md` §11 describes the convention; this file is the
concrete layout for this repository.

## Layout

One directory per run, named after the run's branch:

```text
docs/ai/
└── <branch-name>/            e.g. night-2026-09-15/
    ├── plan.md               objective, scope, task list, non-goals
    ├── progress.md           per-task: status, commit, verification evidence
    ├── decisions.md          choices made and why — including rejected options
    ├── questions.md          parked ambiguities awaiting a human answer
    └── lint-baseline.txt     pylint output captured before any work started
```

A supervised task that spans many files or sessions may use the same layout
under its own branch name. Most supervised work needs none of this.

The `night-*` directories come from unattended runs, driven by a night-run
skill that was removed in `21cd14d` (`git show 21cd14d^:.claude/skills/night-run/SKILL.md`
to read it). Such a run worked on several branches — one per task, plus its
integration branch `night-<YYYY-MM-DD>` — but kept **one** directory, named
after the integration branch. Each task committed its updates to these files on
its own branch, and they reached the run branch when that task merged. Keep
that shape for any run of this kind: the point of this record is that a reader
finds the whole run in one place, not one directory per task branch.

## What each file is for

**plan.md** — written before any code changes. The objective, the ordered task
list, what is explicitly out of scope, and the acceptance criteria for each task.
If the run is interrupted, this is what lets the next agent resume without
re-deriving the goal.

For an unattended run, a **human** wrote `plan.md` beforehand, in
`docs/ai/night-<YYYY-MM-DD>/`, dated the day the run started. The run read the
plan and never edited it; with no plan there, it stopped without doing
anything.

**progress.md** — appended as work completes. For each task: what changed, the
commit SHA, the exact verification commands run and their real outcome, and any
remaining risk. Never record a verification that was not observed — an entry
claiming a passing suite that never ran is worse than an empty file, because it
will be believed.

**decisions.md** — implementation and architectural choices with consequences.
Record the alternatives considered and why they lost. A choice that was obvious
does not belong here.

**lint-baseline.txt** — the raw `python scripts/dev.py lint` report from before
the first code change. Its purpose is to be diffed: the lint gate only fails on
errors, so warnings introduced during a run are invisible without something to
compare against. The unattended runs wrote one before their first change; a
supervised task needs it only if it expects to churn a lot of code.

**questions.md** — the queue for a human. Each entry states the ambiguity, the
options, a recommendation, and what was done in the meantime. The unattended
runs parked questions here rather than stopping (`AGENTS.md` §15).

## Lifecycle

These files are committed alongside the work they describe, on the same branch.
When the branch merges, the record merges with it — the reasoning stays attached
to the diff it explains.

Delete a run directory once its branch is merged and the decisions worth keeping
have moved somewhere durable: an ADR under `docs/adr/`, a rule in
`.claude/rules/`, or the code itself. This directory is a staging area for
knowledge, not its final home.
