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

## D3. T2: the allergen vocabulary lives in `shop/allergens.py`

Both `Candy.allergens` and `accounts.User.allergies` need it. Options:
- **`shop/allergens.py` (chosen):** a plain constants module. `accounts` imports
  it, but `shop` imports nothing from `accounts`, so there is no cycle, and
  nothing about models or a service layer (ADR 0003) is involved. Allergens
  are food data, which is the shop's domain.
- **`accounts/allergens.py`:** puts food vocabulary in the user app, and makes
  `shop` depend on `accounts` for a candy's own field.
- **A project-level module (`mysite/`):** `mysite` is settings and URLs; no
  domain data lives there today.

The choices are enforced by `clean_fields()`/`full_clean()` and forms, not by a
database constraint. A `<@ ARRAY[...]` check would need a migration for every
vocabulary change, and nothing writes these fields except forms and the seed.

## D4. T2: legacy free-text allergies are not migrated or guarded (reviewer, Low)

The reviewer found that `UserAdminChangeForm` renders only the 14 keys, so a
user whose `allergies` already held a free-text value (e.g. `"nuts"`) would
lose it silently on the next admin save. Not fixed in code:

- A form check that refuses the save deadlocks. The value is also rejected by
  the model's choices, so the admin could never save that user without
  removing it.
- Mapping legacy values to keys is a data decision per value ("nuts" could be
  tree nuts or peanuts).
- Measured exposure: the dev database has **0** users with any allergy (queried
  during T2). Before today the only way to write one was the admin's
  comma-separated text box.

Raised as questions.md Q2. `allergens.names()` skips unknown keys, so a legacy
value cannot break rendering or the later warning; it is simply not matched.
