# AI Task Template

Use this template for any non-trivial task given to an AI coding agent.

The goal is to make the task sufficiently precise for autonomous execution while leaving implementation decisions to the agent when the repository already provides the appropriate patterns.

---

## Task

**What needs to change?**

Describe the desired outcome in terms of user-visible or system-visible behavior.

Do not prescribe implementation details unless they are part of the requirement.

```text
Example:

Add support for cancelling an active subscription from the account settings page.

A cancelled subscription should remain visible until the end of the
current billing period, but the user must not be charged for the next
period.
```

---

## Why

**Why is this change needed?**

Explain the problem, business reason, user need, or technical motivation.

```text
Example:

Customers currently have to contact support to cancel subscriptions.
The cancellation flow should be self-service while preserving the
existing billing-period semantics.
```

---

## Context

Relevant repository information:

* Related feature:
* Related files:
* Existing implementation:
* Relevant API:
* Relevant database tables:
* Existing tests:
* External systems:
* Known constraints:

Only include information that is known to be useful.

The agent should inspect the repository rather than treating this section as a complete map.

---

## Requirements

The implementation must:

* [ ] Requirement 1
* [ ] Requirement 2
* [ ] Requirement 3

Requirements should describe observable behavior or enforceable constraints.

Avoid vague requirements such as:

> "Make the code better."

Prefer:

> "Return a validation error when the requested quantity is zero or negative."

---

## Non-Goals

Do not change:

* Unrelated features
* Existing APIs unless required
* Database behavior unrelated to this task
* Styling outside the affected UI
* Dependencies unless necessary

Add task-specific exclusions when useful.

Explicit non-goals reduce accidental scope expansion.

---

## Acceptance Criteria

The task is complete when:

* [ ] Expected behavior works.
* [ ] Existing behavior remains intact.
* [ ] Relevant tests pass.
* [ ] New behavior has appropriate regression coverage.
* [ ] Error and edge cases are handled.
* [ ] Security/authorization requirements are satisfied.
* [ ] Relevant UI behavior has been verified when applicable.
* [ ] Final diff contains no unrelated changes.

Use observable criteria whenever possible.

---

## Constraints

Respect:

* Existing architecture
* Existing patterns and abstractions
* Existing API contracts
* Existing dependency choices
* Existing authentication/authorization model
* Existing database conventions
* Existing test conventions
* Repository instructions in `AGENTS.md` and `CLAUDE.md`
* Applicable rules in `.claude/rules/`

Do not introduce new infrastructure or abstractions unless the existing system cannot reasonably support the requirement.

---

## Investigation

Before editing:

1. Locate the relevant implementation.
2. Identify the execution path.
3. Inspect related tests.
4. Identify existing abstractions and conventions.
5. Check for callers/consumers of affected interfaces.
6. Identify security, persistence, compatibility, and concurrency implications.

Do not begin implementation based solely on filenames or assumptions.

---

## Plan

Before making significant changes, produce a concise implementation plan.

The plan should include:

1. What will change.
2. Where it will change.
3. Why that approach fits the existing architecture.
4. What tests will be added or updated.
5. How the result will be verified.

For small changes, a short plan is sufficient.

For large changes, break the plan into independently verifiable phases.

---

## Implementation Rules

While implementing:

* Prefer the smallest sufficient change.
* Reuse existing abstractions.
* Preserve established contracts.
* Avoid speculative refactoring.
* Keep unrelated cleanup out of the diff.
* Follow repository conventions.
* Treat external input as untrusted.
* Preserve security boundaries.
* Add regression coverage for changed behavior.
* Stop and investigate when assumptions prove incorrect.

Do not repeatedly patch symptoms without understanding the root cause.

---

## Verification

Run the narrowest useful verification first.

Typical order:

1. Focused test for changed behavior.
2. Related test suite.
3. Type checking.
4. Linting/static analysis.
5. Build.
6. Integration/e2e tests where relevant.
7. Browser/visual verification for UI changes.
8. Final diff review.

Do not claim success without actually running the relevant checks.

If a check cannot be run, state why.

---

## Failure and Repair

When verification fails:

1. Read the complete failure.
2. Determine whether the failure is caused by the change.
3. Reproduce or isolate the problem.
4. Identify the root cause.
5. Make the smallest corrective change.
6. Re-run the relevant verification.
7. Repeat only while progress remains measurable.

Do not weaken tests merely to make them pass.

Do not suppress errors without understanding them.

---

## Completion Report

When finished, report:

### Summary

What changed and why.

### Files Changed

List the meaningful files changed.

### Verification

List the commands/checks actually run and their results.

### Remaining Issues

Mention:

* Known failures
* Environment limitations
* Deferred work
* Unverified assumptions

If nothing remains, say so explicitly.

### Risk

Briefly describe any meaningful compatibility, migration, deployment, or operational risk.

---

## Task Example

```text
Task:
Add a password-confirmation step before deleting an account.

Why:
Account deletion is irreversible and currently requires only a single
button click.

Requirements:
- Require the current password before deletion.
- Reject incorrect passwords.
- Do not reveal whether the password or account state was the reason
  for a failure.
- Preserve the existing deletion workflow after successful confirmation.
- Add tests for successful deletion, incorrect password, and unauthenticated access.

Non-goals:
- Do not redesign account settings.
- Do not change the account deletion API unless required.
- Do not change password hashing.

Acceptance criteria:
- An authenticated user cannot delete the account without confirming
  the current password.
- Incorrect confirmation does not delete the account.
- Existing deletion tests continue to pass.
- New security regression tests pass.
- The final diff contains no unrelated changes.

Verification:
- Focused account-deletion tests
- Authentication/authorization tests
- Typecheck
- Lint
- Relevant integration tests
```

## Principle

**Give the agent a clear outcome, constraints, acceptance criteria, and verification target. Let the repository determine the implementation details whenever possible.**
