# AI Engineering Instructions

This repository is developed with AI-assisted engineering tools, including coding agents.

These instructions define the engineering standards that AI agents must follow when inspecting, modifying, testing, reviewing, and explaining changes in this repository.

The goal is not to make the agent produce code as quickly as possible.

The goal is to make the agent produce **correct, maintainable, verifiable software with the smallest sufficient change**.

This file is the engineering contract for this repository — the standards that apply regardless of which task is being worked on. Claude Code-specific operating guidance lives in `CLAUDE.md`, which should defer to this file rather than duplicate it.

---

# 1. Core Operating Principle

Treat the repository as the primary source of truth.

Before making consequential changes, inspect:

- the existing implementation
- surrounding architecture
- relevant tests
- configuration
- package/dependency definitions
- documentation
- existing patterns
- generated-code boundaries
- security boundaries
- API contracts
- persistence/data models where relevant

Do not invent repository conventions when the repository can reveal them.

Prefer:

> discover → understand → plan → implement → verify → review

over:

> prompt → guess → edit → hope

---

# 2. Before Changing Code

For trivial changes, use judgment and avoid unnecessary ceremony.

For non-trivial changes, first establish:

1. What the requested behavior actually is.
2. Where the behavior currently lives.
3. Which components participate in it.
4. Which existing implementation is the closest canonical example.
5. Which tests already cover the behavior.
6. Which interfaces or contracts must remain stable.
7. Which files are likely to change.
8. What could regress.
9. How success can be objectively verified.

Use repository search and inspection aggressively.

Do not start implementing merely because a task appears simple if important architectural context is unknown.

---

# 3. Repository Discovery

When exploring a repository, prioritize high-signal sources.

Typical discovery order:

1. root documentation
2. `AGENTS.md`
3. `CLAUDE.md` and `.claude/rules/`
4. package/project configuration
5. application entry points
6. relevant feature/module
7. tests
8. canonical neighboring implementations
9. generated/configuration files

Do not read the entire repository indiscriminately.

Use targeted exploration based on the task.

When multiple implementations appear possible, identify which one is canonical before copying or extending a pattern.

---

# 4. Planning

Non-trivial work should have a concise implementation plan before substantial modification.

A useful plan should state:

- intended behavior
- relevant architecture
- files likely to change
- implementation approach
- tests/verification
- important edge cases
- known risks
- consequential assumptions

The plan should be proportional to the task.

Do not create elaborate plans for trivial changes.

Do not use planning as a substitute for implementation.

If investigation reveals a consequential ambiguity, stop and ask rather than silently inventing product or architectural requirements.

---

# 5. Smallest Sufficient Change

Prefer the smallest change that completely satisfies the requirements.

This means:

- reuse existing abstractions when appropriate
- follow existing architectural patterns
- avoid speculative abstractions
- avoid unrelated refactoring
- avoid drive-by formatting
- avoid unnecessary dependency changes
- avoid renaming unrelated symbols
- avoid changing generated files manually
- avoid changing APIs unless required
- avoid changing behavior outside the task

"Smallest" does not mean "shortest code."

A slightly larger change may be preferable if it is materially safer, clearer, better tested, or more consistent with the existing architecture.

---

# 6. Existing Patterns

Before introducing a new pattern, search for an existing one.

Examples:

- existing API error handling
- existing validation
- existing state management
- existing database access
- existing authentication/authorization
- existing logging
- existing UI components
- existing test factories
- existing configuration mechanisms
- existing feature flags
- existing retry behavior
- existing observability

Do not introduce a second solution to a problem the repository already solves.

If an existing abstraction is inadequate, explain why before replacing or bypassing it.

---

# 7. Scope Control

Keep unrelated concerns separate.

Do not silently combine:

- feature development
- large refactors
- dependency upgrades
- formatting migrations
- architecture changes
- test-framework migrations
- unrelated bug fixes

If a change is genuinely required to complete the task, make the dependency explicit.

If an improvement is merely desirable, leave it out and mention it separately.

---

# 8. Dependencies

Do not add a dependency without justification.

Before adding one:

1. Check whether the repository already provides equivalent functionality.
2. Check whether the platform/runtime provides it.
3. Consider whether a small local implementation is safer.
4. Consider maintenance and security implications.
5. Consider bundle/build/runtime impact where applicable.
6. Explain the dependency if it materially affects the project.

Never add a dependency merely because it makes an implementation slightly more convenient.

---

# 9. APIs and Contracts

Treat externally observable behavior as a contract.

Before changing an API, consider:

- request shape
- response shape
- validation
- authentication
- authorization
- error behavior
- status codes
- retries
- idempotency
- backwards compatibility
- clients consuming the API
- versioning

Do not break an existing contract unless the task explicitly requires the change.

When a contract must change, identify all known consumers and update them deliberately.

---

# 10. Data and Persistence

Treat database and persistent-data changes as high risk.

Consider:

- existing production data
- schema constraints
- nullability
- indexes
- uniqueness
- foreign keys
- migration order
- rollback behavior
- backwards compatibility
- old application versions
- new application versions
- concurrent access
- data volume
- query performance

Never assume the database is empty.

Never assume migrations only run once in a clean environment.

Never directly manipulate production data as part of ordinary development.

---

# 11. Security

Treat the following as security-sensitive:

- authentication
- authorization
- sessions
- credentials
- API keys
- secrets
- payments
- personal data
- external input
- file uploads
- network requests
- database access
- privilege boundaries
- administrative operations

Never:

- expose secrets in source code
- print credentials in logs
- weaken authorization to make a test pass
- disable security controls merely to simplify development
- invent cryptographic primitives
- trust external input without validation
- assume client-side authorization is sufficient
- expose sensitive data unnecessarily

Prefer existing project security primitives.

---

# 12. Testing

Tests are part of implementation, not an optional final step.

For new behavior, add appropriate coverage.

For bug fixes, add a regression test when practical.

Tests should focus on observable behavior and important invariants rather than implementation details.

Consider:

- normal behavior
- edge cases
- failure behavior
- authorization boundaries
- malformed input
- concurrency where relevant
- backwards compatibility where relevant

Use the narrowest relevant test first.

Then expand validation when appropriate.

---

# 13. Verification

Never claim a task is complete without evidence.

Depending on the repository and task, verification may include:

- unit tests
- integration tests
- end-to-end tests
- type checking
- linting
- formatting checks
- build
- migration validation
- static analysis
- security checks
- browser/UI verification
- manual reproduction
- final diff inspection

Do not report:

> "This should work."

when the repository provides a way to verify it.

Prefer:

> "Implemented X. Ran Y and Z. Both passed."

If something could not be verified, say so explicitly.

---

# 14. Debugging

Do not immediately patch the first plausible cause.

Use an evidence-driven loop:

1. reproduce
2. observe
3. trace
4. form hypotheses
5. gather evidence
6. identify root cause
7. make the smallest appropriate fix
8. add regression coverage
9. reproduce again
10. run broader validation

Do not confuse correlation with root cause.

Do not repeatedly make speculative changes without updating the hypothesis.

If repeated fixes fail, stop and reconsider the model of the problem.

---

# 15. UI Development

For UI work, code correctness is not sufficient.

Consider:

- loading states
- empty states
- error states
- disabled states
- success states
- responsive behavior
- keyboard navigation
- focus management
- semantic HTML
- accessible names
- contrast
- existing design system
- interaction behavior

Reuse existing UI primitives before creating new ones.

For meaningful UI changes, visually verify the result when tooling permits it.

Do not claim a UI implementation is correct solely because it compiles.

---

# 16. Generated Files

Identify generated files before editing.

Prefer modifying the source/template/schema and regenerating output.

Do not manually edit generated files unless:

- the task explicitly requires it
- generation is unavailable
- the repository's process requires it

If generated output changes, verify that the change is reproducible.

---

# 17. Git and Diff Hygiene

Before completion, inspect the final diff.

Check for:

- unintended files
- debugging statements
- temporary code
- commented-out experiments
- accidental formatting changes
- generated artifacts
- secrets
- unrelated refactoring
- incomplete TODOs
- missing tests

The final diff should tell a coherent story about the task.

---

# 18. Agent Autonomy

Agents should be autonomous within clearly defined boundaries.

The agent should normally be allowed to:

- inspect the repository
- search code
- read documentation
- modify relevant files
- run tests
- run validation
- repair failures
- inspect diffs

The agent should pause for human input when:

- requirements are materially ambiguous
- a consequential architecture decision is required
- a destructive migration is proposed
- security posture would materially change
- a public API contract must unexpectedly change
- a large unrelated refactor becomes necessary
- requirements conflict
- the requested behavior appears unsafe

Do not ask the user for information that can be discovered from the repository.

Do not repeatedly ask for approval for routine implementation details.

---

# 19. Failure Recovery

When validation fails:

1. Read the complete failure.
2. Determine whether the failure is caused by the change.
3. Identify the smallest repair.
4. Apply the repair.
5. Re-run the relevant validation.
6. Continue until the acceptance criteria are satisfied or a genuine blocker is identified.

Do not simply suppress failing tests.

Do not weaken assertions to make tests pass.

Do not delete tests because they expose a bug.

Do not change unrelated infrastructure merely because a local command fails.

---

# 20. Human Review

Human attention should concentrate on high-leverage decisions.

Humans should primarily review:

- requirements
- architecture
- security-sensitive changes
- data migrations
- public contracts
- consequential tradeoffs
- final behavior
- final diff

Agents should handle repetitive execution and evidence gathering where practical.

The objective is not to remove humans from engineering.

The objective is to move humans toward decisions where their judgment has the highest value.

---

# 21. Completion Report

When completing a non-trivial task, report:

## Summary

What changed.

## Files

Which important files changed and why.

## Verification

Exactly what was run and whether it passed.

## Decisions

Important implementation or architectural decisions.

## Risks

Known limitations or remaining uncertainty.

## Follow-up

Only genuinely useful follow-up work.

Do not produce vague completion statements.

---

# 22. Rule Maintenance

These instructions should evolve from observed engineering failures.

If an agent repeatedly makes the same mistake:

1. determine whether the mistake is deterministic or judgment-based
2. if deterministic, prefer tooling/CI
3. if judgment-based, encode the lesson in the appropriate rule
4. keep the rule concise
5. remove rules that no longer provide value

Do not turn this file into an encyclopedic style guide.

The repository's actual tooling should enforce deterministic behavior wherever possible.

---

# 23. Priority

When instructions conflict, use this priority:

1. explicit user requirements
2. system/platform constraints
3. repository architecture and contracts
4. security and correctness
5. project-specific AI instructions
6. technology-specific conventions
7. stylistic preferences

When a conflict cannot be resolved safely, ask for clarification.
