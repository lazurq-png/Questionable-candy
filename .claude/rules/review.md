# Code Review Rules

Open this before declaring a non-trivial task complete, to review your own diff as a skeptical senior engineer would. The goal is to find concrete problems, not to praise the implementation. Do not modify files during this pass unless a finding is being fixed as a separate, explicit step.

---

## 1. Correctness

Look for:

- incorrect assumptions
- missing edge cases
- incorrect state transitions
- race conditions
- partial failures
- error handling problems
- incorrect defaults
- backwards compatibility issues
- broken invariants

Ask:

> What could make this implementation behave incorrectly even though the happy path works?

---

## 2. Security

Check:

- authentication
- authorization
- object-level access
- privilege escalation
- input validation
- injection
- SSRF
- secret exposure
- sensitive data exposure
- unsafe redirects
- insecure defaults
- cryptographic misuse

Do not invent vulnerabilities without evidence.

---

## 3. Data Integrity

Check:

- transactions
- duplicate writes
- deletion behavior
- migration safety
- concurrency
- stale state
- consistency between related records

---

## 4. Maintainability

Look for:

- unnecessary abstractions
- duplicated logic
- excessive complexity
- inconsistent patterns
- hidden coupling
- unrelated changes
- missing tests
- unclear ownership

Do not report style-only issues that automated tooling should catch.

---

## 5. Compatibility

Consider:

- existing API consumers
- old application versions
- stored data
- external integrations
- feature flags
- deployment sequencing

---

## 6. Findings

Only report actionable findings.

For each finding provide:

### Severity

Critical / High / Medium / Low

### Location

File and relevant code area.

### Problem

What is wrong.

### Impact

Why it matters.

### Recommendation

What should change.

---

## 7. Review Standard

A finding should be supported by evidence from:

- the code
- tests
- architecture
- contracts
- configuration
- documented requirements

Do not invent requirements.

Do not report hypothetical problems merely because something could theoretically be different.

---

## 8. Final Question

Before completing the review, ask:

> If this change reached production tomorrow, what is the most likely concrete failure I would regret not catching?

Investigate that possibility.
