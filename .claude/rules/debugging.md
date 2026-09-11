# Debugging Rules

Do not begin debugging by guessing at a patch. Use evidence.

---

## 1. Reproduce

First establish whether the problem can be reproduced.

Record:

- input
- environment
- expected behavior
- actual behavior
- relevant error
- frequency
- relevant state

If reproduction is impossible, identify what evidence is available instead.

---

## 2. Trace

Follow the actual execution path.

Inspect:

- entry point
- inputs
- transformations
- state changes
- external calls
- persistence
- error handling

Do not stop at the first suspicious line.

---

## 3. Hypothesize

Form plausible explanations.

A useful hypothesis should be testable.

Example:

> The request is authorized against the current user's tenant, but the database lookup is not scoped to that tenant.

This is better than:

> Something is wrong with permissions.

---

## 4. Gather Evidence

Use:

- logs
- stack traces
- tests
- targeted instrumentation
- code inspection
- database state
- network behavior
- browser behavior

Eliminate hypotheses based on evidence.

---

## 5. Root Cause

Do not patch symptoms when the underlying cause is identifiable.

Before changing code, be able to explain:

- what failed
- why it failed
- why the failure occurs
- why the proposed fix prevents recurrence

---

## 6. Fix

Make the smallest appropriate fix.

Avoid unrelated cleanup.

If the fix changes behavior, add or update regression coverage.

---

## 7. Verify

Verify the original failure again.

Then run broader validation as appropriate.

Preferred sequence:

```text
original failure
     ↓
fix
     ↓
original case passes
     ↓
regression test passes
     ↓
broader validation
```

---

## 8. Repeated Failure

If several attempted fixes fail:

Stop patching.

Reassess:

- the root-cause hypothesis
- assumptions
- environment
- reproduction
- architecture
- test validity

Repeated unsuccessful patches are evidence that the current model is probably wrong.

---

## 9. Completion Report

For significant debugging work, report:

- root cause
- evidence
- fix
- regression coverage
- validation
- remaining uncertainty
