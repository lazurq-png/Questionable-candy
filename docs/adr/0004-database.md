---
status: "proposed"
date: "2026-09-10"
decision-makers: "Martin Larsson"
---

# 0004. Choosing the database engine and media storage for the candy ordering schema

## Context and Problem Statement

The schema defines Candy, User, Cart, and Order entities with relational links between them (a user's cart and orders reference candy items), plus a Picture field on Candy that must be served efficiently to mobile clients. The database must support these relations, array-like fields such as Allergies, and choice-based fields like Order Status used to drive order tracking. Which database engine and media storage approach should back these models in production versus local development?

## Decision Drivers

- Works well with the rest of the techstack
- Covers all the usecases/models

## Considered Options

- PostgreSQL
- MySQL / MariaDB
- SQLite
- MongoDB (document-oriented NoSQL database)

## Decision Outcome

Chosen option: "PostgreSQL", in production and in local development, because the data model uses `ArrayField` for the allergy fields and PostgreSQL covers the Candy/Cart/Order relations at production scale.

Unlike the other ADRs in this set, this one is not started on the Django default and swapped later: SQLite and PostgreSQL differ in available field types and concurrency behaviour, so running one in development and the other in production means development does not test what production runs.

### Confirmation

Nothing enforces it currently, but there could be a use for adding CI jobs to enforce framework at a later stage. (Tests run against PostgreSQL rather than a local SQLite fallback for example.)

## Pros and Cons of the Options

### PostgreSQL

- Good, because it has first-class support for array and JSON fields, a natural fit for the Allergies field and structured order-item content
- Good, because it handles the relational structure between Candy, Cart, and Order reliably at production scale, with strong support in Django's ORM
- Neutral, because it requires running a separate database server, unlike SQLite, but this is standard practice for production Django deployments
- Bad, because it has a steeper operational setup (connection pooling, backups, tuning) compared to a file-based database

### MySQL / MariaDB

- Good, because it is widely supported by hosting providers and has mature tooling for backups, replication, and monitoring
- Good, because it performs well for straightforward relational workloads like the Candy/Cart/Order structure
- Bad, because its support for array-like and JSON fields is less mature and less idiomatic in Django compared to PostgreSQL
- Bad, because certain SQL features (e.g. full JSON path querying) are less capable than PostgreSQL's equivalents

### SQLite

- Good, because it requires zero configuration, making it ideal for local development and quick prototyping
- Good, because it is bundled with Python, so there is no separate database server to install
- Bad, because it does not handle concurrent writes well, making it unsuitable for a production site with multiple simultaneous orders
- Bad, because it lacks some field types and constraints available in PostgreSQL/MySQL, which can cause behavior differences between development and production

### MongoDB (document-oriented NoSQL database)

- Good, because its flexible document model easily accommodates variable fields like Allergies or Info without rigid schema migrations
- Good, because it can scale horizontally for high write volumes if order volume grows significantly
- Bad, because it does not enforce relational integrity between Candy, Cart, and Order the way a relational database does, requiring more application-level validation
- Bad, because Django's ORM is built around relational databases; MongoDB now has an official, MongoDB-maintained Django backend (`django-mongodb-backend`), but as of 2026 it is still in public preview and its own documentation advises against using it in production, leaving third-party options (Djongo, MongoEngine) with less community support as the only production-ready alternatives

## More Information

[`docs/data-model.md`](../data-model.md) depends on this decision: `Profile.allergies` and `Candy.allergens` use `ArrayField`, which is PostgreSQL-only.

Media storage for the Candy Picture is named in the title and context but no options are given for it — still open.
