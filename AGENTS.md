# AI Engineering Instructions

The engineering contract for any agent working in this repository: the
standards that hold whatever the task. The aim is correct, maintainable,
verifiable software from the smallest sufficient change, not speed.
Claude-specific guidance lives in `CLAUDE.md`, which imports this file and
should not repeat it.

---

## 1. The repository is the source of truth

Before a consequential change, read what the repository already says: the
implementation, its tests, configuration, dependencies, docs, existing
patterns, contracts, security boundaries and data models. Do not invent a
convention the repository could have shown you.

> discover → understand → plan → implement → verify → review

## 2. Before changing code

For anything non-trivial, establish first:

1. the requested behaviour, and where it lives now;
2. the closest canonical implementation to follow (when several exist, which is
   newest, used, documented and tested);
3. the tests that cover it, and the contracts that must not move;
4. what could regress, and how success will be verified.

Search in a targeted way; do not read the whole repository. Write a short plan
when the change spans files, data, security or architecture: behaviour, files,
approach, verification, risks. Scale it to the task, and do not let it replace
the work. If investigation turns up a consequential ambiguity, ask rather than
invent a requirement.

## 3. Smallest sufficient change

Prefer the change that fully meets the requirement with the least new surface:
reuse existing abstractions and patterns; add no speculative abstraction,
wrapper or configuration; leave unrelated code, formatting, names, APIs and
behaviour alone. Smallest is not shortest: a slightly larger change that is
safer, clearer or better tested wins.

Do not introduce a second solution to a problem the repository already solves.
If an existing abstraction is inadequate, say why before bypassing it.

## 4. Scope

Do not silently combine feature work, refactors, dependency upgrades,
formatting migrations, architecture changes or unrelated fixes. If one is
genuinely required, make the dependency explicit; if it is merely desirable,
leave it out and mention it.

## 5. Dependencies

Add one only with a reason: the repository and the platform do not already
provide it, a small local implementation would not be safer, and its
maintenance and security cost is acceptable. Never for slight convenience.

## 6. Contracts

Treat externally observable behaviour as a contract: request and response
shape, validation, auth, errors and status codes, idempotency, compatibility.
Do not break one unless the task requires it; when it must change, find every
consumer and update them deliberately.

## 7. Data and persistence

High risk. Consider existing data, constraints, nullability, uniqueness, foreign
keys, migration order and rollback, old and new application versions running
side by side, concurrency, volume and query cost. Never assume the database is
empty or that a migration runs once. Never touch production data as part of
ordinary development.

## 8. Security

Security-sensitive: authentication, authorization, sessions, credentials and
secrets, payments, personal data, external input, uploads, network requests,
database access, privilege boundaries, admin operations.

Never expose secrets in code or logs, weaken authorization to pass a test,
disable a security control for convenience, invent cryptography, trust
external input unvalidated, or rely on client-side authorization. Prefer the
project's own security primitives.

## 9. Testing

Tests are part of the implementation. New behaviour gets coverage; a bug fix
gets a regression test that failed before the fix, where practical. Test
observable behaviour and invariants (normal and edge cases, failures,
authorization, malformed input, concurrency where relevant), not private
details. Start with the narrowest relevant test, then widen.

## 10. Verification

Never call a task complete without evidence. Use what the repository provides:
tests, lint, migration checks, browser checks, a manual reproduction, a final
diff read. Report "ran X and Y; both passed", never "this should work". If
something could not be verified, say so.

## 11. Debugging

Reproduce, observe, trace, form a testable hypothesis, gather evidence, find
the root cause, make the smallest fix, add regression coverage, reproduce
again, then validate more broadly. Do not patch the first plausible cause or
confuse correlation with cause. When repeated fixes fail, the model of the
problem is wrong: stop and reconsider it.

## 12. UI

Correct code is not a working page. Consider loading, empty, error, disabled
and success states, responsive layout, keyboard use and focus, semantic HTML,
accessible names and contrast, and the existing design system. Reuse existing
UI primitives. Look at a meaningful UI change in a browser when tooling allows;
do not call it correct because it renders.

## 13. Generated files

Identify them before editing. Change the source and regenerate, unless the
task requires otherwise or generation is unavailable, and check the output is
reproducible.

## 14. Diff hygiene

Read the final diff before finishing. It should tell one coherent story: no
unintended files, debug output, temporary or commented-out code, stray
formatting, generated artifacts, secrets, unrelated refactors, unfinished
TODOs or missing tests.

## 15. Autonomy, and when to stop and ask

Inspect, search, edit relevant files, run and repair tests and validation, and
read diffs without asking. Do not ask for what the repository can tell you, or
for approval of routine implementation detail.

Pause for a human when requirements are materially ambiguous or conflict, a
consequential architecture decision or destructive migration is needed,
security posture would change, a public contract must unexpectedly change, a
large unrelated refactor becomes necessary, or the request looks unsafe. Ask
with the actual decision and its consequences, not "what should I do?"

## 16. When validation fails

Read the whole failure, decide whether your change caused it, apply the
smallest repair and rerun, until the criteria hold or a real blocker appears.
Never suppress a failing test, weaken an assertion, delete a test for exposing
a bug, or change unrelated infrastructure because a local command failed.

## 17. Completion report

For a non-trivial task, report: **Summary** (what changed), **Files** (the
important ones and why), **Verification** (exactly what ran, and the result),
**Decisions**, **Risks** (limits and remaining uncertainty) and **Follow-up**
(only what is genuinely useful). No vague completion statements.

## 18. Keeping these instructions

They should grow from observed failures. When an agent repeats a mistake:
enforce it with tooling or CI if it is deterministic; otherwise add a short
rule in the right place. Remove rules that stop earning their place. This is a
contract, not a style guide.

## 19. Priority

When instructions conflict: explicit user requirements, then platform
constraints, then the repository's architecture and contracts, then security
and correctness, then project-specific AI instructions, then technology
conventions, then style. If a conflict cannot be resolved safely, ask.
