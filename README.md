# Questionable Candy

Design documentation for a candy ordering website — a professional storefront with
a dash of satire, where every product is required to disclose a significant flaw and
checkout triple-confirms that you really do want to buy candy.

This repository currently holds the specification and architecture decisions only.
No application code has been written yet.

## Planned stack

| Layer    | Choice                                 |
| -------- | -------------------------------------- |
| Frontend | Django Templates + hand-written CSS    |
| Backend  | Django monolith with server-rendered   |
| Auth     | Django built-in session authentication |
| Database | PostgreSQL                             |

## Documentation

- [Requirements specification](docs/requirements.md) — use cases in Cockburn fully-dressed format
- [Data model](docs/data-model.md) — entity-relationship model and entity definitions

### Architecture decision records

- [ADR 0001 — Frontend stack](docs/adr/0001-frontend.md)
- [ADR 0002 — Middleware: authentication, session and cart handling](docs/adr/0002-middleware.md)
- [ADR 0003 — Backend architecture](docs/adr/0003-backend.md)
- [ADR 0004 — Database engine and media storage](docs/adr/0004-database.md)

New decisions start from [the ADR template](docs/adr/0000-adr-template.md).

## Status

Draft — requirements and data model are at version 0.1, and all four ADRs are
`proposed` rather than `accepted`.
