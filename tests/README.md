# Tests

Layout for the test suite. The framework choice behind it is recorded in
[ADR 0005](../docs/adr/0005-testing.md) — `pytest-django`, `pytest-cov`,
`factory_boy` and Playwright.

```
tests/
├── unit/          models, forms and pure logic
├── integration/   views, templates and DB-backed flows
├── e2e/           browser flows driven by Playwright
└── factories/     factory_boy factories shared by the stages above
```

No tests exist yet, and no runner is installed — the folders mark where each
stage goes once the first app is written. Running the suite will be
`pytest tests` from the repository root, against PostgreSQL rather than a local
SQLite fallback (see [ADR 0004](../docs/adr/0004-database.md)).
