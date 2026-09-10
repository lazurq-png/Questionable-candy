# Unit tests

Model methods, form validation and pure business logic — the pieces that can be
checked in isolation, touching the database only where a model makes that
unavoidable.

Covered by `pytest-django`, using its fixtures rather than `setUp`/`tearDown`.
See [ADR 0005](../../docs/adr/0005-testing.md).
