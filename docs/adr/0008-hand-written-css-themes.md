---
status: "accepted"
date: "2026-09-23"
decision-makers: "Martin Larsson"
---

# 0008. Hand-written CSS with light and dark themes

## Context and Problem Statement

[ADR 0001](0001-frontend.md) chose hand-written CSS and deferred Tailwind, but
left that half unexercised: until 2026-09-16 the project had no CSS at all, so
nothing about styling was settled — [ADR 0006](0006-frontend-htmx-alpine.md)
says as much. The run of 2026-09-16 then styled every page and added a
light/dark theme with a toggle, which set real conventions in code:
`shop/static/shop/site.css`, `shop/static/shop/theme.js`, an inline script in
`templates/base.html`, and a custom-property palette written twice so that both
`prefers-color-scheme` and `data-theme` select it.

Those conventions exist and are partly exercised by tests (see Confirmation
below), but no ADR records them.
ADR 0006 names that ordering — a decision made in code and documented
afterwards — as "the defect this document closes, not a pattern to repeat", so
this ADR closes it for styling. What should the styling layer be, and what is
the theme mechanism?

## Decision Drivers

- ADR 0001's own terms: no CSS framework until one is shown to be needed, and
  no build step (there is still no Node, bundler or preprocessor in the repo).
- `docs/requirements.md` §3: mobile-first, usable on a phone and on a desktop.
- The site must work without JavaScript: the theme has to follow the visitor's
  system setting with CSS alone.
- What can be verified has to be verifiable by a test, since an unattended run
  cannot look at a page (`.claude/rules/frontend.md`).
- One place to change a colour.

## Considered Options

- Keep hand-written CSS, one stylesheet, custom properties for both themes
- Adopt Tailwind (or another utility framework), accepting a build step
- Adopt a small classless CSS framework from a CDN (Pico CSS itself, say)

## Decision Outcome

Chosen option: "Keep hand-written CSS, one stylesheet, custom properties for
both themes", because it is the only option that adds neither a dependency nor
a build step, which ADR 0001 and ADR 0006 both make a condition, and because
the site is small enough that one 1300-line stylesheet is navigable.

The conventions being recorded, as built (night-2026-09-16 `decisions.md` D6
and D7, night-2026-09-17 D16):

- **One stylesheet**, `shop/static/shop/site.css`, loaded from `base.html` with
  `{% static %}`. `django.contrib.staticfiles` and app-directory static are
  enough; no settings change was needed. `templates/500.html` repeats that
  `<link>` and the inline theme script below by design: it cannot extend
  `base.html`, because Django renders it with no request and no context
  processors, and a page shown when the site is broken must not need either.
- **Colours are custom properties on `:root`.** The dark values appear twice:
  under `@media (prefers-color-scheme: dark)` for the system setting, and under
  `[data-theme="dark"]` for the toggle. CSS cannot share one declaration block
  between a media query and an attribute selector without a preprocessor, and a
  preprocessor is a build step.
- **Mobile-first:** the base rules are the phone layout; `min-width` queries
  widen it.
- **The theme toggle** is `theme.js` plus a short inline script in `<head>`
  that applies a stored choice before first paint (otherwise a dark choice
  flashes light; `templates/500.html` carries its own copy of that script for
  the same reason it carries its own `<link>`). Vanilla JavaScript, not Alpine:
  the toggle needs no reactivity, and it keeps working if the Alpine CDN is
  slow. With no stored choice the CSS alone follows the system; pressing the
  toggle back to the system's own theme clears the stored choice (D16).
- **Without JavaScript** the toggle ships `hidden` and is never revealed, so no
  visitor sees a control that cannot work.
- **The visual reference was Pico CSS's restrained card-and-system-font look,
  re-implemented by hand.** No Pico code, variable names or values were copied
  (D6); the palette is this site's own.

### Confirmation

Partly enforced, partly not — plainly:

- **Enforced by tests.** `tests/e2e/test_theme.py` drives a real browser at
  375px, in both themes, from the system setting and from a stored choice, over
  every customer page, and asserts: no horizontal overflow, the header on one
  row, every control at least 44×44, and body text at 4.5:1 against the colour
  actually painted behind it. `tests/e2e/test_error_pages.py`,
  `test_accounts.py`, `test_checkout_warning.py` and `test_checkout_confirm.py`
  apply the same checks to the pages added since.
- **Not enforced.** Nothing stops a second stylesheet, an external font, or a
  CDN stylesheet being added: `scripts/adr_guards.py` reads `requirements.txt`,
  and CSS arrives in templates rather than in a Python manifest. A reviewer
  reading a diff is the only check. If that proves too weak, the guard script
  could grep `templates/` for `<link rel="stylesheet">` hosts and
  `shop/static/` for a second `.css` file.
- **Never verified by any test:** whether the pages look good. Hierarchy,
  rhythm, balance, whether the flaw disclosure reads as a warning — each
  morning report since says so, and this ADR does not change it.

## Pros and Cons of the Options

### Keep hand-written CSS, one stylesheet, custom properties

- Good, because it needs no dependency, no build step and no Node, which is
  what ADR 0001 and ADR 0006 require.
- Good, because the theme works with CSS alone; JavaScript only stores an
  override.
- Good, because one file means one place to change a colour, and custom
  properties keep the two theme blocks to values rather than rules.
- Neutral, because the dark palette is written twice. It is values only, and a
  test reads both copies.
- Bad, because nothing but review stops the conventions being broken.
- Bad, because hand-written CSS scales by discipline; at several times this
  size, a framework's constraints would do work review has to do here.

### Adopt Tailwind or another utility framework

- Good, because it makes consistency the default and is well documented.
- Bad, because it needs a build step and Node, neither of which exists here,
  and ADR 0001 deferred it precisely until shown to be needed. It has not been.
- Bad, because nothing mechanical would stop it: `scripts/adr_guards.py` reads
  `requirements.txt`, and a CSS framework arrives through npm or a CDN tag. The
  deferral in ADR 0001 and ADR 0006 rests on review, not on a check.

### Adopt a classless CSS framework from a CDN

- Good, because it would have given a decent look with almost no work, and Pico
  in particular needs no build.
- Neutral, because the look would be close to what was built by hand anyway.
- Bad, because it puts the site's appearance behind a third-party CDN at
  runtime. The htmx and Alpine tags already take that risk for behaviour, and
  they were pinned by version in the URL alone when this was written, with no
  integrity hash ([ADR 0006](0006-frontend-htmx-alpine.md)); a stylesheet would
  extend the same exposure to how the site looks.
- Bad, because overriding a framework's own custom properties is a second way
  of doing the same thing, and the two drift.

## More Information

- The conventions as they were built: `docs/ai/night-2026-09-16/decisions.md`
  D6, D7, and that run's morning report (T5).
- The theme's two states: `docs/ai/night-2026-09-17/decisions.md` D16, which
  answers `docs/ai/night-2026-09-16/questions.md` Q3.
- Related: [ADR 0001](0001-frontend.md) (which this exercises rather than
  supersedes), [ADR 0006](0006-frontend-htmx-alpine.md).
- **Revisit** when: a second stylesheet or an external font is wanted; a
  designer joins; the site outgrows one file; or someone looks at the pages and
  finds the hand-built look wanting.
- **Proposed 2026-09-17 by the unattended run night-2026-09-17**, which may not
  accept an ADR itself, and **accepted as written on 2026-09-23**, after
  checking it against the code.
