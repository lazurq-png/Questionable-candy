# Architecture Rules

Open this when implementing non-trivial behavior, changing boundaries, or refactoring architecture.

---

## 1. Map the System First

Before modifying architecture, identify:

- entry points
- data flow
- control flow
- domain boundaries
- service boundaries
- persistence boundaries
- external integrations
- relevant tests

Do not make architectural decisions from one isolated file.

---

## 2. Find Canonical Implementations

Search for existing examples of the behavior you need.

Prefer extending the repository's established pattern over introducing a competing one.

If multiple patterns exist, determine:

- which is newer
- which is actively used
- which is documented
- which is covered by tests
- which best matches the requested feature

---

## 3. Responsibilities

Keep responsibilities clear.

Examples:

- transport handles transport concerns
- validation validates external input
- services coordinate application behavior
- domain logic represents business rules
- persistence handles storage
- UI components render and coordinate interaction

Do not move logic between layers merely to make one file shorter.

---

## 4. Abstraction

Do not introduce abstraction before there is a demonstrated need.

Avoid:

- generic frameworks for one use case
- wrappers around trivial APIs
- speculative plugin systems
- unnecessary factories
- unnecessary interfaces
- configuration for hypothetical future requirements

Prefer concrete code until a reusable abstraction is justified.

---

## 5. Refactoring

A refactor should have a clear reason.

Good reasons:

- existing structure prevents required behavior
- duplication creates correctness risk
- architecture violates an established boundary
- testing is materially impaired
- security requires restructuring

Bad reason:

> "While I was here, this looked cleaner."

Keep unrelated refactoring out of feature changes.

---

## 6. Compatibility

Before changing an interface, consider existing consumers.

Preserve compatibility unless the task explicitly changes the contract.

For migrations, consider transitional states where:

```text
old application → new data
new application → old data
```

may coexist.

---

## 7. Architecture Documentation

For consequential architectural decisions, document the decision in the repository's architecture/ADR system.

A useful decision record explains:

- context
- decision
- alternatives
- consequences

Do not document trivial implementation choices.

---

## 8. Review

After an architectural change, review:

- dependency direction
- ownership
- coupling
- failure behavior
- testing
- backwards compatibility
- operational consequences

Prefer the simplest architecture that satisfies the actual requirements.
