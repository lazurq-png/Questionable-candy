---
name: night-run
description: Protocol for running unattended, with no human available to answer questions — overnight or long autonomous sessions. Defines preflight, branch and commit cadence, durable state, forbidden operations, and stop conditions. Use when starting an unsupervised run, or when a session discovers mid-flight that nobody is there.
---

# Unattended Run

This is how this repository is worked on when nobody is watching.

Everything in `AGENTS.md` and `CLAUDE.md` still applies. This document changes
only what *cannot* work without a human: asking questions, looking at a page,
and knowing when to stop.

## Read this first

An unattended session runs with permission prompts bypassed. Nothing in
`.claude/settings.json` is consulted — a `deny` entry there will not stop
anything, because the harness never asks. **Every guardrail below is honoured
because you choose to honour it.** There is no second line of defence and no one
to catch a mistake before morning.

Work accordingly: prefer the reversible action, commit early so there is always a
known-good point to return to, and when a step feels like it needs permission,
that is the signal to log it rather than the signal to proceed.

---

## 1. Preflight

Run these in order, before touching any code. If a step fails in a way the step
does not tell you how to recover from, stop the run and write why to
`docs/ai/<branch>/progress.md`.

### 1.1 Database

Every `scripts/dev.py` task begins with `makemigrations` and `migrate`, so a
cluster that is down fails *all* verification, including `test:unit`. `dev.py`
no longer starts it — the `db:start`/`db:stop` tasks were removed.

```bash
"%USERPROFILE%\Binaries\pgsql\bin\pg_isready" -h localhost -p 5432
```

Branch on the **exit code**, never on the message text — this cluster's messages
are localised and are not in English:

| Code | Meaning | Action |
| ---- | ------- | ------ |
| 0 | accepting connections | continue |
| 1 | rejecting (starting up / shutting down) | wait 5s and retry, up to 3 times |
| 2 | no response — not running | start it, below |
| 3 | no attempt made (bad invocation) | stop the run; the command itself is wrong |

To start it:

```bash
"%USERPROFILE%\Binaries\pgsql\bin\pg_ctl" start -D "%USERPROFILE%\Binaries\pgsql\data" -l "%USERPROFILE%\Binaries\pgsql\server.log"
```

Then re-check `pg_isready` until it returns 0. If it has not within ~30s, read
the tail of `server.log`, record it, and stop the run.

Starting the cluster is the **only** environment repair permitted unattended. Do
not install packages, create databases, modify `pg_hba.conf`, edit `.env`, or
alter anything else about the machine. If the database exists but is empty or
wrong, that is a stop, not a fix.

### 1.2 Migration drift

`dev.py` *writes* missing migrations rather than failing on them, so an
unexpected migration file can appear without anyone deciding it should. Record
the starting state:

```bash
python manage.py makemigrations --check --dry-run --noinput
```

Exit 0 means models and migrations agree. Non-zero means drift already exists —
note it in `progress.md` as pre-existing, so a migration appearing later is not
misattributed to your work.

### 1.3 Baseline

```bash
python scripts/adr_guards.py
python scripts/dev.py test
```

Both must pass before any new work begins. Without a green baseline, every
"passed" reported afterwards is meaningless.

**If the baseline is red, repairing it is task #1.** Fix it on its own commit,
with regression coverage where appropriate, and reach green before starting the
work you were actually asked to do — even if that consumes the whole run. Note in
`progress.md` that the requested work did not start, and why. The three-attempt
limit (§6) applies to the baseline repair too; if it holds after three cycles,
stop the run.

### 1.4 Branch and state

```bash
git status                       # nothing mid-conflict or mid-rebase
git checkout -b night-<YYYY-MM-DD>
```

Never run unattended on `master` or `dev`.

Pre-existing uncommitted changes are **not yours**. Leave them alone, carry them
onto the branch untouched, and list them in `progress.md` so the morning diff is
readable. Never `git stash`, `git checkout --` or `git restore` a file you did
not modify in this run.

Then create `docs/ai/night-<YYYY-MM-DD>/` with `plan.md`, `progress.md`,
`decisions.md` and `questions.md` — `docs/ai/README.md` says what each holds.
Write `plan.md` before the first code change.

---

## 2. The task loop

Per task, `CLAUDE.md` §1 is unchanged — explore, plan, implement, verify,
review — with these additions:

1. **Verify before committing, always.** The narrowest relevant suite during
   work; `python scripts/dev.py test` plus `python scripts/adr_guards.py` before
   the commit. Never commit on unrun tests.
2. **UI work needs a browser.** Not `django.test.Client`, which is what let a 403
   through for two commits. Write or extend a Playwright test in `tests/e2e/`
   using `live_server` — see `.claude/rules/frontend.md`.
3. **Review independently.** Before committing a non-trivial task, dispatch the
   `reviewer` subagent (`.claude/agents/reviewer.md`). Give it the task
   description and let it establish the diff itself — do **not** give it your
   implementation reasoning, which is the assumption set it exists to not share.
   Unattended, this is the only review the change will get. Act on its findings
   before committing, or record in `decisions.md` why a finding was not acted
   on. "The reviewer was wrong" is an acceptable entry; omitting the finding is
   not.
4. **Re-check migration drift** after any task touching `shop/models.py`. A
   migration you did not intend to create is a finding, not a side effect.
5. **Commit.** One commit per completed, verified task:

   ```text
   <what changed, imperative, one line>

   <why, and what verification was actually run>

   Unattended run: docs/ai/night-<YYYY-MM-DD>/
   ```

   Plus whatever attribution lines this session has been instructed to add.
   **Never push.** A human decides what reaches a shared branch.
6. **Update `progress.md`** with the commit SHA and the real verification output
   before starting the next task.

Provisional work — anything built on a parked assumption (§4) — goes in its own
commit, prefixed `PROVISIONAL:`, never mixed with settled work.

---

## 3. Forbidden operations

Never, unattended, regardless of how reasonable it seems at the time:

- `git push` in any form, `git push --force` above all
- Rewriting history: `rebase`, `commit --amend`, `reset --hard` onto anything but
  your own uncommitted work from this run
- Discarding or stashing changes you did not make in this run
- Destructive schema operations: dropping or renaming a table or column,
  `migrate <app> zero`, deleting or editing an existing migration file, `flush`,
  `dropdb`
- Touching `.env`, or writing any real credential to any file
- Adding a dependency to `requirements.txt` — `scripts/adr_guards.py` enforces
  ADR 0003 (no DRF) and ADR 0005 (test stack ≤ 5 packages), and changing either
  means superseding an ADR, which is a human decision
- Weakening a test, an assertion, or a security control to make something pass
  (`AGENTS.md` §19)
- Installing software, changing PATH, or modifying anything outside this
  repository — except starting the PostgreSQL cluster per §1.1
- Deleting a file you did not create in this run
- Contacting any external service

**If a task requires one of these, abandon the task.** Revert its partial
changes, and write to `questions.md` what was needed, why the rule blocked it,
and the exact command or diff you would have run, for a human to approve
verbatim. Then move to the next independent task.

Do not route around the rule, and do not implement the parts up to the boundary —
a half-applied schema change is worse than none.

---

## 4. Ambiguity: park and continue

When a requirement has two defensible readings, or an architectural fork appears
that `AGENTS.md` §18 would normally have you stop and ask about:

1. Write to `questions.md`: the question, each option with its consequence, your
   recommendation, and what you did in the meantime.
2. Take the **smallest reversible** interpretation. Prefer the one that is
   cheapest to undo, not the one you think is most likely right.
3. Commit it separately, prefixed `PROVISIONAL:`.
4. Continue with the next independent task.

Do not stop the run, and do not build further work on top of a parked assumption
— if the next task depends on the answer, park that one too and move on.

---

## 5. Task selection

Good unattended tasks are ones whose completion can be *proven* by a command:
behaviour with testable acceptance criteria, bug fixes that start from a failing
test, coverage for existing behaviour, documentation of things the repository can
be read to confirm.

Poor unattended tasks, to be logged for supervised work instead: primarily visual
changes, anything whose acceptance criteria are a matter of taste, exploratory
refactors with no behavioural definition of done, and anything requiring a
decision the repository cannot settle.

---

## 6. Stop conditions

End the run, write the state, and leave the branch as it is:

- **Three consecutive failed verify → repair cycles on one failure.** Revert that
  task, record all three hypotheses and what each eliminated, and move on —
  `.claude/rules/debugging.md` §8. If a *second* task also hits three, stop the
  run entirely: something environmental is wrong.
- **The database cannot be brought up** (§1.1).
- **The baseline cannot be made green** in three attempts (§1.3).
- **The task list is complete.** Stopping early with a clean, documented result
  is a success. Do not invent additional work to fill the night — unrequested
  scope is exactly what `AGENTS.md` §7 exists to prevent, and nobody is awake to
  catch it.

On stopping, always: working tree clean or its state explained, `progress.md`
current, final commit verified.

---

## 7. Morning report

The run's last act is a summary at the top of `progress.md`, committed:

- **Completed** — task, commit SHA, verification actually run
- **Provisional** — what was built on a parked assumption, and which question
- **Abandoned** — task, why, what was needed
- **Questions** — the `questions.md` queue, most consequential first
- **State** — branch name, whether it is green, whether anything is uncommitted

Report only what was observed. `CLAUDE.md` §9 applies with full force here: there
is nobody to catch an overstated result before it is believed and acted on.
"Could not verify X" is a useful sentence; a claimed passing suite that never ran
is a lie the morning will act on.
