# Testing Rules

Tests provide the feedback loop that allows coding agents to work autonomously. Open this when planning coverage or triaging test failures.

---

## Test Behavior

Prefer testing observable behavior and important invariants.

Avoid tests that unnecessarily lock implementation details.

A refactor should not break a test merely because an internal helper was renamed if the externally observable behavior is unchanged.

---

## New Features

For new behavior, consider coverage for:

- normal behavior
- important edge cases
- expected failures
- validation
- authorization
- persistence
- integration behavior
- UI interaction where relevant

Do not mechanically create tests for every line.

Test meaningful behavior.

---

## Bug Fixes

Whenever practical, create a regression test that demonstrates the original failure.

Preferred sequence:

```text
test fails
   ↓
fix
   ↓
test passes
```

This provides evidence that the fix addresses the actual bug.

---

## Test Selection

Start with the narrowest relevant test.

For example:

```text
specific test
    ↓
module tests
    ↓
integration tests
    ↓
full suite
```

Use broader validation when the change warrants it.

---

## Flaky Tests

Do not simply retry flaky tests indefinitely.

Investigate:

- timing
- shared state
- order dependence
- external services
- race conditions
- cleanup
- nondeterminism

A test that passes only after repeated retries is not reliable evidence.

---

## Test Failures

When a test fails:

1. read the failure
2. determine whether the change caused it
3. inspect the relevant implementation
4. identify root cause
5. repair the implementation or test as appropriate
6. rerun

Do not modify assertions simply to make the suite green.

---

## Definition of Done

A task is not complete merely because:

- code compiles
- one test passes
- the agent believes it is correct

Completion requires:

- acceptance criteria satisfied
- appropriate tests
- relevant validation
- final diff review

---

## Test Quality

Avoid:

- meaningless snapshot expansion
- excessive mocking
- testing private implementation details
- duplicate coverage without value
- tests that encode accidental behavior

Prefer tests that remain useful as the code evolves.
