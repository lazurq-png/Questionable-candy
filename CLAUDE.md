# CLAUDE.md

# Claude Code Operating Instructions

This file contains Claude Code-specific instructions.

The repository-wide engineering contract is defined in `AGENTS.md`. Read and follow it first.

This file defines how Claude should operate within that contract.

---

## 1. Operating Model

Use the following default loop for non-trivial engineering work:

**Explore → Plan → Implement → Verify → Review**

When verification fails:

**Repair → Verify → Review**

Do not skip exploration simply because the requested change appears straightforward if the task touches unfamiliar or interconnected code.

Do not produce a long plan for trivial changes.

Match investigation depth to task risk.

---

## 2. Start With Repository Context

Before implementing a significant task:

1. Read `AGENTS.md`.
2. Inspect the relevant project structure.
3. Locate the existing implementation.
4. Locate related tests.
5. Search for similar patterns.
6. Inspect relevant configuration.
7. Determine the smallest appropriate change.

Use repository evidence rather than assumptions about frameworks or conventions.

If the repository contains more specific instructions in nested directories, follow those instructions for files in their scope.

If the task touches a specific domain, read the matching reference in `.claude/rules/` before implementing:

* `.claude/rules/architecture.md` — boundaries, layering, refactors
* `.claude/rules/frontend.md` — UI, accessibility, state, browser-facing work
* `.claude/rules/backend.md` — APIs, services, validation, errors, transactions
* `.claude/rules/database.md` — schemas, migrations, persistence, data integrity
* `.claude/rules/testing.md` — coverage strategy, flaky tests, definition of done
* `.claude/rules/debugging.md` — evidence-driven failure diagnosis
* `.claude/rules/review.md` — adversarial review of a finished diff
* `.claude/rules/security-review.md` — authn/authz, secrets, payments, external input

These are not auto-loaded — open the one(s) relevant to the task based on what the work touches.

---

## 3. Exploration

Exploration should answer the questions necessary to make a good implementation decision.

Prioritize:

* relevant symbols
* callers
* implementations
* tests
* configuration
* data flow
* API boundaries
* error handling
* neighboring patterns

Avoid reading large numbers of unrelated files.

Do not start editing simply because you have found one plausible implementation.

---

## 4. Planning

Create a plan before substantial implementation when the task involves:

* multiple files
* architectural changes
* database changes
* external integrations
* security-sensitive behavior
* complicated debugging
* uncertain ownership
* non-trivial migrations

A useful plan contains:

* current behavior
* desired behavior
* affected components
* implementation approach
* verification strategy
* risks
* open questions

The plan should be actionable rather than descriptive.

---

## 5. Implementation

Implement the smallest sufficient change.

Prefer existing:

* utilities
* components
* services
* repositories
* validation
* error handling
* state-management patterns
* API conventions

Avoid introducing a new abstraction unless the existing architecture cannot reasonably support the requested behavior.

Do not mix unrelated cleanup into feature work.

---

## 6. Use the Repository as Persistent Memory

Important project knowledge should live in the repository.

Use:

* `AGENTS.md`
* `CLAUDE.md`
* `.claude/rules/`
* documentation
* architecture records
* task plans
* handoffs

for durable knowledge.

Do not rely on the assumption that previous conversational context will remain available.

When a long task becomes too large for the current context, preserve the important state before continuing.

---

## 7. Context Management

Prefer targeted context over indiscriminate context.

Search for the exact:

* function
* class
* component
* endpoint
* error
* schema
* test
* configuration value

that matters.

Read surrounding code only when needed to understand behavior.

Before making a large edit, confirm that the relevant implementation and its callers are understood.

Do not repeatedly rediscover information that can be captured in a durable task artifact.

---

## 8. Subagents

Use specialized subagents when the task benefits from independent investigation or review.

Good uses include:

* repository exploration
* architecture investigation
* security review
* test analysis
* independent code review
* isolated research

Do not delegate tiny tasks merely to increase parallelism.

When using multiple agents:

* give each a narrow objective
* provide relevant context
* avoid overlapping edits
* prefer independent investigation over competing modifications
* synthesize results before implementation

For high-risk changes, an independent reviewer should ideally evaluate the implementation without relying on the builder's assumptions.

---

## 9. Verification

Verification is mandatory for meaningful code changes.

Choose checks appropriate to the change:

* targeted tests
* type checking
* linting
* formatting
* build
* integration tests
* end-to-end tests
* browser verification
* migration checks
* security checks

Start with the narrowest useful verification.

Expand verification when the change has broader impact.

Never report a verification result that was not actually observed.

---

## 10. Debugging

When a test, command, or runtime behavior fails:

1. reproduce it
2. inspect the exact failure
3. identify the relevant execution path
4. form a hypothesis
5. gather evidence
6. make the smallest fix
7. rerun verification

Avoid random trial-and-error edits.

If the same strategy fails repeatedly, stop and reassess the hypothesis.

---

## 11. Long-Running Tasks

For large tasks, maintain durable progress.

A useful task state includes:

* objective
* current understanding
* decisions made
* files changed
* remaining work
* verification status
* unresolved risks

Do not keep critical state exclusively in the conversation.

When handing work to another agent or resuming after interruption, leave enough information for the next agent to continue without reconstructing the entire investigation.

---

## 12. Parallelization

Parallelize independent work when it reduces total task time.

Examples:

* one agent maps architecture
* one agent investigates tests
* one agent performs security review
* one agent evaluates an isolated subsystem

Do not have multiple agents modify the same files unless the workflow explicitly supports conflict resolution.

For parallel implementation, use isolated worktrees or equivalent isolation.

---

## 13. Code Review

Before declaring substantial work complete, review the resulting diff.

Ask:

* Does this actually solve the requested problem?
* Did the implementation follow existing architecture?
* Did it introduce unnecessary complexity?
* Are edge cases covered?
* Are contracts preserved?
* Are errors handled correctly?
* Are security boundaries intact?
* Are tests meaningful?
* Did unrelated files change?
* Is there anything a skeptical reviewer would question?

Review the final state, not merely the edits made during implementation.

---

## 14. Minimality

Minimality means avoiding unnecessary complexity, not avoiding necessary code.

Prefer:

* direct solutions
* established project patterns
* small interfaces
* localized changes
* explicit behavior

Avoid:

* speculative extensibility
* premature abstractions
* unnecessary wrappers
* broad refactors
* unrelated dependency changes

---

## 15. Generated Files

Identify the source of truth before modifying generated output.

If generated code changes:

1. modify the source
2. run the generator
3. inspect the output
4. verify it

Do not manually patch generated artifacts unless explicitly required.

---

## 16. Human Interaction

Do not ask for approval for ordinary implementation decisions that fall clearly within the task.

Ask when the task requires a material product or architecture decision that cannot reasonably be inferred.

Examples:

* two incompatible interpretations of requirements
* destructive database behavior
* breaking public API changes
* irreversible external operations
* unclear security requirements

When asking, explain the actual decision and its consequences rather than asking a vague "what should I do?"

---

## 17. Final Response

For meaningful engineering tasks, provide a concise completion report:

### Summary

What changed.

### Verification

What was run and what passed or failed.

### Notes

Important implementation or compatibility considerations.

### Remaining Issues

Only include genuine unresolved items.

Do not include generic statements such as "everything should work" without evidence.

---

## 18. Claude-Specific Assets

This repository's `.claude/` directory is structured as follows:

```text
.claude/
├── rules/      — domain-specific reference docs (see §2), opened on demand
├── skills/     — reusable procedural workflows, invoked as slash commands
├── docs/       — supporting human-readable process docs (workflow, task
│                 template, prompt patterns) — not auto-loaded
├── scripts/    — validate.example: the repository's validation entry point
└── settings.json  — permissions/hooks, if this project defines any
```

Use `.claude/skills/code-review/` for an adversarial review pass over a diff —
see §13 for when to run it.

Add `.claude/agents/` for specialized subagents if the repository's task mix
justifies dedicated ones (e.g. a standing security-reviewer).

Keep these complementary to `AGENTS.md`.

Do not duplicate the entire repository engineering contract in Claude-specific files.

---

# Default Claude Behavior

Unless the task explicitly calls for another approach:

**Explore the relevant system.
Plan proportional to risk.
Implement the smallest sufficient change.
Verify with evidence.
Review the final diff.
Report what actually happened.**
