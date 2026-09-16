---
name: night-run
description: Protocol for running unattended, with no human available to answer questions — overnight or long autonomous sessions. Defines preflight, a branch per task pushed as each one finishes, durable state, forbidden operations, two deadlines (08:00 Europe/Stockholm and the session budget, whichever comes first) with the morning report reserved for on both, bounded discretionary visual work when the task list runs out, and stop conditions. Use when starting an unsupervised run, or when a session discovers mid-flight that nobody is there.
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

One thing here does reach outside the machine: §2.6 pushes each completed task's
branch, and the run branch with it. That is deliberate and it is narrow — the
run's own branches, never a shared one, never with `--force`. Everything a push
makes permanent, it makes permanent on someone else's machine too, so the gate
is the finished, verified, reviewed task and nothing less.

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

### 1.3 Branches

The run uses **one integration branch plus one branch per task**:

```text
dev                              the base; never committed to
└── night-<YYYY-MM-DD>           the run's integration branch
    ├── night-<YYYY-MM-DD>-t1-<slug>    task 1, cut from the run branch
    ├── night-<YYYY-MM-DD>-t2-<slug>    task 2, cut from it again, after t1 merged
    └── …
```

```bash
git status                       # nothing mid-conflict or mid-rebase
git checkout dev                 # the base, explicitly -- not wherever HEAD was
git checkout -b night-<YYYY-MM-DD>
```

Never run unattended on `master` or `dev`.

**The separator is a hyphen, not a slash, and that is not cosmetic.** Git stores
refs as paths, so `night-2026-09-15` and `night-2026-09-15/t1-detail-page`
cannot both exist — the first is a file where the second needs a directory. The
slash form is the one you will reach for, and it fails on the *second* branch,
after the run branch is already made:

```text
fatal: cannot lock ref 'refs/heads/night-2026-09-15/t1-detail-page':
'refs/heads/night-2026-09-15' exists; cannot create
'refs/heads/night-2026-09-15/t1-detail-page'
```

Task branches are cut in §2 as each task starts, not up front: a task branch cut
before the task before it has merged is cut from the wrong commit.

### 1.4 Remote

Pushing is part of the loop now (§2.6), so establish up front whether it can
work:

```bash
git remote -v                    # is there an origin at all?
git ls-remote --heads origin "night-<YYYY-MM-DD>*"
```

| Result | Action |
| ------ | ------ |
| No remote configured | The run is local-only. Record it in `progress.md` and skip every push; this is not a failure. |
| Remote reachable, no matching branches | Normal. Continue. |
| Remote already has a branch in this run's namespace | **Stop the run.** Either a previous run of the same date is still live or someone else owns that name. Picking a different name unattended risks two agents writing to one namespace. |
| Remote configured but unreachable | Continue local-only, record why. A network problem is not a reason to abandon work you can still do. |

Do not create, delete or fetch anything else on the remote during preflight.

### 1.5 State

Pre-existing uncommitted changes are **not yours**. Leave them alone, carry them
onto the branch untouched, and list them in `progress.md` so the morning diff is
readable. Never `git stash`, `git checkout --` or `git restore` a file you did
not modify in this run.

Then create `docs/ai/night-<YYYY-MM-DD>/` with `plan.md`, `progress.md`,
`decisions.md` and `questions.md` — `docs/ai/README.md` says what each holds.
Write `plan.md` before the first code change.

**One state directory for the whole run**, named after the *run* branch, never
after a task branch. It is committed on each task branch as that task updates
it, and reaches the run branch when the task merges. Splitting it per task would
scatter the record across branches that a reader has to find first.

**Record two starting readings in `progress.md` before the first task**: the
wall clock (§8.1) and the session budget figure the harness reports (§8.6).
The budget thresholds are proportions of where the run started, so without the
starting figure written down there is no denominator — and by the time it
matters, the message that carried it may have been summarised away.

### 1.6 Baseline

```bash
python scripts/adr_guards.py
python scripts/dev.py lint
python scripts/dev.py test
```

All three must pass before any new work begins. Without a green baseline, every
"passed" reported afterwards is meaningless.

`lint` needs one extra step. It exits 0 while still printing warnings — errors
are the only failing class — so its exit code alone tells you nothing about what
it found. Save the report somewhere it can be diffed later:

```bash
python scripts/dev.py lint > docs/ai/<branch>/lint-baseline.txt 2>&1
```

Record the score line (`Your code has been rated at N/10`) in `progress.md`. A
warning you introduced is invisible against a baseline you never read.

**If the baseline is red, repairing it is task #1.** Reach green before starting
the work you were actually asked to do — even if that consumes the whole run.
Note in `progress.md` that the requested work did not start, and why. The
three-attempt limit (§6) applies to the baseline repair too; if it holds after
three cycles, stop the run.

A repair is work, so it runs as a task through §2 like any other, on a branch
`night-<YYYY-MM-DD>-t0-baseline`. Do not repair a red baseline on `dev` — the
rule against working unattended on a shared branch has no exception for fixing
something that was already broken.

This step is last in preflight for two concrete reasons: `lint-baseline.txt` is
written into the directory §1.5 creates, and a repair needs the branch §1.3
creates. Running it earlier leaves its own output with nowhere to go.

---

## 2. The task loop

Per task, `CLAUDE.md` §1 is unchanged — explore, plan, implement, verify,
review — with these additions:

0. **Check the clock, then cut the task's branch**, from the run branch, with
   nothing uncommitted:

   ```bash
   date '+%H:%M'                           # NOT TZ='Europe/Stockholm' -- see §8.1
   git checkout night-<YYYY-MM-DD>
   git status --short                      # must be empty
   git checkout -b night-<YYYY-MM-DD>-t<N>-<slug>
   ```

   This is the only place the clock is read (§8.2). If it is past the cutoff for
   the kind of task you were about to start, do not start it — go to §8.2's row
   for that time instead. Record the reading with the task.

   `<N>` is the task's position in `plan.md`; `<slug>` is two or three words of
   what it does. Cut it **now**, not at the start of the run: it must be based
   on the run branch as the previous task left it, or a task that depends on its
   predecessor is built on a commit that predates it.

   A task that turns out to need a predecessor's work confirms the model rather
   than breaking it — that work is already on the run branch, so it is already
   in this branch's history.

1. **Verify before committing, always.** Run the narrowest relevant suite during
   the work itself; before the commit, `python scripts/dev.py test`,
   `python scripts/dev.py lint` and `python scripts/adr_guards.py` must all
   exit 0. **Never commit on a failing or unrun check** — a pylint error blocks
   a commit exactly as a failing test does.

   Lint then needs the comparison its exit code does not give you: diff its
   output against `lint-baseline.txt` from §1.6. A warning your task introduced
   is either fixed before the commit, or recorded in `decisions.md` with the
   reason it stands. It does not pass unmentioned.

   Warnings are not errors, so do not spend the three-attempt budget (§6) on
   one. A warning you decide not to fix is a decision to write down, not a
   failure to repair.
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
5. **Record, then commit — in that order.** Update `progress.md`,
   `decisions.md` and `questions.md` on the **task** branch *before* staging, so
   the evidence is committed with the diff it describes rather than trailing it.

   The entry carries what changed, the verification actually run and its real
   output, and the branch name. It cannot carry the commit SHA — a commit cannot
   contain its own hash — and it cannot yet carry whether the push succeeded.
   Both belong to the morning report (§7), which is written last and knows them.

   One commit per completed, verified task:

   ```text
   <what changed, imperative, one line>

   <why, and what verification was actually run>

   Unattended run: docs/ai/night-<YYYY-MM-DD>/
   ```

   Plus whatever attribution lines this session has been instructed to add.
   The commit lands on the **task** branch.
6. **Merge and push.** Only once the task is complete, verified green and
   reviewed — the gate is the same one the commit passed, because a push is a
   commit that other people can now see.

   ```bash
   git checkout night-<YYYY-MM-DD>
   git merge --ff-only night-<YYYY-MM-DD>-t<N>-<slug>
   git push --set-upstream origin night-<YYYY-MM-DD>-t<N>-<slug>
   git push origin night-<YYYY-MM-DD>
   ```

   `--ff-only` is the check, not a formality. The task branch was cut from the
   run branch and only this run writes to either, so a fast-forward must be
   possible; if git refuses one, something happened that this protocol does not
   model. **Stop the run** rather than reaching for a merge commit or a rebase.

   The rules on the push itself:

   - **Only branches in this run's own namespace** — `night-<YYYY-MM-DD>` and
     its `-t<N>-` branches. Never `master`, never `dev`, whatever the reason.
     Check the branch name against the namespace before every push; there is no
     second line of defence.
   - **Never `--force`, never `--force-with-lease`**, never `--delete`, never
     `--tags`, never push another branch's ref.
   - **A rejected push is a stop, not a problem to solve.** These branches are
     the run's alone, so a non-fast-forward rejection means something you do not
     understand is writing to them. Do not force, do not pull-and-retry. Record
     it in `progress.md`, stop pushing for the rest of the run, and keep working
     locally — the commits are safe either way.
   - **No pull requests.** Pushing a branch publishes work for a human to look
     at. Opening a PR asks for a merge, and that is their call.
   - **Local-only runs push nothing** and are not lesser for it (§1.4).

   Pushing changes what a mistake costs. A commit that stays local can be
   rewritten; a pushed one is on someone else's machine, and a secret in it is
   disclosed, not merely written. The rules in §3 against credentials in files
   and against touching `.env` stop being hygiene at this point and start being
   the thing that prevents a disclosure.

   **A push starts a check; it is not itself one.** `.github/workflows/ci.yml`
   triggers on `night-**`, so pushing does hand the branch to CI — the ADR
   guards, lint, and the suite including `tests/e2e/` against a real PostgreSQL
   and a real browser.

   You cannot see the result. CI runs on GitHub; this session has no way to
   observe it and must never report one (`CLAUDE.md` §9). So the honest line in
   the morning report is *"pushed; CI will have run on it, result unseen from
   here"* — never "CI passed". If the push itself was rejected or skipped
   (§1.4), say that instead, because then not even CI has looked.

7. **Leave the tree clean.** After the merge the run branch is checked out with
   nothing modified, which is exactly what the next task's step 0 requires.

   **Never commit directly to the run branch.** It moves only by fast-forward
   from a task branch — that is the property that makes `--ff-only` a real
   check rather than a ritual. If something still needs recording at this point
   (a refused push, most likely), it is written into `progress.md` and committed
   by the *next* task, or by the report task if there is no next one.

Provisional work — anything built on a parked assumption (§4) — goes in its own
commit, prefixed `PROVISIONAL:`, never mixed with settled work. Its task branch
is **pushed but not merged** into the run branch: a parked assumption must not
become the base the next task is cut from. Name the branch in `questions.md`
beside the question it depends on.

An **abandoned** task (§3, §6) leaves its branch local, unmerged and unpushed.
Name it in `progress.md` so the work can be found, and move on. Do not delete
it — and do not push it either; a pushed branch reads as an offer, and this one
is a dead end.

---

## 3. Forbidden operations

Never, unattended, regardless of how reasonable it seems at the time:

- `git push --force` or `--force-with-lease`, in any form, for any reason
- `git push` to `master` or `dev`, or to any branch outside this run's own
  `night-<YYYY-MM-DD>` namespace — §2.6 permits exactly that namespace and
  nothing else
- `git push --delete`, pushing tags, or pushing a ref this run did not create
- Opening a pull request. Pushing offers work; a PR asks for a merge
- Rewriting history: `rebase`, `commit --amend`, `reset --hard` onto anything but
  your own uncommitted work from this run — and once a branch is pushed, this is
  no longer only a rule about tidiness, because the old commits are already
  somewhere else
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

**If a task requires one of these, abandon the task.** Write to `questions.md`
what was needed, why the rule blocked it, and the exact command or diff you
would have run, for a human to approve verbatim. Then move to the next
independent task.

Abandoning is cheap now that each task has its own branch, and needs no
`reset --hard`:

```bash
git restore .                    # discard this task's uncommitted work only
git checkout night-<YYYY-MM-DD>  # the branch is simply never merged
```

Anything already committed stays on the abandoned branch, which is the record.
Do not delete it, do not merge it, do not push it (§2.6). `git restore` here is
safe *because* the branch is yours — the rule against restoring files you did
not modify still holds for anything outside this task.

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
3. Commit it separately, prefixed `PROVISIONAL:`, on its own task branch.
4. Push that branch but **do not merge it** into the run branch (§2.6), and name
   it in `questions.md` beside the question it waits on.
5. Continue with the next independent task, cut fresh from the run branch.

Do not stop the run, and do not build further work on top of a parked assumption
— if the next task depends on the answer, park that one too and move on.

Leaving provisional work unmerged is what makes that last rule hold by
construction rather than by memory: the next task is cut from the run branch, so
an assumption that never reached it cannot be inherited by accident.

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

**Visual work is the one bounded exception**, and only once the requested list
is finished — §9 sets out what may be built, the four properties that can
actually be verified, and the much larger set that cannot. It does not overturn
the paragraph above: styling is still a poor unattended task, which is why §9
constrains it so tightly and why its output is reported as measured rather than
reviewed.

---

## 6. Stop conditions

End the run, write the state, and leave the branches as they are — merge nothing
further, push nothing further, delete nothing:

- **Three consecutive failed verify → repair cycles on one failure.** Revert that
  task, record all three hypotheses and what each eliminated, and move on —
  `.claude/rules/debugging.md` §8. If a *second* task also hits three, stop the
  run entirely: something environmental is wrong.
- **The database cannot be brought up** (§1.1).
- **The baseline cannot be made green** in three attempts (§1.6).
- **The remote already holds a branch in this run's namespace** (§1.4).
- **A fast-forward merge onto the run branch is refused** (§2.6). The run owns
  both branches, so a refusal means the model is wrong about who is writing to
  them.
- **The wall clock reaches the deadline** (§8.2), **or the session budget does**
  (§8.6) — whichever comes first. Neither discards the task in flight: §8.4
  decides whether it runs to completion or is abandoned, and the ceilings —
  08:30, or 4% of the starting budget — are what keep "finishing up" finite.
- **The task list is complete _and_ the discretionary work in §9 is done or has
  no time left.** Stopping early with a clean, documented result is a success.
  Outside §9's explicit bounds, do not invent work to fill the night —
  unrequested scope is what `AGENTS.md` §7 exists to prevent, and nobody is
  awake to catch it.

A **rejected push** is deliberately not on this list. It stops further pushing
for the rest of the run (§2.6) and the work continues locally; the commits exist
on the branch whether or not anyone else can see them yet.

On stopping, always: working tree clean or its state explained, `progress.md`
current, final commit verified, and the run branch left pointing at the last
task that actually passed its checks. A half-merged task is worse than an
unmerged one.

---

## 7. Morning report

The run's last act. It begins when the last task ends — the list running out, a
stop condition, or the deadline resolving the task in flight (§8.4) — and it is
a summary at the top of `progress.md`.

It is the one thing never cut short for the clock (§8.5).

It is written as a task like any other — its own branch,
`night-<YYYY-MM-DD>-t<N>-report`, merged and pushed — because the run branch
moves only by fast-forward (§2 step 7). This is also the moment the SHAs and
push outcomes that the per-task entries could not contain get filled in.

- **Completed** — task, branch, commit SHA, verification actually run, and
  whether it was pushed
- **Discretionary (§9)** — visual work, under its own heading, described as
  **built and measured, not reviewed**, with the before/after screenshot paths
  and the §9.4 checks that passed. Never phrased so a reader could think the
  design was looked at
- **Clock and budget** — the readings at each task boundary, the two starting
  figures from §1.5, and **which deadline ended the run**: the clock, the
  budget, the task list, or a stop condition. A reader who knows the run ended
  on budget at 04:00 reads the rest of the report differently from one who
  thinks it finished everything it meant to
- **Provisional** — what was built on a parked assumption, which question, and
  the branch it is on (pushed, deliberately unmerged — §2.6)
- **Abandoned** — task, why, what was needed, and the local branch it is on
- **Questions** — the `questions.md` queue, most consequential first
- **State** — the run branch, every task branch and which of them reached the
  remote, whether the run branch is green, whether anything is uncommitted, and
  the lint score against the §1.6 baseline

On pushing, say what it did and did not buy. A pushed `night-**` branch *is*
picked up by CI, but this session cannot see the outcome — so write "pushed; CI
triggered, result not observable from here", never "CI passed". The difference
matters to a reader deciding whether to look.

Report only what was observed. `CLAUDE.md` §9 applies with full force here: there
is nobody to catch an overstated result before it is believed and acted on.
"Could not verify X" is a useful sentence; a claimed passing suite that never ran
is a lie the morning will act on.

---

## 8. Deadlines: the clock and the budget

The run has **two** deadlines and ends at whichever arrives first:

- **the clock** — 08:00 Europe/Stockholm (§8.1–§8.3), because someone will read
  the result over breakfast, and a run still mid-task at that moment hands them
  a half-finished branch and no report;
- **the session budget** (§8.6), because a run that spends its last tokens on a
  commit leaves exactly the same thing: branches nobody can interpret.

Both resolve the same way — §8.4 decides whether the task in flight finishes or
is abandoned, and §8.5's ceiling keeps that finite. The morning report is not
what you do with whatever is left over; it is reserved for, on both axes.

### 8.1 Reading the clock — do not use `TZ`

**`TZ='Europe/Stockholm' date` is wrong on this machine.** Git Bash here ships
no zoneinfo database, so it silently falls back to GMT for any named zone.
Measured on 2026-09-16:

```text
date                         ->  Wed Sep 16 09:18:58 WEST 2026   (correct)
TZ='Europe/Stockholm' date   ->  2026-09-16 07:18 GMT            (2h early)
TZ='UTC' date                ->  2026-09-16 07:18 GMT            (identical!)
```

The last two agreeing is the tell: the named zone was never resolved. Trusting
it would end the run at 06:00 in summer and 07:00 in winter.

**Use the machine's own clock**, which is set to Stockholm — the `WEST` label
Git Bash prints is cosmetic and also wrong, but the time itself is right:

```bash
date '+%H:%M'
```

Confirm that once during preflight, alongside §1.1. The system zone must be
`W. Europe Standard Time`, the Windows id covering Stockholm:

```bash
powershell -NoProfile -Command "[System.TimeZoneInfo]::Local.Id"
```

If it reports anything else, the machine is not on Swedish time and `date` is
not the deadline you were given. Convert explicitly instead, and record in
`progress.md` that you had to:

```bash
powershell -NoProfile -Command "[System.TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, [System.TimeZoneInfo]::FindSystemTimeZoneById('W. Europe Standard Time')).ToString('HH:mm')"
```

### 8.2 The checkpoints

Check the clock **and the budget** (§8.6) at every task boundary — §2 step 0,
before cutting a branch — and record both readings in `progress.md` with that
task.

**After 07:00, also check them at the seams inside a task**: when a verification
run finishes, before starting a repair cycle, and before dispatching the
`reviewer`. Those are already pauses, so a check there costs nothing — and a
threshold you can only observe at a task boundary cannot fire during the task it
is meant to govern. Do not check in the middle of a verify cycle; interrupting
one tells you less and takes longer.

The table below is the clock. §8.6 has the budget's, with the same three stages;
whichever threshold is reached first governs.

| From  | Rule |
| ----- | ---- |
| 07:15 | Start no new **discretionary** task (§9). Requested work may still start. |
| 07:30 | Start no new task of any kind. Carry on with the one in flight. |
| 08:00 | **The deadline.** Start nothing further. The task in flight either runs to completion or is abandoned — §8.4 decides which, and it is a judgement about the task's *state*, not about how much you want to finish it. Then the report. |
| 08:30 | **Ceiling** (§8.5). Abandon whatever is in flight, however close. Report now. |

### 8.3 Estimating

You will estimate badly, so anchor on measurement rather than feel. In the
2026-09-15 run a task took **20–45 minutes** of wall clock end to end, including
the `reviewer` pass (4–7 minutes on its own) and several full `dev.py test`
runs.

So: **do not start a task after 07:30**, and do not start one you believe is
large after 07:00. The overrun in §8.4 is there to save a task that is nearly
finished, not to make a late start survivable — a task abandoned at the ceiling
spent the night's remaining time and produced nothing, whereas stopping early
with a clean report is explicitly a success (§6).

If the requested list runs out well before the cutoff, that is what §9 is for.

### 8.4 At the deadline: finish or abandon

08:00 stops you *starting* things. It does not throw away a task that is nearly
done — an hour of finished work discarded at the last minute helps nobody, and
on a per-task branch a completed task is worth having even when the run ends
immediately afterwards.

So at 08:00, put one question to the task in flight: **is what remains the
ordinary steps of §2, or is it unknown?**

**Run it to completion** when all of these hold:

- the change is written — you are not still deciding what to do;
- verification is green, or running and expected to be;
- the `reviewer` pass has run, or there is room for it (4–7 minutes);
- nothing is sitting in a verify → repair cycle with an unresolved failure.

Then finish §2 steps 1–7 as normal: verify, review, act on the findings, record,
commit, merge, push.

**Abandon it** (§3) when any of those fails — still mid-implementation, an
unresolved failure, or a reviewer finding that needs real work. Finishing from
an unknown state is not finishing; it is starting something new against a clock,
and that is how a rushed commit gets made at 08:20 with nobody awake to catch
it.

Two things are never traded for the clock:

- **the reviewer pass.** Skipping it to make the deadline is weakening a control
  to make something pass (§3), and unattended it is the only review the change
  will ever get.
- **a failing check.** The commit gate in §2.1 has no time-based exception.

If either cannot be honoured in the time remaining, the answer is abandon, not
hurry.

**Discretionary work (§9) gets no overrun.** At 08:00 a visual task in flight is
abandoned outright. The allowance exists for work someone actually asked for.

### 8.5 The ceiling

**08:30 is absolute.** Whatever is in flight is abandoned, however close it
looks. "Nearly done" at 08:30 is the same sentence that was true at 08:00, and
hearing it twice is evidence the estimate was wrong — not that another ten
minutes will do it.

Write the report and stop. A run that overruns its ceiling has stopped being an
overnight run and become an unsupervised one that somebody is now waiting on.

The report itself is never cut short for the clock. It is the deliverable, it
takes minutes, and a run that ends without one has produced branches nobody can
interpret.

### 8.6 The budget

The clock is not the only thing that runs out. A session has a finite budget,
and spending the last of it on a commit produces the failure the deadline exists
to prevent: work that landed, and no report saying what it was or whether it
passed.

**The report is reserved for, not left over.**

#### Reading it

The harness surfaces a remaining figure in a system reminder, of the form
`<total_tokens>N tokens left</total_tokens>`. It decrements across the run — an
unattended run is effectively one long turn — so it is a real gauge rather than
a per-message reading.

Read it at the same points as the clock (§8.2): every task boundary, and after
07:00 at the seams inside a task. **Read it; do not estimate it.** The whole
problem with budget is that the feeling of having plenty is uncorrelated with
having plenty.

#### The thresholds

Proportions of the figure the run *started* with, with absolute floors, because
a percentage of a small budget is not enough to write anything:

| Remaining | Rule |
| --------- | ---- |
| below 30%, or 150k — whichever is larger | **Roundup.** Start nothing new, and put the task in flight to §8.4's finish-or-abandon test, exactly as at 08:00. Then the report. |
| below 4%, or 40k | **Ceiling.** Abandon whatever is in flight and write the report now. Mirrors 08:30. |

Two stages here where the clock has three, and the first is deliberately far
more generous than its 07:30 equivalent. The asymmetry is the point: a run that
misjudges the clock writes its report late, which costs a reader nothing much,
while a run that misjudges the budget cannot write one at all. Those are not
comparable mistakes, so the budget buys its margin early and in one step rather
than trimming it in two.

The band between 30% and 4% is the room to *finish* in — begin rounding up at
the first, be done by the second.

Measured on the 2026-09-15 run, as the only data that exists so far: the whole
run — preflight, three tasks each with a `reviewer` dispatch, and the report —
cost roughly **195k tokens**. Preflight was around 80k of that, because it
carries the fixed cost of the system prompt and `AGENTS.md`; each task ran
40–55k; the report itself 10–15k. Subagent usage is billed separately and does
not draw down this figure at the same rate — the reviewer reported 60–80k of its
own while the parent moved far less.

**In that run the budget was never close to binding.** It started at 15,000,000
and used about 1.3%; the clock was the constraint throughout. So do not
contort the night around this — but do check it, because the one run that ends
early for budget is the one that most needs a report and will have least left to
write it with.

#### When no figure is visible

If the harness surfaces nothing, there is no denominator and the percentages
above cannot be applied at all. Fall back to proxies, which are deliberately
stricter than the thresholds would be — being blind is a reason to stop earlier,
not later — and say in the report that you were flying blind:

- **Task count.** Five completed tasks is well past the measured shape of a run.
  Round up there.
- **Context compaction.** If the conversation has been summarised, older detail
  is already gone. That is both a budget signal and an accuracy one: quote
  `progress.md`, not your recollection.

#### Why the state files are the defence

`progress.md` is what makes the report cheap enough to write from a nearly-empty
budget. Kept current — the entry written on the task branch before each commit
(§2 step 5) — the report is assembled from files and `git log`, not from memory.

That matters most precisely when memory is the thing running out. A run whose
records are current can still produce an accurate report on its last tokens; a
run that was holding it all in context cannot, and compaction will have quietly
taken the verification output it needed to quote.

Under a tight budget the report may be terse. **A short accurate report is a
success; no report is not.** Cut the prose, never the facts: what landed, which
branches, what was actually verified, what was left undone.

---

## 9. Discretionary work: the visual layer

This is the **one** exception to §6's rule against inventing work, and it is
narrow. It exists because the repository has reached a state its own records
keep describing as a gap: `.claude/rules/frontend.md` and every morning report
so far end with some version of *"nothing has looked at how these pages
appear"*, and [ADR 0001](../../../docs/adr/0001-frontend.md)'s hand-written-CSS
half is still unexercised — no CSS of any kind exists in this project.

### 9.1 When it may start

All four, or not at all:

1. Every **requested** task is complete, parked (§4) or abandoned (§3).
2. The baseline is green and the run branch is clean.
3. The clock is before **07:15** (§8.2).
4. The run has not already hit a stop condition (§6).

Discretionary work never pre-empts requested work, and never runs to use up time
a requested task could have had.

### 9.2 Explore before building

The first discretionary task is **exploration, not CSS**. It produces a written
plan, not a stylesheet:

- Screenshot every page at 375px and 1280px into
  `docs/ai/night-<YYYY-MM-DD>/screenshots/before/`.
- Read `docs/requirements.md` §3 (mobile-first, usable on phone and desktop) and
  ADR 0001. These are the only recorded design constraints, and taste beyond
  them is not yours to invent unattended.
- Run the §9.4 checks against the pages as they stand and record what they find.
- Write the result into `plan.md` as discretionary tasks, smallest first, each
  with an acceptance criterion drawn from §9.4.

That exploration is itself a task: its own branch, its own commit. It is worth
doing even if the night ends immediately afterwards, because the morning gets
screenshots and a measured list instead of an opinion.

### 9.3 Hard bounds

- **No new dependency.** Tailwind stays deferred (ADR 0001, reaffirmed by ADR
  0006); adding one is forbidden by §3 and would fail `adr_guards.py` anyway.
- **No build step.** Hand-written CSS only.
- **One stylesheet**, at `shop/static/shop/<name>.css`, loaded from `base.html`
  via `{% load static %}`. `django.contrib.staticfiles` is already installed and
  app-directory static works, so **no settings change is needed** — and
  `live_server` serves static automatically, so the e2e tests see it.
- **Do not restructure markup the tests assert on.** Add classes; do not move,
  rename or unwrap an element carrying a `data-testid`, an ARIA role or a
  heading level. If a change genuinely needs restructuring, that is a task for a
  human — park it (§4).
- **No JavaScript.** Alpine is loaded, but interactivity is not styling, and new
  behaviour is a new requirement.
- **Never weaken an existing test** to accommodate a visual change (§3).

### 9.4 What is actually verifiable

Styling is mostly taste, which is why §5 calls it a poor unattended task. These
four are the parts that are *not* taste, and each is a real acceptance
criterion. All four were probed in this repository on 2026-09-16 and work:

| Check | How | Why it is not taste |
| ----- | --- | ------------------- |
| No horizontal overflow | `page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")` at 375px, must be `0` | `requirements.md` §3 requires the site to be usable on a phone |
| Tap target size | `locator.bounding_box()`, width and height ≥ 44 | A control too small to hit is broken, not ugly |
| Text contrast | read `getComputedStyle` colours via `page.evaluate` and compute the WCAG ratio in the test — no new dependency | Legibility is measurable |
| Screenshots | `page.screenshot(path=...)` at 375px and 1280px into the run's `screenshots/after/` | Evidence for a human, not a verdict |

**The contrast check has a trap, found while probing.** On the current pages
`getComputedStyle(document.body).backgroundColor` is `rgba(0, 0, 0, 0)` —
transparent, because nothing sets it. A ratio computed against that is
meaningless and will happily "pass". Either resolve the real painted background
by walking ancestors until a non-transparent colour appears, or make the test
assert that an explicit background is set and fail when it is not.

**A measurement worth having before you start:** the Add-to-cart button
currently renders at **80 × 21 px**, against the 44 × 44 guideline. There is
already a finding here — the check earns its keep on the first run.

### 9.5 What it still does not prove

None of the above knows whether the page looks *good*. Hierarchy, rhythm,
balance, whether the flaw disclosure reads as a warning or as decoration — a
human sees those in a second and no assertion here will.

So the morning report says exactly that, under its own heading (§7), and links
the before/after screenshots. Report discretionary work as **built and measured,
not reviewed**. A reader who believes the design was checked will not look at
it, and then nobody ever does.

Commit and merge it like any other task (§2.6) — it is real, tested work — but
keep each visual change in its own commit, so one can be dropped without
unpicking the rest.

### 9.6 The ADR

The first CSS in the project means ADR 0001's deferred half is finally being
exercised, and a static-files convention is being set. That deserves a record —
but **do not write an accepted ADR unattended.** ADR 0006 exists precisely
because a decision was made in code and documented afterwards, and it names that
ordering as "the defect this document closes, not a pattern to repeat".

Write what was chosen and why into `decisions.md`, and raise the ADR itself as a
question in `questions.md`, for a human to accept, amend or reject.
