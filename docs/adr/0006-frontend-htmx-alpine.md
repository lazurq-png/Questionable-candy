---
status: "accepted"
date: "2026-09-14"
decision-makers: "Martin Larsson"
---

# 0006. Adopting htmx and Alpine.js for the server-rendered candy screens

## Context and Problem Statement

[ADR 0001](0001-frontend.md) chose Django Templates plus hand-written CSS and recorded htmx and Alpine.js as "deferred, not rejected" — to be added "later if the baseline turns out to be insufficient". That later arrived without being written down: `templates/base.html` has loaded `htmx.org@2.0.3` and `alpinejs@3.14.1` from unpkg since the cart work in `2935aac`, and `shop/templates/shop/candy_list.html` drives the add-to-cart button with `hx-post`/`hx-swap` rather than a form submit. No hand-written CSS was ever added. The repository therefore ran on a stack that its own ADR said it was not using. Should the deferral be reversed on the record, or should the code be reverted to the ADR?

## Decision Drivers

- The decision record must describe what actually runs; a decision contradicted by `base.html` is worse than no decision
- ADR 0001's driver — "Test what Django provides out of the box before adding dependencies" — has now been tested rather than assumed
- Partial page updates for the cart without a build step or an SPA
- [ADR 0003](0003-backend.md) keeps the backend server-rendered with no API layer, so any interactivity layer must work against HTML responses, not JSON

## Considered Options

- Adopt htmx + Alpine.js via CDN and supersede ADR 0001 (record what runs)
- Revert `base.html` and rewrite the cart as plain form POSTs, keeping ADR 0001 intact
- Adopt htmx + Alpine.js but vendor them as static files instead of CDN script tags
- Add Tailwind CSS alongside them, taking the whole deferred stack from ADR 0001 at once

## Decision Outcome

Chosen option: "Adopt htmx + Alpine.js via CDN and supersede ADR 0001", because the cart already demonstrates the insufficiency ADR 0001 named as its own trigger: swapping a single button after a POST is the exact case that a full-page form submit handles badly, and it was reached on the first interactive feature rather than hypothetically.

This ADR supersedes ADR 0001 on the interactivity layer only. ADR 0001's choice of **Django Templates** stands unchanged, and its hand-written-CSS decision stands as still-unexercised — no CSS of any kind exists yet, so nothing about styling is settled here.

Tailwind remains deferred, and for the same reason ADR 0001 gave: it has not yet been shown to be needed.

### Confirmation

`tests/integration/test_views.py::test_catalog_page_supplies_csrf_token_to_htmx` fails if `base.html` stops serving htmx a CSRF token, which is the thing most likely to break silently — Django's test client does not enforce CSRF, so the suite passed for two commits while every real-browser `hx-post` returned 403.

Since 2026-09-15 a stronger confirmation exists: `tests/e2e/test_catalog.py::test_add_to_cart_swaps_the_button_in_the_browser` performs the click in a real browser, so the token is exercised by htmx rather than asserted to be present in the HTML. The integration test stays: it is fast, and it names the cause directly where the browser test only shows the effect.

Nothing pins the htmx or Alpine versions beyond the literal URLs in `base.html`; a CDN outage or a deleted version breaks the page at runtime with no build-time signal. That is the accepted cost of the no-build-step option and the trigger for revisiting the vendoring alternative below.

## Pros and Cons of the Options

### Adopt htmx + Alpine.js via CDN and supersede ADR 0001

- Good, because it makes the record match `base.html`, so the next reader is not misled about which stack is live
- Good, because htmx returns HTML fragments, which fits ADR 0003's server-rendered monolith without introducing serializers or a JSON API
- Good, because two script tags need no npm, no bundler and no build step, keeping the "no build step" property ADR 0001 valued
- Neutral, because it spends the deferral ADR 0001 was holding in reserve, leaving Tailwind as the only remaining deferred item
- Bad, because CDN script tags are an unpinned runtime dependency on unpkg with no integrity hash and no offline story

### Revert base.html and rewrite the cart as plain form POSTs

- Good, because it keeps ADR 0001 intact and removes the third-party runtime dependency entirely
- Good, because `{% csrf_token %}` inside a form makes the CSRF problem disappear rather than needing `hx-headers`
- Bad, because a form POST reloads the whole catalog to update one button, which is the behaviour the cart work was written to avoid
- Bad, because it discards working code to satisfy a record that could instead be corrected

### Adopt htmx + Alpine.js but vendor them as static files

- Good, because it pins exact versions in the repository and removes the runtime dependency on unpkg
- Good, because the page keeps working offline and in a locked-down network
- Bad, because it puts minified third-party bundles in version control and needs a manual update procedure that nothing currently enforces
- Neutral, because it can be adopted later without changing any template except the two script tags

### Add Tailwind CSS alongside them

- Good, because it would settle the styling question at the same time as the interactivity question
- Bad, because Tailwind's build step is exactly the thing ADR 0001 avoided, and no styling need has been demonstrated yet
- Bad, because it bundles an unforced decision into a forced one

## More Information

Supersedes [0001](0001-frontend.md). The Django Templates half of 0001 is unchanged.

This ADR is written after the fact: the code landed in `2935aac` and this record follows in `7f690d3`'s wake. That ordering is the defect this document closes, not a pattern to repeat — see `CLAUDE.md` §4 on deciding before implementing.

Revisit when: a CDN outage or version removal breaks the page (adopt the vendoring option), or when styling work begins and the hand-written-CSS half of ADR 0001 finally gets exercised.

[ADR 0005](0005-testing.md) made Playwright conditional on "the ADR 0001 templates giving it a page to open". Those templates exist and this ADR confirms the interactivity layer they use, so that condition is now met and `tests/e2e/` is unblocked.
