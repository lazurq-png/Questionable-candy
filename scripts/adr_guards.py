#!/usr/bin/env python
"""Enforce the ADR decisions whose records name requirements.txt as the check.

ADR 0003 defers Django REST Framework; ADR 0005 caps the test stack at five
packages. Both name requirements.txt as where compliance is visible, so both
are real checks rather than prose in a document nobody re-reads.

Runs in CI (.github/workflows/ci.yml) and by hand:

    python scripts/adr_guards.py

Reads one text file -- no Django, no database, no installed dependencies -- so
CI can run it as a job of its own that fails in seconds.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST = BASE_DIR / "requirements.txt"

# ADR 0005 budgets 3-5 packages for the test stack. Faker arrives transitively
# through factory_boy and is not counted, so it is absent from the prefixes.
TEST_STACK_BUDGET = 5
TEST_STACK_PREFIXES = ("pytest", "factory_boy", "factory-boy")


def packages(manifest):
    """Requirement lines, with comments and blank lines stripped out."""
    lines = [
        line.split("#")[0].strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
    ]
    return [line for line in lines if line]


def check(manifest=MANIFEST):
    print(f"$ adr-guards {manifest.name}", flush=True)
    if not manifest.exists():
        print(f"{manifest.name} is missing -- ADR 0003 and 0005 cannot be checked.")
        return 1

    found = packages(manifest)
    failures = []

    drf = [p for p in found if p.lower().startswith("djangorestframework")]
    if drf:
        failures.append(
            f"ADR 0003 defers Django REST Framework, but requirements.txt has: {', '.join(drf)}.\n"
            "  Either drop it or supersede docs/adr/0003-backend.md."
        )

    test_stack = [p for p in found if p.lower().startswith(TEST_STACK_PREFIXES)]
    if len(test_stack) > TEST_STACK_BUDGET:
        failures.append(
            f"ADR 0005 budgets 3-{TEST_STACK_BUDGET} test packages; requirements.txt has "
            f"{len(test_stack)}: {', '.join(test_stack)}.\n"
            "  Adding one more means revisiting docs/adr/0005-testing.md."
        )

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1

    print(
        f"ok: no DRF, {len(test_stack)} test packages "
        f"(ADR 0005 budget is 3-{TEST_STACK_BUDGET})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(check())
