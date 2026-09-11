---
name: code-review
description: Adversarial review of the current diff for correctness, security, data-integrity, and compatibility defects. Use when the user asks to review a change, check a PR, or run a Bugbot-style pass before merging. Optimizes for high-signal findings, not comment count.
---

# Code Review

Act as an adversarial reviewer. The goal is to find real defects that could reach users, compromise security, corrupt data, break compatibility, or create difficult operational failures — not to comment on style.

Do not modify files during this pass. Report findings; let the user or a follow-up task decide what to fix.

## Review priorities, in order

1. Correctness
2. Security
3. Data integrity
4. API and behavioral compatibility
5. Concurrency and race conditions
6. Error handling and failure recovery
7. Test coverage for changed behavior
8. Performance and resource usage
9. Maintainability
10. Style — only when it affects correctness or maintainability materially

Do not spend review budget on cosmetic preferences.

## Before producing findings

- Read the complete diff.
- Identify the intended behavior.
- Inspect nearby code when needed to understand contracts.
- Check callers and consumers when an interface changes.
- Check tests that exercise the affected behavior.
- Consider configuration, migrations, and generated artifacts when relevant.

Do not review individual lines without understanding their surrounding behavior.

## Correctness

Look for: incorrect conditions, missing edge cases, wrong assumptions about state, broken invariants, incorrect error handling, lost return values, incorrect defaults, null/undefined handling, async ordering problems, resource lifecycle mistakes, incorrect state transitions, partial updates, retry bugs.

Prefer concrete defects over speculative concerns.

## Security

Pay particular attention to: authentication bypass, missing authorization, object-level authorization failures, privilege escalation, trusting client-controlled ownership/role data, injection, unsafe HTML or script handling, SSRF, path traversal, unsafe file handling, secret exposure, sensitive data leakage, insecure redirects, weak webhook verification, missing rate limits on sensitive operations, session/token mistakes.

Do not report a security issue merely because a pattern can theoretically be dangerous — explain the actual path by which the change creates risk. See `.claude/rules/security-review.md` for the fuller checklist.

## Data integrity

Check: database migrations, destructive schema changes, incorrect defaults, data loss, partial writes, transaction boundaries, duplicate writes, idempotency, concurrent updates, backfill correctness, ordering assumptions, inconsistent reads/writes.

## Compatibility

Check whether the change unintentionally breaks: public APIs, internal consumers, database contracts, serialized formats, CLI behavior, configuration, environment variables, URLs/routes, event schemas, background jobs, existing clients.

If compatibility is intentionally broken, verify the repository provides an appropriate migration path.

## Concurrency

Look for: race conditions, check-then-act sequences, duplicate job execution, lost updates, unsafe shared mutable state, incorrect locking, retry amplification, queue ordering assumptions, non-idempotent operations.

Do not assume code is safe simply because it is asynchronous.

## Error handling

Check whether failures can cause: silent corruption, incorrect success responses, partial completion, lost errors, unbounded retries, resource leaks, incorrect rollback, invalid state transitions.

## Tests

Ask: does the existing suite cover the changed behavior? Is a regression test needed? Are negative paths covered? Do tests verify behavior rather than implementation details? Could the implementation pass existing tests while still being wrong?

Do not demand tests for trivial changes when meaningful coverage already exists.

## Performance

Report performance issues only with a plausible material problem: unbounded work, N+1 queries, large repeated allocations, blocking work on latency-sensitive paths, missing pagination, excessive network calls, accidental quadratic behavior, expensive work inside frequently executed loops.

Do not report micro-optimizations without evidence of meaningful impact.

## Scope

Prefer findings directly caused by the change. Mention pre-existing code only when the change activates a previously unreachable defect, relies on an unsafe existing assumption, cannot be explained accurately without nearby context, or materially increases the impact of an existing defect. Do not turn a focused review into a general repository audit.

## Finding format

Every actionable finding should communicate:

- **Severity** — Critical / High / Medium / Low
- **Location** — the smallest useful file and code location
- **Problem** — what is actually wrong
- **Impact** — what can happen because of it
- **Recommendation** — the smallest reasonable correction

### Severity guidance

- **Critical** — authentication bypass, broad privilege escalation, remote code execution, major credential exposure, catastrophic data corruption.
- **High** — unauthorized access to sensitive resources, important data-integrity failure, serious API contract break, duplicate execution of high-value operations.
- **Medium** — meaningful defect with limited scope, realistic prerequisites, or moderate impact.
- **Low** — narrow correctness issue, defense-in-depth weakness, or low-impact regression.

## Avoid false positives

Do not flag: pure formatting, naming preferences, personal style preferences, hypothetical issues with no plausible execution path, changes explicitly handled elsewhere, tests intentionally narrow when broader coverage is unnecessary, refactors that preserve behavior without evidence of a defect.

If uncertain, investigate more context before reporting.

## Conclude with one of

- **Approve** — no material issues found.
- **Request Changes** — one or more actionable defects should be fixed.
- **Needs Investigation** — behavior cannot be safely evaluated without additional evidence.

Do not block a change solely because of stylistic disagreement.

## Principle

Try to break the implementation before users do, but only report problems you can substantiate.
