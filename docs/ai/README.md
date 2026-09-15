# `docs/ai/` — durable agent task state

Working state for agent runs that outlive a single conversation. This is the
artifact a human reads afterwards to find out what happened and why.

`.claude/docs/ai-workflow.md` §11 describes the convention; this file is the
concrete layout for this repository.

## Layout

One directory per run, named after the branch the run works on:

```text
docs/ai/
└── <branch-name>/          e.g. night-2026-09-15/
    ├── plan.md             objective, scope, task list, non-goals
    ├── progress.md         per-task: status, commit, verification evidence
    ├── decisions.md        choices made and why — including rejected options
    └── questions.md        parked ambiguities awaiting a human answer
```

A supervised task that spans many files or sessions may use the same layout
under its own branch name. Most supervised work needs none of this.

## What each file is for

**plan.md** — written before any code changes. The objective, the ordered task
list, what is explicitly out of scope, and the acceptance criteria for each task.
If the run is interrupted, this is what lets the next agent resume without
re-deriving the goal.

**progress.md** — appended as work completes. For each task: what changed, the
commit SHA, the exact verification commands run and their real outcome, and any
remaining risk. Never record a verification that was not observed — an entry
claiming a passing suite that never ran is worse than an empty file, because it
will be believed.

**decisions.md** — implementation and architectural choices with consequences.
Record the alternatives considered and why they lost. A choice that was obvious
does not belong here.

**questions.md** — the queue for a human. Each entry states the ambiguity, the
options, a recommendation, and what was done in the meantime. An unattended run
parks questions here rather than stopping (`AGENTS.md` §18).

## Lifecycle

These files are committed alongside the work they describe, on the same branch.
When the branch merges, the record merges with it — the reasoning stays attached
to the diff it explains.

Delete a run directory once its branch is merged and the decisions worth keeping
have moved somewhere durable: an ADR under `docs/adr/`, a rule in
`.claude/rules/`, or the code itself. This directory is a staging area for
knowledge, not its final home.
