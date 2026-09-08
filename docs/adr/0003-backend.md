---
status: "proposed"
date: "2026-09-08"
decision-makers: "Martin Larsson"
---

# 0003. Choosing the backend architecture for order processing and catalog logic

## Context and Problem Statement

The backend must implement the core business logic behind the Candy catalog, Cart operations, and the Order lifecycle (creation, status transitions, and the Track order feature), as well as expose an admin interface for managing Candy records (Price, Supplier, Allergies, Picture). Some of this work — order confirmation, notifying the Supplier, status updates — is naturally asynchronous. Which backend framework and architecture should be used to implement this logic?

## Decision Drivers

- Work with ORM
- Mobile and desktop compatability

## Considered Options

- Django monolith with server-rendered views (MVT pattern, no separate API layer)
- Django + Django REST Framework as an API-first backend
- FastAPI as a lightweight, async-first API backend
- Flask as a minimal, unopinionated backend framework

## Decision Outcome

Chosen option: "Django + Django REST Framework as an API-first backend", because it ships with built-in ORM and would work well for a mobile app.

### Consequences

- Good, because it exposes Candy, Cart, and Order data through a versioned REST API that can serve a web frontend, a future mobile app, or partner integrations equally
- Good, because DRF provides serialization, validation, and browsable API documentation out of the box
- Bad, because it requires building a separate frontend (SPA or otherwise) to consume the API, duplicating some logic (e.g. cart totals) on both client and server
- Bad, because it adds development overhead not justified if only a single server-rendered website is planned

### Confirmation

Nothing enforces it currently, but there could be a use for adding CI jobs to enforce framework at a later stage.

## Pros and Cons of the Options

### Django monolith with server-rendered views (MVT pattern, no separate API layer)

- Good, because it gives a free, full-featured admin interface for managing the Candy catalog with no extra setup
- Good, because it keeps the codebase simple: one framework, one deployment unit, fewer moving parts to maintain
- Neutral, because it couples the frontend rendering to the backend, which is fine while the frontend stays server-rendered but limits reuse if a native mobile app is added later
- Bad, because it is harder to expose the same order and catalog data to a future mobile app or third-party integration without retrofitting an API layer

### Django + Django REST Framework as an API-first backend

- Good, because it exposes Candy, Cart, and Order data through a versioned REST API that can serve a web frontend, a future mobile app, or partner integrations equally
- Good, because DRF provides serialization, validation, and browsable API documentation out of the box
- Bad, because it requires building a separate frontend (SPA or otherwise) to consume the API, duplicating some logic (e.g. cart totals) on both client and server
- Bad, because it adds development overhead not justified if only a single server-rendered website is planned

### FastAPI as a lightweight, async-first API backend

- Good, because its native async support suits high-concurrency scenarios like real-time order-status polling or websocket-based tracking
- Good, because it generates OpenAPI documentation automatically and has strong type-checking via Pydantic
- Bad, because it lacks Django's built-in admin, ORM conveniences, and authentication scaffolding, meaning more custom code for the Candy management interface
- Bad, because it is a second framework to introduce alongside Django if any part of the stack still needs Django's features, increasing operational complexity

### Flask as a minimal, unopinionated backend framework

- Good, because its minimalism allows a tailored architecture with only the components this project needs
- Good, because it has a shallow learning curve for small teams
- Bad, because it requires manually assembling an ORM, admin interface, authentication, and form handling that Django provides out of the box, increasing development time
- Bad, because the lack of enforced structure can lead to inconsistent patterns as the codebase grows (catalog, cart, and order logic each built ad hoc)

## More Information

{Supporting links: docs, the blog post or commit where the decision played out,
related ADRs. Note here when the decision should be revisited.}
