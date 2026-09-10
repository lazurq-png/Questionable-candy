# Integration tests

Views, URL routing, template rendering and flows that cross several models —
anything exercised through the Django test client with a real test database
behind it.

Covered by `pytest-django` and its `client`/`db` fixtures.
See [ADR 0005](../../docs/adr/0005-testing.md).
