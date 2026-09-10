---
status: "proposed"
date: "2026-09-10"
decision-makers: "Martin Larsson"
---

# 0001. Choosing a mobile-first frontend stack for the candy ordering website

## Context and Problem Statement

A candy ordering website (Customer flow: View the candy → Read about it → Choose candy → Order candy → Track order) needs a rendering approach for the Website component that displays the Candy catalog, Cart, and Order tracking screens. The stack must be built mobile-first, since customers are expected to browse and order from both phones and desktop. Which frontend technology (templating, styling, and interactivity layer) should be used to render and drive these views?

## Decision Drivers

- Test what Django provides out of the box before adding dependencies
- Learning new approaches and technologies.
- Create a professional website, with a dash of satire.

## Considered Options

- Django Templates + hand-written CSS (Django out of the box)
- Django Templates + Tailwind CSS + HTMX + Alpine.js
- React Single-Page Application (SPA) + Django REST Framework API
- Vue.js Single-Page Application (SPA) + Django REST Framework API
- Django Templates + Bootstrap (server-rendered, no JS framework)

## Decision Outcome

Chosen option: "Django Templates + hand-written CSS (Django out of the box)", to see how far Django's own templating and static files get the catalog, cart and order screens. Tailwind, HTMX and Alpine.js get added later if the baseline turns out to be insufficient.

### Confirmation

Nothing enforces it currently, but there could be a use for adding CI jobs to enforce framework at a later stage. (Builds fail when react/vue is found in package.json for example.)

## Pros and Cons of the Options

### Django Templates + hand-written CSS (Django out of the box)

- Good, because it renders the catalog, cart and order screens with no dependency beyond Django itself and no build step
- Good, because HTMX and Alpine.js are script tags that can be added to working templates later, so nothing here has to be undone to adopt them
- Bad, because hand-written CSS has to handle mobile-first breakpoints deliberately, which Tailwind's unprefixed utilities would do by default
- Bad, because none of the unfamiliar technology gets exercised in the first iteration

### Django Templates + Tailwind CSS + HTMX + Alpine.js

- Good, because Tailwind's unprefixed utility classes are mobile-first by default, encouraging small-screen-first layout decisions
- Good, because HTMX enables partial page updates (cart changes, filtering) without a full JavaScript framework or separate API layer
- Neutral, because it keeps the project server-rendered, which simplifies SEO and initial load but limits offline/app-like behavior without extra work (e.g. a PWA layer)
- Bad, because the team must learn HTMX's request/response model if unfamiliar with this

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

Tailwind CSS, HTMX and Alpine.js are deferred, not rejected — revisit once the baseline is running and its limits are known.

Related: [0003](0003-backend.md), which assumes the same server-rendered architecture.
