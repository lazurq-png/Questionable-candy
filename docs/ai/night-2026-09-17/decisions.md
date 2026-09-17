# Decisions — night-2026-09-17

Choices made during the run, with the alternatives and why they lost. Choices
the human settled are in `plan.md` ("Settled by the human") and are not
repeated here.

## D1. T1: a duplicate-code lint message left standing

`pylint` R0801 matches five lines of theme setup in
`tests/e2e/test_error_pages.py` (`_show`) against the parametrized body of
`tests/e2e/test_theme.py`. Removing it means moving that setup out of
`test_theme.py` into a shared helper, which changes an existing test file for a
refactor-class message, outside T1. It is a refactor note, not a warning or an
error, and the lint gate passes. Left for Exploration, where "duplicated code"
is an allowed category.

## D2. T1: 404 and CSRF pages extend base.html, the 500 page does not

Django's `page_not_found` and `csrf_failure` render with the request (context
processors run, `csrf_token` is fresh); `server_error` renders with nothing.
Extending base.html for the first two keeps the header, cart and theme toggle;
the 500 page must not depend on the request or a context processor, as the plan
requires.
