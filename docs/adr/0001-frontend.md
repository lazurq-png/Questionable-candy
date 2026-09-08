---
status: "proposed"
date: "2026-09-08"
decision-makers: "Martin Larsson"
---

# 0001. Choosing a mobile-first frontend stack for the candy ordering website

## Context and Problem Statement

A candy ordering website (Customer flow: View the candy → Read about it → Choose candy → Order candy → Track order) needs a rendering approach for the Website component that displays the Candy catalog, Cart, and Order tracking screens. The stack must be built mobile-first, since customers are expected to browse and order from both phones and desktop. Which frontend technology (templating, styling, and interactivity layer) should be used to render and drive these views?

## Decision Drivers

- Learning new approaches and technologies.
- Create a professional website, with a dash of satire.

## Considered Options

- Django Templates + Tailwind CSS + HTMX + Alpine.js
- React Single-Page Application (SPA) + Django REST Framework API
- Vue.js Single-Page Application (SPA) + Django REST Framework API
- Django Templates + Bootstrap (server-rendered, no JS framework)

## Decision Outcome

Chosen option: "Django Templates + Tailwind CSS + HTMX + Alpine.js".
Because HTMX and Alpine.js are frameworks I have yet to work with, instead of for example React or Vue which I have done some smaller projects in already.
Could swap to "Django Templates + Bootstrap", if there is too much to learn with HTMX + Alpine.js.

### Consequences

- Good, because Tailwind's unprefixed utility classes are mobile-first by default, encouraging small-screen-first layout decisions
- Good, because HTMX enables partial page updates (cart changes, filtering) without a full JavaScript framework or separate API layer
- Neutral, because it keeps the project server-rendered, which simplifies SEO and initial load but limits offline/app-like behavior without extra work (e.g. a PWA layer)
- Bad, because the team must learn HTMX's request/response model if unfamiliar with this

### Confirmation

Nothing enforces it currently, but there could be a use for adding CI jobs to enforce framework at a later stage. (Builds fail when react/vue/djangorestframework is found in package.json for example)

## Pros and Cons of the Options

### Django Templates + Tailwind CSS + HTMX + Alpine.js

- Good, because Tailwind's unprefixed utility classes are mobile-first by default, encouraging small-screen-first layout decisions
- Good, because HTMX enables partial page updates (cart changes, filtering) without a full JavaScript framework or separate API layer
- Neutral, because it keeps the project server-rendered, which simplifies SEO and initial load but limits offline/app-like behavior without extra work (e.g. a PWA layer)
- Bad, because the team must learn Tailwind's utility-class conventions and HTMX's request/response model if unfamiliar with either

### React Single-Page Application (SPA) + Django REST Framework API

- Good, because it supports a rich, app-like mobile experience (smooth transitions, live order-tracking updates, offline caching)
- Good, because it decouples frontend and backend, useful if a mobile app is planned later that reuses the same API
- Bad, because it requires building and maintaining a full REST API in addition to the Django backend, adding significant complexity for a catalog-and-checkout site of this size
- Bad, because SEO and first-paint performance need extra work (server-side rendering or static generation) to match a server-rendered approach

### Vue.js Single-Page Application (SPA) + Django REST Framework API

- Good, because Vue has a gentler learning curve than React for teams new to SPA frameworks
- Good, because it shares the same architectural benefits as the React option (API reuse, rich interactivity)
- Bad, because it still requires a full DRF API layer, duplicating logic that could otherwise live directly in Django views
- Bad, because component-based state management (cart state, order status) adds overhead not needed for a mostly linear browse-to-checkout flow

### Django Templates + Bootstrap (server-rendered, no JS framework)

- Good, because it is the simplest option to build and maintain, with no build tooling or JS framework to manage
- Good, because Bootstrap's responsive grid handles mobile layouts adequately out of the box
- Bad, because Bootstrap's component styling is generic and harder to make visually distinctive compared to a utility-first approach
- Bad, because without HTMX or similar, cart and catalog interactions require full page reloads, which feels slower on mobile connections

## More Information

{Supporting links: docs, the blog post or commit where the decision played out,
related ADRs. Note here when the decision should be revisited.}
