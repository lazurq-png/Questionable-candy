---
status: "proposed"
date: "2026-09-10"
decision-makers: "Martin Larsson"
---

# 0005. Choosing test frameworks for the different test stages

## Context and Problem Statement

The project currently consists of `manage.py` and the `mysite/` settings package with no apps, no views and no tests, while `.gitignore` already reserves a `# Tests` block for `.pytest_cache/`, `.coverage`, `coverage.xml` and `htmlcov/` — a coverage-producing runner is anticipated but nothing has been chosen. Because the suite is empty, whichever runner is picked now is the one every future test is written against, and switching later means rewriting the tests rather than adding a package. Which frameworks should cover the unit, integration and browser stages, and which test data and coverage tooling should go with them?

## Decision Drivers

- Has to be actually used in real django projects professionally
- Should not require more than 3-5 different packages, if possible
- Choosing now costs nothing because there are zero tests, whereas choosing later means rewriting whatever suite exists by then

## Considered Options

- Django's built-in `unittest` stack (`django.test.TestCase`, JSON fixtures, `LiveServerTestCase` with Selenium)
- pytest-django stack (`pytest-django`, `pytest-cov`, `factory_boy`, Playwright)
- pytest-django core only, without factories or a browser layer
- Full enterprise stack (the pytest stack plus `tox`/`nox`, DRF `APIClient`/`schemathesis`, hosted coverage reporting)

## Decision Outcome

Chosen option: "pytest-django stack", because it is the default in professional Django work today and it lands exactly inside the package budget at five entries — `pytest`, `pytest-django`, `pytest-cov`, `factory_boy` and `pytest-playwright` — with Faker arriving transitively through factory_boy rather than as a sixth choice.

The stack is adopted as one decision but not installed all at once: `pytest-django`, `pytest-cov` and `factory_boy` apply from the first app that has a model, while Playwright is decided here and stays dormant until the ADR 0001 templates give it a page to open. Mocking adds no package to the count — `unittest.mock` is in the standard library, and the HTTP-specific alternatives (`responses`, `requests-mock`) are not counted because nothing in the project makes an outbound call yet.

### Confirmation

Nothing enforces it currently, but there could be a use for adding CI jobs to enforce framework at a later stage. (Tests run against PostgreSQL rather than a local SQLite fallback for example.)

## Pros and Cons of the Options

### Django's built-in `unittest` stack (`django.test.TestCase`, JSON fixtures, `LiveServerTestCase` with Selenium)

- Good, because it ships with Django and requires no extra dependency at all, satisfying the package budget trivially
- Good, because `self.client`, `assertTemplateUsed` and transactional test-database wrapping are integrated out of the box, and `LiveServerTestCase` hands Selenium a running server with no glue code
- Bad, because the assertion API is verbose and the class-based `setUp`/`tearDown` boilerplate scales badly once several tests need the same Candy and Profile objects
- Bad, because Selenium needs manual `WebDriverWait` calls, which makes browser tests slower and more flaky than the auto-waiting alternatives

### pytest-django stack (`pytest-django`, `pytest-cov`, `factory_boy`, Playwright)

- Good, because fixture-based dependency injection and plain `assert` statements remove the `setUp` boilerplate and the `assertEqual` zoo, and the plugin ecosystem (`pytest-xdist` for parallel runs, `pytest-mock`) is there when the suite grows
- Good, because factory_boy composes test objects programmatically, so a schema change breaks one factory instead of every JSON fixture that mentioned the field
- Neutral, because five packages sits at the very top of the 3-5 budget, leaving no room for a sixth without revisiting this decision
- Bad, because it needs configuration that the built-in runner does not (`pytest.ini` or `pyproject.toml` plus `DJANGO_SETTINGS_MODULE`) and is a steeper start for anyone who only knows unittest

### pytest-django core only, without factories or a browser layer

- Good, because two packages is the lightest possible move off unittest while still getting fixtures and plain `assert`
- Good, because it defers every tool that is not needed until an app actually exists
- Bad, because it falls back on JSON fixtures for the `ArrayField` data in ADR 0004, which is exactly the brittle case factories exist to solve
- Bad, because it leaves the server-rendered flows from ADR 0001 with no browser coverage, forcing a second framework decision later on rather than one now

### Full enterprise stack (the pytest stack plus `tox`/`nox`, DRF `APIClient`/`schemathesis`, hosted coverage reporting)

- Good, because tox/nox pin reproducible environments across Python and Django versions, and schemathesis property-tests an API against its OpenAPI schema
- Good, because hosted coverage reporting puts a threshold and a PR comment in front of every change once CI exists
- Bad, because the DRF test tooling is dead weight while ADR 0003 defers DRF and there is no API layer to point it at
- Bad, because tox/nox is overkill for an application targeting a single Python and Django version, and the additions push the count well past the 3-5 package budget

## More Information

Playwright is decided but dormant — revisit when the templates from ADR 0001 exist and there are interactive flows to drive. Related: [0001](0001-frontend.md)

DRF-specific test tooling (`APIClient`, `pytest-drf`, `schemathesis`) is deferred, not rejected — revisit if ADR 0003 is reopened and an API layer is added. Related: [0003](0003-backend.md)

The `ArrayField` usage on `Profile.allergies` and `Candy.allergens` is what pushes test data toward factory_boy rather than JSON fixtures. Related: [0004](0004-database.md)

`mysite/settings.py` still configures SQLite while ADR 0004 chose PostgreSQL for development and production, so the Confirmation clause above cannot hold until that is changed — noted here as an open item, not addressed by this ADR.
