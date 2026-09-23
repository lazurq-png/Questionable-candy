---
name: night-run
description: Protocol for running unattended, with no human available to answer questions — overnight or long autonomous sessions, including ones spanning several sessions. Executes a human-written plan read from docs/ai/night-<today>/plan.md (and stops if there is none). Defines preflight and how to resume a run already in progress, a branch per task pushed as each one finishes, CI polled in the background while the next task proceeds, durable state, forbidden operations, the 08:00 Europe/Stockholm deadline, a per-session budget reserve that protects the morning report or a handoff, bounded discretionary visual work when the task list runs out, stop conditions, and a morning report that shows each task's code with what it does and why it was added. Use when starting an unsupervised run, resuming one, or when a session discovers mid-flight that nobody is there.
---

# Unattended Run

`AGENTS.md` and `CLAUDE.md` still apply. This document changes only what cannot
work without a human: asking questions, looking at a page, and knowing when to
stop.

## Read this first

- **Permission prompts are bypassed** and `.claude/settings.json` is not
  consulted. Every guardrail here holds only because you hold it. Prefer the
  reversible action, commit early, and when a step feels like it needs
  permission, log it rather than proceed.
- **Two things reach outside the machine**, both narrow, both in §3's list:
  pushing this run's own branches, and a read-only, unauthenticated poll of
  GitHub Actions for commits this run pushed (§2.6).
- **Work in parallel wherever nothing depends.** Independent reads and checks go
  in one message of parallel tool calls. Long jobs (the full suite, the
  `reviewer`, the CI poll) run in the background while you do the next
  independent thing; the harness re-invokes you when a background command or
  agent finishes. Never poll one yourself, and never `sleep` in the foreground,
  which is blocked anyway.
- **The state files are the memory.** Write what the report will need into
  `docs/ai/night-<YYYY-MM-DD>/progress.md` when it happens. Quote files and
  `git`, not recollection, because context may already have been compacted.

---

## 1. Preflight

Run these together, in one message. All are read-only:

```bash
date '+%F %H:%M'                                              # §8.1
powershell -NoProfile -Command "[System.TimeZoneInfo]::Local.Id"
~/Binaries/pgsql/bin/pg_isready -h localhost -p 5432; echo "exit $?"   # §1.1
git status --short
git remote -v
cat "docs/ai/night-$(date +%F)/plan.md"                       # §1.0
for b in $(git branch --list 'night-*' --format='%(refname:short)' \
           | grep -E '^night-[0-9]{4}-[0-9]{2}-[0-9]{2}$'); do
  git show "$b:docs/ai/$b/progress.md" 2>/dev/null \
    | grep -q '^## Morning report' || echo "in progress: $b"
done
```

- **The loop prints a run branch** → you are **resuming** it: go to §10.2. Do
  not run §1.0, §1.3 or §1.5. Recreating the branch or state files is how a run
  loses its history.
- **It prints nothing** → a new run: §1.0–§1.6 in order.

The loop reads `progress.md` from each run branch, never from the working tree.
A new run is cut from `dev`, which lacks unmerged earlier runs, so the tree
would make a finished run look unfinished. A run branch with no committed
`progress.md` counts as in progress, which is correct.

If a step fails in a way it does not say how to recover from, stop and write why
into `progress.md`.

### 1.0 The plan

**The run reads a plan; it does not write one.** A human writes
`docs/ai/night-<YYYY-MM-DD>/plan.md` beforehand, where the date is today's
`date +%F`.

| Result | Action |
| ------ | ------ |
| Exists and lists at least one task | Continue. This is the task list. |
| Missing, empty, or no task | **Stop.** Create no branch. Write an uncommitted `progress.md` in that directory saying no plan was found at that path, and end. |

Only today's directory counts. Never borrow another date's plan or derive one
from `docs/requirements.md`, because a run without a human's plan has no
requested work (§6).

The plan is **read-only** to the run:

- Do not add, remove, reorder, reword or tick off its tasks. Progress goes in
  `progress.md`. The one addition allowed is §9.2's list, under its own heading
  below everything the human wrote.
- An underspecified task gets acceptance criteria derived while exploring it,
  recorded in `decisions.md`. A task with two defensible readings goes to §4.
- `<N>` in branch names is the plan's own numbering, or the order of its tasks
  if it has none.
- The plan does not switch off this document. The exception is one the human
  wrote *explicitly*, naming the rule it lifts and the task it applies to, and
  it covers exactly that. No plan lifts the push rules (§2.6, §3).

The plan is usually uncommitted. `git status --short -- docs/ai/night-<date>/`
tells you. An untracked plan survives `git checkout dev`, and the first task
commits it exactly as the human left it. If it was committed on a branch other
than `dev`, check it is still readable after §1.3. If it is not, stop as for a
missing plan and do not fetch it from that branch.

### 1.1 Database

Every `dev.py` task except `lint`/`lint:workflows` runs `makemigrations` and
`migrate` first, so a down cluster fails all verification. Branch on the **exit
code** of the `pg_isready` above. The messages are localised, and the
`%USERPROFILE%\…` form of the path does not expand in bash: it fails with exit
1, which would be misread as "starting up".

| Code | Meaning | Action |
| ---- | ------- | ------ |
| 0 | accepting | continue |
| 1 | starting / shutting down | retry after 5s, up to 3 times |
| 2 | not running | start it (below) |
| 3 | bad invocation | stop the run |

```bash
~/Binaries/pgsql/bin/pg_ctl start -D ~/Binaries/pgsql/data -l ~/Binaries/pgsql/server.log
```

Re-check until exit 0. If it is not up within ~30s, record the tail of
`server.log` and stop. Starting the cluster is the **only** environment repair
allowed. An empty or wrong database is a stop, not a fix.

### 1.2 Migration drift

```bash
python manage.py makemigrations --check --dry-run --noinput
```

Non-zero means drift already exists. Record it as pre-existing, so a migration
`dev.py` writes later is not misattributed.

### 1.3 Branches

One integration branch, plus one branch per task, each cut when its task starts
(§2 step 0):

```text
dev                                     base; never committed to
└── night-<YYYY-MM-DD>                  the run branch; moves only by fast-forward
    ├── night-<YYYY-MM-DD>-t1-<slug>
    └── night-<YYYY-MM-DD>-t2-<slug>    cut after t1 merged
```

```bash
git checkout dev && git checkout -b night-<YYYY-MM-DD>
```

- **The separator is a hyphen.** Git stores refs as paths, so
  `night-2026-09-15/t1-x` cannot coexist with `night-2026-09-15`. The failure
  (`cannot lock ref`) only appears at the second branch.
- **`<YYYY-MM-DD>` is the date the run started** and never changes, even after
  midnight. A resumed session takes it from the branch, never from `date`.
- Never work unattended on `master` or `dev`.

### 1.4 Remote

```bash
git ls-remote --heads origin "night-<YYYY-MM-DD>*"
```

| Result | Action |
| ------ | ------ |
| No remote | Local-only run: record it, skip every push and poll. Not a failure. |
| Reachable, no matching branch | Normal. |
| Matching branch, **resuming** | Expected. Confirm with `git fetch origin && git merge-base --is-ancestor origin/night-<date> night-<date>`, then continue. |
| Matching branch, **new run** | **Stop.** Someone else owns the namespace. |
| Unreachable | Continue local-only, record why. |

Create, delete or fetch nothing else on the remote.

### 1.5 State

- **Pre-existing uncommitted changes are not yours.** Carry them onto every
  branch untouched, list them in `progress.md`, and never stash, restore or
  commit them. Wherever this document says "clean", it means clean apart from
  these.
- Create `progress.md`, `decisions.md` and `questions.md` beside `plan.md`
  (`docs/ai/README.md` says what each holds). There is one directory for the
  whole run, named after the run branch. Never create, overwrite or template
  `plan.md`.
- Record in `progress.md`, before the first task: the wall clock, the session's
  budget figure (§8.6), and the **deadline as a full date and time** (§8.2),
  e.g. `Deadline: 2026-09-18 08:00`. The budget thresholds are proportions of
  that starting figure, and compaction will lose it if it is not written down.

### 1.6 Baseline

Run the three checks in parallel. `lint` and `adr_guards` never touch the
database, so they cannot race `test`'s migrate:

```bash
python scripts/dev.py test
python scripts/dev.py lint > docs/ai/night-<YYYY-MM-DD>/lint-baseline.txt 2>&1
python scripts/adr_guards.py
```

All three must exit 0. Record the lint score line (`rated at N/10`). `lint`
exits 0 on warnings, so the saved report is what later diffs are against.
`lint:workflows` is not part of the baseline (§2 step 1).

**A red baseline makes the repair task #1**, on
`night-<YYYY-MM-DD>-t0-baseline`, through §2 like any task and never on `dev`.
If it stays red after three cycles, stop the run. Record that the requested work
did not start, and why.

---

## 2. The task loop

`CLAUDE.md` §1 applies per task (explore, plan, implement, verify, review), with
these additions.

0. **Read clock and budget, then cut the branch** from the run branch:

   ```bash
   date '+%F %H:%M'
   git checkout night-<YYYY-MM-DD> && git status --short
   git rev-parse HEAD                      # the task's base SHA -- record it (§7)
   git checkout -b night-<YYYY-MM-DD>-t<N>-<slug>
   ```

   Past a cutoff for this kind of task (§8.2, §8.6), do not start it. Record
   the clock, budget and **base SHA** with the task in `progress.md`. The base
   SHA is what the morning report diffs the task's code against.

1. **Verify before committing.** During the work, run the narrowest suite
   (`test:unit`, `test:int`, `test:e2e`, or a single test via `-- -k`). Before
   the commit, `dev.py test`, `dev.py lint` and `adr_guards.py` must all exit 0,
   run in parallel as in §1.6. **Never commit on a failing or unrun check.** A
   pylint error blocks the commit like a failing test.

   - **Lint diff.** Diff the lint output against `lint-baseline.txt`. A new
     warning is either fixed or recorded in `decisions.md` with its reason.
     Warnings do not spend the three-cycle budget (§6).
   - **`lint:workflows`** joins the gate only if the task changed a workflow
     (any output from `git diff --name-only night-<date> -- .github/workflows/`
     or `git ls-files --others --exclude-standard -- .github/workflows/`), or a
     workflow is known to have failed, including by §2.6's poll. Otherwise do
     not run it or list it. Exit 2 `not found` means the task cannot be
     verified: abandon it (§3) and name the missing tool. Never call
     `actionlint` directly, because alone it silently skips shellcheck and
     pyflakes rules.
   - **Negative controls** (breaking the code to prove a test fails): undo the
     mutation by reversing your own edit. **Never `git checkout <file>` or
     `git restore <file>` to undo a control.** That restores the last commit and
     throws away the task's uncommitted work, which happened twice on
     2026-09-17.

2. **UI work needs a real browser**: a Playwright test in `tests/e2e/` using
   `live_server`, per `.claude/rules/frontend.md`. `django.test.Client` does not
   enforce CSRF, and that is how a 403 once shipped behind a green suite.

3. **Independent review.** For a non-trivial task, dispatch the `reviewer`
   subagent **in the background, at the same moment as step 1's final
   checks**. Give it the task description, not your reasoning, and let it find
   the diff itself. If the checks then force a non-trivial change, have it
   re-review. Act on every finding, or record in `decisions.md` why not. "The
   reviewer was wrong" is an acceptable entry; silence is not. Unattended, this
   is the only review the change gets.

4. **Re-check migration drift** (§1.2) after touching `shop/models.py` or
   `accounts/models.py`. An unintended migration is a finding.

5. **Record, then commit.** Update the state files on the task branch before
   staging, so the evidence travels with the diff. The `progress.md` entry
   holds:

   - branch and base SHA (step 0), clock and budget at start;
   - **What the code does**: per file or group of files, the behaviour it adds
     or changes, in plain words;
   - **Why it was added**: the plan task or finding it answers, and any
     non-obvious choice, with its `decisions.md` reference;
   - the verification actually run, with real results (counts, coverage, lint
     score), and the reviewer's verdict and what was done about it.

   Write the what and the why now, while the context is fresh. The morning
   report copies them (§7). The entry cannot contain its own SHA, or whether the
   push or CI succeeded. Those go into the next task's entry and the report.

   **Gate:** if the previous task's CI poll (step 6) has not resolved yet, wait
   for its notification before this commit. Do something else useful meanwhile,
   or end the turn and let the notification resume you. If it failed, handle
   that first (step 6).

   One commit per task, on the task branch:

   ```text
   <what changed, imperative, one line>

   <why, and what verification was actually run>

   Unattended run: docs/ai/night-<YYYY-MM-DD>/
   ```

   Add whatever attribution lines this session is instructed to add.

6. **Merge, push, and poll in the background.** Only after a complete, green,
   reviewed task:

   ```bash
   git checkout night-<YYYY-MM-DD>
   git merge --ff-only night-<YYYY-MM-DD>-t<N>-<slug>
   git push --set-upstream origin night-<YYYY-MM-DD>-t<N>-<slug>
   git push origin night-<YYYY-MM-DD>
   ```

   A refused `--ff-only` means something this protocol does not model is
   writing to the run's branches: **stop the run**. Never fall back to a merge
   commit or a rebase. A **rejected push**: record it, push nothing further for
   the rest of the run, and keep working locally. No PRs, ever. Local-only runs
   skip this step's pushes and polling.

   Then start the poll with the Bash tool's `run_in_background: true`, record
   `CI: pending` for the task, and **go straight on to the next task**. The
   poll sleeps inside its own process and exits once every expected branch has
   a completed run, after 30 minutes, or on repeated API errors:

   ```bash
   python - "$(git rev-parse HEAD)" night-<date>-t<N>-<slug> night-<date> <<'PY'
   import json, sys, time, urllib.request
   sha, want = sys.argv[1], set(sys.argv[2:])
   url = ("https://api.github.com/repos/lazurq-png/Questionable-candy"
          f"/actions/runs?head_sha={sha}")
   hdr = {"Accept": "application/vnd.github+json", "User-Agent": "night-run"}
   end, errors = time.time() + 1800, 0
   time.sleep(300)
   while True:
       try:
           with urllib.request.urlopen(urllib.request.Request(url, headers=hdr),
                                       timeout=30) as r:
               runs = json.load(r).get("workflow_runs", [])
           errors = 0
       except Exception as exc:  # network, rate limit, non-200
           errors += 1
           if errors >= 2:
               print("UNOBSERVED api-error", exc)
               sys.exit(0)
           runs = []
       done = [x for x in runs if x["status"] == "completed"]
       if want <= {x["head_branch"] for x in done}:
           for x in done:
               print(x["head_branch"], x["conclusion"], x["html_url"])
           sys.exit(0)
       if time.time() > end:
           print("UNOBSERVED timeout",
                 [(x["head_branch"], x["status"]) for x in runs])
           sys.exit(0)
       time.sleep(120)
   PY
   ```

   A `PROVISIONAL:` branch (§4) is pushed alone, so pass only its own name.
   When the notification arrives, record the outcome in `progress.md` (it is
   committed with the next task):

   - **All `success`** → "CI passed", with the run URLs. This is the only
     outcome that may say so.
   - **`UNOBSERVED`, or `cancelled`** → "pushed; CI not observed", and why.
     Never infer a result.
   - **`failure`** → a verification failure found late. It continues this
     task's three-cycle count (`.claude/rules/debugging.md` §8):
     1. Name the failing jobs: append `/jobs` to the run's API URL. Do not
        fetch logs, which needs auth and is outside §3's exception.
     2. Park the task in flight. Stash **only the paths it touched**
        (`git stash push -- <paths>`), never the pre-existing changes.
     3. Check out task N's branch (still the run-branch tip, since the gate in
        step 5 kept the next task from merging). Reproduce the failure locally
        with the matching check, fix it in a **new commit** (never `--amend`,
        because the commit is pushed), then steps 1–6 again: fast-forward,
        push both, poll the new SHA.
     4. Return: `git checkout <in-flight branch> && git merge --ff-only
        night-<date> && git stash pop`. The in-flight branch has no commits of
        its own (one commit per task, at the end), so this fast-forward always
        succeeds.
     5. On the third failed cycle, leave task N's branches pushed as they are
        (nothing pushed may be rewritten), record the three hypotheses and what
        each CI run showed, and continue. A failure that does not reproduce
        locally is evidence that the environments differ. Record that; do not
        guess. A second task reaching three cycles stops the run (§6).

7. **Never commit directly to the run branch.** It moves only by fast-forward,
   which is what makes `--ff-only` a real check. Anything left to record goes
   in the next task's commit, or the report's.

**Provisional work** (built on a §4 assumption) is one commit prefixed
`PROVISIONAL:`, on its own task branch, **pushed but never merged**, so no later
task inherits the assumption. Name the branch in `questions.md`.

**Abandoned work** (§3, §6) stays on its local branch, unmerged and unpushed. A
pushed branch reads as an offer. Name it in `progress.md` and do not delete it.

---

## 3. Forbidden operations

Never, unattended:

- `git push --force` / `--force-with-lease`, `--delete`, `--tags`, or a push to
  anything outside this run's `night-<YYYY-MM-DD>` namespace: never `master`,
  never `dev`, never a ref this run did not create. Check the name before every
  push.
- Opening a pull request.
- Rewriting history (`rebase`, `commit --amend`, `reset --hard`) except over
  your own uncommitted work. Once pushed, never.
- Stashing, restoring or discarding changes you did not make in this run.
- Destructive schema operations: dropping or renaming a table or column,
  `migrate <app> zero`, editing or deleting an existing migration, `flush`,
  `dropdb`.
- Touching `.env`, or writing any real credential anywhere. Pushed, that is a
  disclosure, not a mess.
- Adding a dependency (`requirements*.txt`). Whether one earns its place is a
  human's decision, and ADR 0003 rules out DRF outright.
- Weakening a test, an assertion or a security control to make something pass
  (`AGENTS.md` §19).
- Installing software, changing PATH, or modifying anything outside this
  repository, except starting PostgreSQL (§1.1).
- Deleting a file you did not create in this run.
- Contacting any external service, **except** `git push`/`fetch` to `origin`
  for this run's branches and the §2.6 poll: read-only, no token, only on
  commits this run pushed.

**If a task needs one of these, abandon it.** Write in `questions.md` what was
needed, which rule blocked it, and the exact command or diff for a human to
approve verbatim. Then:

```bash
git restore -- <paths this task touched>    # never a bare `git restore .`: pre-existing changes are not yours
git checkout night-<YYYY-MM-DD>
```

Do not implement up to the boundary. A half-applied schema change is worse than
none.

---

## 4. Ambiguity: park and continue

When a requirement has two defensible readings, or a fork appears that
`AGENTS.md` §18 would have you ask about:

1. In `questions.md`: the question, each option with its consequence, your
   recommendation, and what you did meanwhile.
2. Take the **smallest reversible** interpretation: cheapest to undo, not most
   likely right.
3. Build it as a `PROVISIONAL:` commit on its own branch. Push it, do not merge
   it (§2), and name the branch beside the question.
4. Continue with the next independent task. If a task depends on the answer,
   park it too.

---

## 5. Task selection

Good unattended tasks are provable by a command: testable behaviour, bug fixes
that start from a failing test, coverage, documentation the repository can
confirm. Poor ones, which should be logged for supervised work: primarily visual
changes, matters of taste, refactors with no behavioural definition of done, and
decisions the repository cannot settle. Visual work is the one bounded exception
(§9), only after the requested list.

---

## 6. Stop conditions

End the run (merge, push and delete nothing further) when:

- **A second task hits three failed verify → repair cycles.** The first one
  just gets abandoned (§3), with all three hypotheses recorded
  (`.claude/rules/debugging.md` §8), and the run moves on.
- **The database cannot be brought up** (§1.1).
- **The baseline stays red** after three attempts (§1.6).
- **The remote already holds this run's namespace** at the start of a new run
  (§1.4).
- **A `--ff-only` merge is refused** (§2.6).
- **The clock reaches the deadline** (§8.2). §8.4 decides whether the task in
  flight finishes; 08:30 is the ceiling.
- **The budget reaches roundup** (§8.6). That ends the *session*. It ends the
  *run* only if this session owes the report; otherwise hand off (§10.3).
- **The list is done and §9 is done or out of time.** Stopping early with a
  clean record is a success. Outside §9, do not invent work.

A rejected push is **not** a stop. It ends pushing, not work.

On stopping: the tree clean or its state explained, `progress.md` current,
outstanding CI polls resolved or recorded as pending, and the run branch at the
last task that passed its checks.

---

## 7. Morning report

The **run's** last act. It is a task like any other, on
`night-<YYYY-MM-DD>-t<N>-report`, merged and pushed, and it goes at the top of
`progress.md` under exactly `## Morning report`. §1 recognises a finished run by
that heading. It is never cut short for the clock (§8.5). An earlier session
writes §10.3's handoff instead, which carries the same content.

**Before writing it, let every outstanding CI poll resolve** (or reach its own
30-minute timeout). The report's own push is not waited on.

Build it from `progress.md`, `questions.md` and `git`, not from memory. It
contains:

- **Headline**: two or three sentences on what a user of the site can now do,
  and whether everything requested landed.
- **Completed**: a table of task, branch, SHA, verification actually run, and CI
  outcome. Use "CI passed" only with a `success` in hand and the run URL,
  otherwise "CI failed, fixed in N cycles (job)", "abandoned after 3 CI cycles
  (job)", or "pushed; CI not observed".
- **Code by task** (below).
- **Discretionary (§9)**: described as **built and measured, not reviewed**,
  with the before/after screenshot paths and the §9.4 checks that passed.
- **Provisional**: what was built, on which question, on which branch.
- **Abandoned**: the task, why, what it needed, and its local branch.
- **Questions**: the `questions.md` queue, most consequential first.
- **Clock and budget**: the starting figures (§1.5), the reading at each task
  start, and **which deadline ended the run**: clock, budget, list, or a stop
  condition.
- **State**: the run branch and tip, which branches reached the remote, green or
  not, anything uncommitted, and the lint score against the baseline.
- **What no test has done**: at minimum, that nobody looked at the pages.

### Code by task

For every completed, discretionary and provisional task, the report shows the
code the task added, then says what it does and why it was added. Generate the
diffs from git rather than retyping them. That keeps them exact, and they never
need to pass through your context:

```bash
# tasks.txt, in your scratchpad directory: one line per task, <N> <base SHA> <task branch>
while read -r n base br; do
  stat=$(git diff --shortstat "$base" "$br" -- . ':(exclude)docs/ai/')
  printf '#### T%s — `%s`\n\n<!-- T%s what/why -->\n\n' "$n" "$br" "$n"
  printf '<details><summary>Code: %s</summary>\n\n~~~~diff\n' "$stat"
  git diff "$base" "$br" -- . ':(exclude)docs/ai/'
  printf '~~~~\n\n</details>\n\n'
done < tasks.txt > code.md                  # both in the scratchpad, never the repo
```

The range runs from the task's base SHA to its branch tip, so CI-fix commits
are included. The state files are excluded, and tests, templates and migrations
are kept. Then replace each `<!-- T<N> what/why -->` marker with that task's
entry from §2 step 5:

- **What it does**: per file or group of files, in behavioural terms, e.g.
  "`shop/views.py`: `checkout` now refuses an empty cart with a redirect to the
  catalog".
- **Why it was added**: the plan task or finding, plus any non-obvious choice
  (`D<n>`).

Put the section inside the morning report, after the Completed table. The
tilde fence survives backtick fences in diffed Markdown. The collapsed
`<details>` keeps the report readable. A task whose diff is only state files
says so in one line instead of an empty block.

Report only what was observed. "Could not verify X" is useful. A claimed
passing suite that never ran is a lie the morning will act on. Under a tight
budget, cut prose, never facts.

---

## 8. Deadlines: the clock and the budget

The run ends at whichever comes first: **08:00 Europe/Stockholm** (§8.1–§8.5),
or the session **budget** (§8.6). Both resolve through §8.4's
finish-or-abandon, and both reserve room for the report instead of leaving it
the remainder.

### 8.1 Reading the clock

**Never `TZ='Europe/Stockholm' date`.** Git Bash here has no zoneinfo and
silently returns GMT (measured 2026-09-16: two hours early, identical to
`TZ=UTC`). The machine clock is on Stockholm time, so use `date '+%F %H:%M'`.
Its `WEST` label is wrong but cosmetic. Always read the date together with the
time.

If preflight's time-zone id is not `W. Europe Standard Time`, record that, and
read the time with:

```bash
powershell -NoProfile -Command "[System.TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, [System.TimeZoneInfo]::FindSystemTimeZoneById('W. Europe Standard Time')).ToString('yyyy-MM-dd HH:mm')"
```

### 8.2 The checkpoints

**The deadline is the first 08:00 after the run started, with its date**: a
start at 22:00 on the 17th or at 00:30 on the 18th both give
`2026-09-18 08:00`. It belongs to the run. A resumed session copies it from
`progress.md` and never recomputes it. Every time below is on the deadline's
date, so compare full dated readings: 23:10 on the 17th is not "after 07:30".

Read clock and budget at every task start (§2 step 0). After 07:00, also read
them at the pauses inside a task: after a verification, before a repair cycle,
before dispatching the `reviewer`, and at the §2 step 5 gate.

| From  | Rule |
| ----- | ---- |
| 07:15 | No new discretionary (§9) task. |
| 07:30 | No new task of any kind. |
| 08:00 | **Deadline.** The task in flight finishes or is abandoned (§8.4). Then the report. |
| 08:30 | **Ceiling** (§8.5). Abandon whatever is in flight. Report now. |

### 8.3 Estimating

From the 2026-09-17 run's task start times: the median task took **~20
minutes**, the range was 3–50, and the `reviewer` took 4–7 minutes of that. CI
now overlaps the next task (§2.6), so it adds wall-clock time only when it
fails, and at the very end, where the report waits on the last poll. Do not
start a task you think is large after 07:00. §8.4's overrun rescues a nearly
finished task. It does not make a late start survivable.

### 8.4 At the deadline: finish or abandon

At 08:00, **run the task in flight to completion** only if all of these hold:
the change is written, verification is green or running and expected to pass,
the `reviewer` has run or there is room for it, and no failure is unresolved.
Otherwise **abandon it** (§3). Finishing from an unknown state is starting new
work against the clock.

Never traded for time: **the reviewer pass** and **a passing gate**. If either
cannot be honoured, abandon. Discretionary work gets no overrun: at 08:00 it is
abandoned outright.

### 8.5 The ceiling

**08:30 is absolute.** "Nearly done" twice is evidence the estimate was wrong.
Abandon, write the report, stop. The report itself is never cut for the clock.

### 8.6 The budget

**Read** the harness's `<total_tokens>N tokens left</total_tokens>` at the same
checkpoints as the clock. Do not estimate it. Thresholds are proportions of the
figure **this session** started with, and whichever of the two numbers is larger
applies:

| Remaining | Rule |
| --------- | ---- |
| below the **reserve** (next table) | **Roundup.** Start nothing new, and apply §8.4 to the task in flight. Then close out: the report if this session owes it, otherwise the handoff (§10.3). |
| below 4%, or 40k | **Ceiling.** Abandon, and close out now. |

| This session | Reserve | Closes with |
| ------------ | ------- | ----------- |
| is final: past 07:30, or less than one task's length before 08:00 | **30%**, or 150k | the morning report (§7) |
| otherwise; another session can follow | **10%**, or 60k | the handoff (§10.3) |

Misjudging which session is final is safe, because a handoff is written to
serve as the report (§10.3).

For scale, the 2026-09-17 run used 4.7% of 15M tokens for preflight, 17 tasks
and the report, about 40k per task. The budget has not yet bound any run. Keep
reading it, because the run that does end on budget needs its report most. The
`reviewer`'s own usage is billed to the subagent, not to this figure.

**No figure visible:** say so in the report, and round the session up after five
completed tasks, handing off first if it is before 07:30. After a context
compaction, trust `progress.md` over memory.

---

## 9. Discretionary work: the visual layer

The one exception to §6's rule against inventing work. The project has had a
hand-written stylesheet since 2026-09-16 (`shop/static/shop/site.css`, light and
dark themes, conventions recorded in
[ADR 0008](../../../docs/adr/0008-hand-written-css-themes.md)), and
`tests/e2e/test_theme.py` asserts §9.4's measurable checks on every page. The
gap that remains is that nobody has *looked* at the pages. Nothing here closes
that gap (§9.5).

### 9.1 When it may start

All of these must hold: every requested task is complete, parked or abandoned;
the baseline is green and the run branch clean; the time is before 07:15; and
no stop condition has fired. It never takes time a requested task could have
had.

### 9.2 Explore before building

The first discretionary task produces a plan, not CSS, on its own branch and in
its own commit:

- Screenshot every page at 375px and 1280px into
  `docs/ai/night-<YYYY-MM-DD>/screenshots/before/`.
- Read `docs/requirements.md` §3 and ADRs 0001 and 0008, the only recorded
  design constraints. Taste beyond them is not yours to invent.
- Run the §9.4 checks and record what they find.
- Append a list to `plan.md` under `## Discretionary (added by the run)`,
  smallest task first, each with a §9.4 acceptance criterion, numbered on from
  the human's last task.

### 9.3 Hard bounds

- No new dependency (§3) and no build step. Hand-written CSS in the existing
  stylesheet, following ADR 0008's conventions.
- Do not restructure markup the tests assert on. Add classes, but never move,
  rename or unwrap anything carrying a `data-testid`, an ARIA role or a heading
  level. If the change needs that, park it (§4).
- No JavaScript. New behaviour is a new requirement.
- Never weaken an existing test (§3).

### 9.4 What is actually verifiable

| Check | How | Why it is not taste |
| ----- | --- | ------------------- |
| No horizontal overflow | `scrollWidth - clientWidth` at 375px is `0` | `requirements.md` §3: usable on a phone |
| Tap targets | `bounding_box()` width and height ≥ 44 | A control too small to hit is broken |
| Text contrast | WCAG ratio from `getComputedStyle`, computed in the test | Legibility is measurable |
| Screenshots | 375px and 1280px into `screenshots/after/` | Evidence for a human, not a verdict |

The contrast check must resolve the real painted background by walking up the
ancestors past transparent ones. A ratio against `rgba(0, 0, 0, 0)` "passes"
meaninglessly. `tests/e2e/test_theme.py` already does this, so extend it rather
than writing a second one.

### 9.5 What it still does not prove

Nothing here knows whether a page looks *good*. Report discretionary work as
**built and measured, not reviewed**, with the screenshots linked. Keep each
visual change in its own commit, so one can be dropped without unpicking the
rest.

### 9.6 Decision records

Never write or accept an ADR unattended. Record a new convention in
`decisions.md`, and raise the ADR, or an amendment to ADR 0008, in
`questions.md` for a human.

---

## 10. Running across sessions

The run branch and `docs/ai/night-<YYYY-MM-DD>/` *are* the run. A session only
holds them for a while, and nothing of its conversation survives it.

### 10.1 What a session owes the next

The run branch with every completed task merged and pushed. State files current,
with real verification output, each task's base SHA and its what/why (§2
step 5), and every CI outcome observed. A handoff (§10.3) as the last entry.

### 10.2 Resuming

Reached from §1. Do not re-run §1.0, §1.3 or §1.5.

```bash
git checkout night-<YYYY-MM-DD>     # the date comes from the branch, not `date`
git status --short
git log --oneline dev..HEAD
```

1. Read the state files, starting with `progress.md`'s last entry: that is the
   handoff.
2. Re-run §1.1, §1.2 and §1.6 (the baseline is a claim you inherit). Reconcile
   the lint score against the existing `lint-baseline.txt` and never overwrite
   it.
3. Under a new session heading, record this session's starting clock and budget
   (its own denominator) and copy the deadline as it stands.
4. Any CI recorded as `pending` belongs to a poll that died with the old
   session. Run the poll again once on that SHA.
5. Pick up an abandoned task only if it was abandoned for time or budget. The
   three-cycle limit belongs to the run and does not reset.
6. Continue at §2 step 0. The resume entry is committed with the next task.

### 10.3 The handoff

What a session writes instead of the morning report when it stops before 08:00:
appended to `progress.md` on `night-<YYYY-MM-DD>-t<N>-handoff`, merged and
pushed. Head it `## Handoff`, **never** `## Morning report`, or §1 will treat
the run as finished.

It states why the session stopped, where the run is (its tip, which tasks are
done and which remain), anything in flight and why it was left, the next
session's first step in one sentence, and **everything §7 requires, including
Code by task**. If no session follows, this is the morning report, so write it
for the person at breakfast. Never write anything that only makes sense if
another session comes.

### 10.4 The run is still one run

These carry across sessions and never reset: the three-cycle limit, the dated
deadline, parked questions (a later session inherits the decision and the
`PROVISIONAL:` branch), and §9's precondition that every requested task is done
across the run. Only the budget is per session.
