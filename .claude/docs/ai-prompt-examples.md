# AI Prompt Examples

These examples are designed for agentic coding workflows with Claude Code.

They emphasize:

* outcome over implementation prescription
* repository-aware investigation
* explicit constraints
* acceptance criteria
* verification
* bounded autonomy
* evidence-driven debugging

Replace the examples with repository-specific terminology when useful.

---

# 1. New Feature

```text
Implement [FEATURE].

Goal:
[Describe the user-visible or system-visible outcome.]

Requirements:
- [Requirement]
- [Requirement]
- [Requirement]

Non-goals:
- [Non-goal]
- [Non-goal]

Before editing:
- Inspect the existing implementation and related tests.
- Identify the existing abstraction that should own this behavior.
- Follow repository instructions and applicable rules.

Implementation:
- Reuse existing patterns and abstractions.
- Make the smallest sufficient change.
- Do not perform unrelated refactoring.

Verification:
- Add or update regression coverage.
- Run the narrowest relevant tests first.
- Then run the broader checks appropriate to the affected area.
- Review the final diff for unrelated changes.

At completion, report:
1. What changed.
2. Files changed.
3. Verification performed.
4. Any remaining risks or limitations.
```

---

# 2. Bug Fix

```text
Investigate and fix this bug:

[BUG DESCRIPTION]

Observed behavior:
[What happens]

Expected behavior:
[What should happen]

Before changing code:

1. Reproduce the failure if possible.
2. Read the actual error/output.
3. Trace the relevant execution path.
4. Inspect existing tests and related code.
5. Form a root-cause hypothesis.

Do not make speculative patches.

Once the root cause is established:

- Make the smallest sufficient fix.
- Preserve existing behavior outside the affected case.
- Add a regression test that would have failed before the fix.
- Run the focused test.
- Run relevant broader verification.
- Review the final diff.

If the failure cannot be reproduced, explain the evidence used to identify the cause and what remains uncertain.
```

---

# 3. Debugging a Failing Test

```text
Investigate the failing test:

[TEST / COMMAND]

Failure:
[ERROR]

Do not immediately modify the test.

First determine:

- What behavior the test is asserting.
- Whether the failure is caused by the current code.
- Whether the failure is environmental or pre-existing.
- What changed recently.
- What the actual runtime state is.

Use evidence from:
- stack traces
- logs
- test output
- source code
- related tests
- recent changes

Identify the root cause before changing code.

Then:
1. Make the smallest corrective change.
2. Re-run the failing test.
3. Run related tests.
4. Explain the root cause and verification result.

Do not weaken assertions merely to make the test pass.
```

---

# 4. Refactoring

```text
Refactor [AREA] to [DESIRED STRUCTURAL OUTCOME].

Behavior must remain unchanged unless explicitly stated below.

Before editing:
- Map the current implementation.
- Identify all callers and consumers.
- Identify public or externally observable contracts.
- Identify relevant tests.

Constraints:
- Preserve behavior.
- Preserve API compatibility.
- Reuse existing abstractions.
- Do not introduce speculative generalization.
- Keep the diff focused.

Verification:
- Run the existing relevant tests.
- Add tests only where the refactor exposes a previously unprotected contract.
- Run typecheck/build as appropriate.
- Review the final diff for accidental behavioral changes.

If the proposed refactor requires a behavioral change, stop and explain it before proceeding.
```

---

# 5. Architecture Change

```text
Evaluate and implement the architectural change:

[DESCRIPTION]

First explore the current architecture.

Identify:
- ownership boundaries
- dependency direction
- existing abstractions
- data flow
- API boundaries
- failure boundaries
- relevant tests
- deployment/runtime implications

Before implementation, propose a concise plan explaining:

1. Current architecture.
2. Problem with the current design.
3. Proposed change.
4. Why it fits the existing architecture.
5. Alternatives considered.
6. Migration/compatibility implications.
7. Verification strategy.

Do not implement a large architectural change until the plan is coherent.

During implementation:
- preserve existing contracts where possible
- avoid unrelated refactoring
- keep changes reversible
- add appropriate tests

Finish with a review of architectural risks and remaining tradeoffs.
```

---

# 6. Database Migration

```text
Implement the database change:

[SCHEMA CHANGE]

Before editing:

- Inspect the current schema.
- Inspect migration conventions.
- Identify affected application code.
- Identify existing production-data assumptions.
- Determine whether the change is backwards compatible.
- Identify deployment ordering requirements.

Prefer a staged migration when necessary:

Expand → Migrate → Verify → Contract

Consider:
- existing rows
- NULL/default behavior
- constraints
- indexes
- query performance
- lock duration
- backfill size
- rollback/recovery
- old application versions

Add appropriate migration tests or validation.

Do not perform destructive changes merely because they are simpler.

Report:
- migration strategy
- compatibility considerations
- verification performed
- rollback/recovery considerations
```

---

# 7. API Change

```text
Change the API behavior:

[API CHANGE]

Before editing:
- Find the route/controller/handler.
- Find request and response schemas.
- Find callers and consumers.
- Find API tests.
- Check authentication and authorization.
- Check compatibility requirements.

Requirements:
- [Requirement]
- [Requirement]

Preserve:
- existing authentication
- authorization boundaries
- error semantics unless intentionally changed
- compatibility for existing consumers where required

Add regression coverage for:
- success
- invalid input
- unauthorized access
- relevant edge cases

Verify with the focused API tests and broader checks appropriate to the service.
```

---

# 8. Frontend Feature

```text
Implement this UI feature:

[FEATURE]

Before editing:
- Inspect the existing design system.
- Find reusable components.
- Identify the existing data-fetching/state pattern.
- Check routing and URL conventions.
- Inspect nearby screens for interaction patterns.

Requirements:
- [Requirement]
- [Requirement]

The UI must handle:
- loading
- success
- empty
- error
- disabled/in-progress states where relevant

Also verify:
- keyboard accessibility
- responsive behavior
- semantic HTML
- focus behavior
- existing visual conventions

Do not introduce a new component pattern when an existing one is appropriate.

Verification:
- component/unit tests where useful
- relevant integration tests
- browser verification when available
- final visual review
```

---

# 9. Security-Sensitive Change

```text
Implement:

[SECURITY-SENSITIVE CHANGE]

Treat all external input as untrusted.

Before editing, identify:
- authentication boundary
- authorization boundary
- trusted vs untrusted data
- sensitive resources
- attack surface
- existing security mechanisms

Explicitly consider:
- privilege escalation
- object-level authorization
- injection
- secrets
- sensitive data exposure
- session/token handling
- SSRF
- file/path handling
- abuse/rate limiting
- error/log leakage

Add negative-path tests.

Do not weaken an existing security control to make the implementation easier.

If the security model is ambiguous, stop and explain the ambiguity rather than guessing.
```

---

# 10. Code Review

```text
Review the current changes as an adversarial engineer.

Do not rewrite the code.

Inspect:
- complete diff
- changed behavior
- callers/consumers where relevant
- tests
- security boundaries
- data integrity
- concurrency
- compatibility
- performance

Look for real defects, not stylistic preferences.

For every finding provide:

Severity:
Location:
Problem:
Impact:
Recommendation:

Prioritize issues that could reach users or corrupt system state.

If no material issues are found, say so explicitly.

Do not invent hypothetical vulnerabilities without a plausible execution path.
```

This maps directly onto the `code-review` skill in `.claude/skills/` — invoke it with `/code-review` instead of retyping this prompt.

---

# 11. Independent Review

Use a separate agent/model after implementation.

```text
Act as an independent reviewer.

You did not implement this change.

Review the current diff and relevant surrounding code.

Your goal is to find defects the implementing agent may have missed.

Prioritize:
1. correctness
2. security
3. data integrity
4. compatibility
5. concurrency
6. error handling
7. test gaps
8. performance

Do not optimize for the number of comments.

For each finding:
- severity
- location
- concrete problem
- impact
- recommended fix

If the implementation appears sound, report that clearly.

Do not modify files.
```

---

# 12. UI Verification Agent

```text
Verify the implemented UI feature in the browser.

Feature:
[FEATURE]

Check:

1. Initial/loading state
2. Successful state
3. Empty state
4. Error state
5. Disabled/in-progress state
6. Keyboard interaction
7. Focus behavior
8. Responsive layouts
9. Navigation/URL behavior
10. Visual consistency with the existing application

Do not change code during the first verification pass.

Report:
- observed behavior
- failures
- screenshots/evidence if available
- likely cause
- recommended next action
```

---

# 13. Root-Cause Debugging

```text
Find the root cause of:

[FAILURE]

Use an evidence-driven debugging process.

1. Reproduce.
2. Establish the baseline.
3. Inspect the complete error.
4. Trace the execution path.
5. Form multiple plausible hypotheses.
6. Gather evidence that distinguishes them.
7. Identify the most likely root cause.
8. Fix only after the cause is understood.
9. Add regression protection.
10. Verify.

Do not:
- randomly edit code
- suppress errors
- weaken tests
- change unrelated components
- stop at the first plausible explanation

At the end, explain:
- root cause
- why the old code failed
- why the fix works
- verification performed
```

---

# 14. Long-Running Task

```text
Work on this task autonomously:

[TASK]

Operate in bounded phases:

Phase 1 — Explore
Phase 2 — Plan
Phase 3 — Implement
Phase 4 — Verify
Phase 5 — Repair failures
Phase 6 — Review

Maintain durable task state if the work spans a long session.

Record:
- completed work
- remaining work
- important decisions
- failed approaches
- verification results
- unresolved risks

Do not expand scope without evidence that it is necessary.

Stop when:
- acceptance criteria are satisfied
- relevant verification passes
- final diff has been reviewed
- remaining risks are documented

If blocked, state the blocker precisely instead of guessing.
```

---

# 15. Parallel Work

```text
Split this task into independent workstreams where useful:

[TASK]

Before parallelizing, identify dependencies.

Possible workstreams:
- implementation
- tests
- security review
- documentation
- independent analysis

Do not have multiple agents modify the same files unless coordination is explicit.

Each workstream must report:
- what it inspected
- what it changed
- what it verified
- remaining concerns

Integrate results only after reviewing for conflicts and consistency.
```

---

# 16. Minimal Change

Useful when an agent starts expanding scope.

```text
Solve the stated problem with the smallest sufficient change.

Do not:
- refactor unrelated code
- rename unrelated symbols
- reorganize directories
- upgrade dependencies
- rewrite neighboring modules
- "clean up" unrelated issues

If a broader change is genuinely necessary, explain:
1. why it is necessary
2. what dependency requires it
3. what additional risk it introduces

Otherwise keep the change local.
```

---

# 17. Investigate Before Acting

Useful when the repository is unfamiliar.

```text
Do not edit yet.

First investigate the repository and the requested behavior.

Determine:
- relevant files
- current execution path
- existing abstractions
- related tests
- configuration
- dependencies
- security boundaries
- likely implementation location

Then provide:
1. current behavior
2. likely cause/design
3. proposed change
4. verification plan

Wait for implementation only after the investigation is complete.
```

---

# 18. Test-Driven Change

```text
Implement this behavior:

[BEHAVIOR]

First identify the best existing test location.

Add a failing regression test that expresses the required behavior.

Then implement the smallest change that makes the test pass.

Afterward:
- run the focused test
- run related tests
- inspect the final diff
- check for edge cases

Do not weaken the test to accommodate the implementation.
```

---

# 19. Repair Loop

```text
The previous implementation failed verification.

Failure:
[FAILURE]

Treat the failure as evidence.

First determine:
- whether the failure is caused by the implementation
- what assumption was incorrect
- whether the failure exposes a deeper issue

Then:
1. identify root cause
2. make the smallest correction
3. rerun the focused check
4. rerun related verification
5. review the final state

Do not repeatedly patch symptoms without updating the underlying diagnosis.
```

---

# 20. Final Verification

```text
The implementation is believed to be complete.

Perform a final verification pass.

Check:

- acceptance criteria
- changed behavior
- edge cases
- security
- authorization
- data integrity
- compatibility
- tests
- typecheck
- lint
- build
- UI/browser behavior if applicable
- final diff
- accidental scope expansion

Do not modify code during the first review pass.

Report:
- verified
- failed
- not run
- remaining risk

Only claim completion based on actual evidence.
```

---

# 21. Completion Prompt

```text
Finish the task and provide a concise engineering completion report.

Include:

## Summary
What changed and why.

## Files
Meaningful files changed.

## Verification
Commands/checks actually run and their results.

## Tests
New or updated regression coverage.

## Risks
Compatibility, migration, deployment, security, or operational risks.

## Remaining Work
Anything intentionally deferred or unresolved.

Do not claim a check passed unless it was actually run.
```

---

# Prompt Design Principles

## Describe outcomes

Prefer:

```text
Add support for retrying failed webhook deliveries safely.
```

Over:

```text
Create a RetryWebhookService class with a retryWebhook() method.
```

The first lets the repository determine the correct architecture.

---

## State constraints

Useful constraints:

```text
Preserve the existing API contract.
```

```text
Do not change the database schema.
```

```text
Use the existing authentication mechanism.
```

```text
Do not add dependencies unless necessary.
```

---

## Define verification

Weak:

```text
Make sure it works.
```

Strong:

```text
Add regression coverage for duplicate requests and verify the
existing webhook test suite plus typecheck.
```

---

## Make uncertainty explicit

Useful:

```text
If the existing architecture does not support this cleanly, stop after
investigation and explain the constraint before introducing a new abstraction.
```

This prevents agents from confidently inventing architecture.

---

## Give autonomy boundaries

Good:

```text
You may modify any files necessary within the feature boundary.
Do not modify unrelated features.
```

Better than:

```text
Only edit these exact three files.
```

unless the exact file boundary is genuinely required.

---

## Prefer Evidence Over Confidence

Instead of:

```text
This is probably caused by caching. Fix the cache.
```

Use:

```text
Investigate why stale data is returned after the update.
Determine whether caching is the root cause before changing it.
```

This preserves the agent's ability to discover the actual cause.

---

# Anti-Patterns

Avoid prompts that encourage:

## Blind implementation

```text
Just code this quickly. Don't investigate.
```

## Unbounded autonomy

```text
Do whatever is necessary to make the entire application better.
```

## Premature implementation

```text
Create a new service for this.
```

before understanding the existing architecture.

## Test suppression

```text
Fix the implementation until all tests pass, even if tests need changing.
```

## Scope explosion

```text
While you're here, clean up the whole module.
```

## False certainty

```text
The bug is definitely in the cache.
```

when this has not been established.

---

# Recommended Default Prompt

When no specialized prompt is needed:

```text
Implement the requested change:

[TASK]

First inspect the repository and applicable instructions.

Before editing:
- understand the current behavior
- identify the relevant implementation
- inspect related tests
- identify important contracts and boundaries

Then:
1. formulate a concise plan
2. implement the smallest sufficient change
3. verify the changed behavior
4. repair any failures using evidence
5. review the final diff

Preserve existing architecture, security boundaries, and contracts.

Do not perform unrelated refactoring.

At completion, report:
- what changed
- files changed
- verification performed
- remaining risks or limitations

Do not claim verification that was not actually run.
```

# Final Principle

**The best AI prompt is not the one that tells the model how to write every line. It is the one that gives the model enough context, constraints, autonomy, and feedback to make good engineering decisions.**
