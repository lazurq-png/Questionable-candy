# AI-Assisted Engineering Workflow

This repository uses AI coding agents as engineering collaborators, not as unrestricted code generators.

The standard operating model is:

**Explore → Plan → Implement → Verify → Repair → Review**

For trivial tasks, some phases may be abbreviated. For substantial work, all phases should be explicit.

---

# 1. Explore

Before changing code, establish what actually exists.

The agent should:

* Read applicable repository instructions.
* Inspect the relevant directory structure.
* Locate the current implementation.
* Trace the relevant execution path.
* Inspect nearby abstractions.
* Read relevant tests.
* Identify callers and consumers.
* Check configuration and environment assumptions.
* Identify database, API, security, and concurrency boundaries.

The goal is not to read the entire repository.

The goal is to build the smallest reliable mental model needed to make the change safely.

## Explore Before Assume

Do not infer architecture from:

* filenames alone
* folder names alone
* framework defaults
* stale documentation
* generated code
* previous implementations

Repository behavior is the source of truth.

---

# 2. Plan

For meaningful changes, write a short implementation plan before editing.

A good plan answers:

1. What behavior changes?
2. Which existing code owns that behavior?
3. Which files should change?
4. Which existing abstractions should be reused?
5. What tests prove the change?
6. What risks or compatibility concerns exist?

The plan should remain proportional to the task.

Do not create elaborate plans for a one-line bug fix.

Do not skip planning for architectural, database, security, or cross-cutting changes.

---

# 3. Implement

Implement the smallest sufficient change.

Prefer:

* Existing abstractions
* Existing patterns
* Existing dependencies
* Existing validation
* Existing error handling
* Existing test utilities
* Existing UI components
* Existing data-access patterns

Avoid:

* speculative abstractions
* unrelated refactoring
* unnecessary dependency additions
* broad renaming
* style-only cleanup
* duplicated implementations
* changing public behavior without justification

A smaller change is easier for both humans and agents to reason about.

---

# 4. Verify Early

Do not wait until the entire task is complete to discover that the approach is wrong.

After meaningful milestones, run the narrowest relevant check.

Examples:

```text
Changed parser
    ↓
Run parser tests
    ↓
Changed API behavior
    ↓
Run endpoint tests
    ↓
Changed database migration
    ↓
Validate migration against appropriate environment/test database
    ↓
Changed UI
    ↓
Run component tests + browser/visual verification
```

Fast feedback prevents long chains of incorrect edits.

---

# 5. Repair

Verification failures are feedback.

When something fails:

### Read

Read the complete error rather than reacting to the first line.

### Classify

Determine whether the failure is:

* caused by the change
* caused by an incorrect assumption
* pre-existing
* environmental
* flaky
* unrelated

### Diagnose

Trace the failure to its root cause.

### Correct

Make the smallest fix that addresses the cause.

### Re-verify

Run the relevant check again.

Do not blindly modify code until the test passes.

---

# 6. Review

After implementation and verification, review the final state independently.

Inspect:

* final diff
* correctness
* edge cases
* security
* authorization
* data integrity
* compatibility
* concurrency
* tests
* performance
* observability
* scope

The final review should answer:

> "What could still go wrong?"

This is different from asking:

> "Does the code look reasonable?"

---

# 7. Human Review

AI should not require humans to supervise every edit.

Human attention is most valuable at decision boundaries:

* architecture
* product behavior
* security-sensitive choices
* destructive data changes
* public API changes
* significant dependency changes
* migration strategy
* final diff
* unresolved uncertainty

The agent should handle routine mechanical work and verification.

The human should retain ownership of consequential decisions.

---

# 8. Repository Context

The repository should contain durable engineering context.

Use:

```text
AGENTS.md
CLAUDE.md
.claude/rules/*.md
.claude/skills/*
```

for different layers of guidance.

## AGENTS.md

Shared, cross-tool engineering contract.

Use it for:

* architecture expectations
* testing standards
* security principles
* repository conventions
* completion requirements

## CLAUDE.md

Claude Code-specific operating instructions. Always loaded by the Claude Code extension/CLI for this repository.

Use it for:

* Claude's workflow
* context management
* subagent conventions
* Claude-specific tools and assets

## Claude Rules

Use `.claude/rules/*.md` for domain-scoped reference material. These are not auto-loaded — CLAUDE.md should tell the agent which one to open for a given task type.

Examples:

```text
architecture.md
frontend.md
backend.md
database.md
testing.md
debugging.md
review.md
security-review.md
```

Keep rules focused.

Do not create one giant instruction file containing every possible rule.

---

# 9. Rules vs Procedures vs Agents

Use the right mechanism for the right problem.

## Rules

Rules define constraints.

Examples:

* Always validate authorization server-side.
* Follow repository error-handling conventions.
* Run tests before completion.

## Skills

Skills define repeatable procedures, invoked as slash commands in Claude Code (e.g. `/code-review`).

Examples:

* Investigate a production incident.
* Review a migration.
* Perform a UI verification pass.
* Prepare a release.

## Subagents

Subagents provide specialized reasoning, defined under `.claude/agents/`.

Examples:

* security reviewer
* database reviewer
* frontend reviewer
* architecture reviewer

## Hooks and CI

Hooks (`.claude/settings.json`) and CI enforce deterministic requirements.

Examples:

* formatting
* type checking
* tests
* secret detection
* generated-file validation
* policy enforcement

Do not rely on an AI instruction for something that can be mechanically enforced.

---

# 10. Task Design

Good AI tasks contain:

* desired outcome
* context
* requirements
* non-goals
* acceptance criteria
* constraints
* verification expectations

Bad task:

```text
Fix the billing system.
```

Better task:

```text
When a subscription cancellation request is repeated, the operation
must remain idempotent and must not create duplicate cancellation
events.

Preserve the existing API contract.

Add a regression test covering repeated requests.

Run the relevant billing tests and typecheck.
```

Specificity should describe behavior, not dictate unnecessary implementation.

---

# 11. Long-Running Tasks

For tasks that span many files or long sessions, maintain durable state.

Useful artifacts include:

```text
docs/ai/
    task.md
    plan.md
    progress.md
    decisions.md
    verification.md
    handoff.md
```

The exact location is repository-dependent.

The purpose is to prevent critical context from existing only inside the agent's current conversation.

## Progress State

Record:

* completed work
* remaining work
* decisions
* failed approaches
* verification results
* known risks
* next action

A future agent should be able to continue without reconstructing the entire history.

---

# 12. Parallel Agents

Parallelize only genuinely independent work.

Good candidates:

```text
Agent A → implementation
Agent B → independent security review
Agent C → test analysis
```

Poor candidates:

```text
Agent A → edits API
Agent B → simultaneously edits same API
Agent C → simultaneously refactors same service
```

Parallel agents should have:

* clear ownership
* non-overlapping files where possible
* explicit outputs
* a defined integration point

More agents do not automatically produce more progress.

---

# 13. Model Diversity

Use different models or reviewers when a problem benefits from independent reasoning.

Examples:

* primary agent implements
* second model reviews architecture
* security-focused agent reviews attack surface
* test-focused agent checks regression coverage

Independent reasoning is particularly valuable for:

* difficult bugs
* security-sensitive changes
* architecture
* migrations
* large refactors

Do not use model diversity merely to generate more opinions.

---

# 14. Verification as Feedback

Tests are not just a final gate.

Treat verification as an active feedback loop:

```text
Hypothesis
    ↓
Implementation
    ↓
Verification
    ↓
Observed behavior
    ↓
Updated hypothesis
    ↓
Correction
```

This is especially important for debugging.

A failing test should update the agent's model of the system.

---

# 15. Debugging Workflow

For bugs:

1. Reproduce.
2. Capture the actual failure.
3. Establish a baseline.
4. Trace the execution path.
5. Form explicit hypotheses.
6. Gather evidence.
7. Identify root cause.
8. Make the smallest correction.
9. Add regression protection.
10. Re-run verification.

Avoid random patching.

A successful test is not proof that the root cause was understood.

---

# 16. UI Work

For frontend tasks, functional verification is necessary but insufficient.

Verify:

* loading state
* success state
* empty state
* error state
* disabled state
* keyboard interaction
* responsive behavior
* accessibility
* navigation
* visual consistency

When browser tooling is available, use it to verify the actual rendered result.

Do not assume that a component compiling means the feature is complete.

---

# 17. Database Changes

Database changes require additional caution.

Before changing schema or migrations:

* inspect existing schema
* inspect migration conventions
* identify affected data
* consider existing production data
* consider deployment ordering
* consider backwards compatibility
* consider rollback/recovery

For risky changes, prefer:

```text
Expand
  ↓
Migrate
  ↓
Verify
  ↓
Contract
```

Avoid destructive one-step changes when a staged migration is practical.

---

# 18. Security

Security-sensitive code requires explicit verification.

Check:

* authentication
* authorization
* object ownership
* tenant boundaries
* input validation
* injection
* secrets
* sensitive data
* sessions/tokens
* external requests
* file handling
* abuse/rate limits

Security behavior should be tested through negative cases, not just successful flows.

---

# 19. Git and Diff Hygiene

Before completion:

* inspect the final diff
* remove debugging artifacts
* remove temporary files
* remove accidental formatting changes
* verify generated files
* verify migrations
* check new dependencies
* confirm no user changes were overwritten
* confirm scope matches the task

The final diff is the artifact being reviewed.

---

# 20. Definition of Done

A task is done when:

* intended behavior is implemented
* existing contracts are preserved
* relevant edge cases are handled
* appropriate tests exist
* verification passes
* security implications are addressed
* UI behavior is verified where applicable
* final diff is reviewed
* no unexplained failures remain
* remaining risks are documented

"Code was written" is not a completion state.

---

# 21. Continuous Improvement

The agent workflow itself should improve over time.

When an agent repeatedly makes the same mistake:

1. Identify the repeated failure.
2. Determine whether it is caused by missing context, missing procedure, or missing enforcement.
3. Add the smallest durable improvement.

Examples:

```text
Repeated mistake
    ↓
Missing repository rule
    ↓
AGENTS.md / .claude/rules/*.md

Repeated procedure error
    ↓
Missing workflow
    ↓
.claude/skills/*

Repeated deterministic failure
    ↓
Missing enforcement
    ↓
Hook / CI check
```

Do not keep expanding prompts to compensate for failures that can be mechanically prevented.

---

# Operating Model

The recommended loop is:

```text
                 ┌──────────────┐
                 │     Task     │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │    Explore   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │     Plan     │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │  Implement   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │    Verify    │
                 └──────┬───────┘
                        ↓
                 ┌──────▼───────┐
                 │   Passed?    │
                 └───┬──────┬───┘
                     │Yes   │No
                     ↓      ↓
                 ┌──────┐ ┌──────────────┐
                 │Review│ │    Repair    │
                 └──┬───┘ └──────┬───────┘
                    │             │
                    │             └──────→ Verify
                    ↓
                 Complete
```

## Final Principle

**Build an engineering system around the coding agent.**

The goal is not to write a better prompt.

The goal is to create a repository where an agent can understand the code, make bounded changes, verify its work, repair failures, and leave behind an auditable result.
