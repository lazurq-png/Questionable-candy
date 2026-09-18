"""Migrations 0013-0014: what candy that predates slugs receives.

0013 adds the column nullable and fills it; 0014 makes it unique and required,
and names unique. Two names that slugify alike must still come out with
different slugs, or 0014 could not add the unique constraint.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from tests.integration.migration_helpers import settle_deferred_checks

BEFORE = [("shop", "0012_order_confirmation_token_required")]
FILLED = [("shop", "0013_candy_slug")]
AFTER = [("shop", "0014_candy_slug_required_and_names_unique")]


@pytest.mark.django_db
def test_candy_older_than_slugs_gets_a_distinct_slug_each():
    """Rows are created on the pre-0013 schema, then migrated forward.

    An ordinary database test, as test_migration_candy_timestamps.py explains.
    The deferred checks are run at the points a real migrate commits, as
    test_migration_order_confirmation_token.py does.
    """
    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE)
    old_candy = executor.loader.project_state(BEFORE).apps.get_model("shop", "Candy")
    old_candy.objects.create(name="Sour Bricks", price="1.00", flaw="Hard.")
    old_candy.objects.create(name="Sour-Bricks", price="1.00", flaw="Also hard.")
    old_candy.objects.create(name="!!!", price="1.00", flaw="Unnameable.")
    old_candy.objects.create(name="123", price="1.00", flaw="Numbered.")
    settle_deferred_checks(connection)

    executor = MigrationExecutor(connection)
    executor.migrate(FILLED)
    settle_deferred_checks(connection)
    executor = MigrationExecutor(connection)
    executor.migrate(AFTER)

    new_candy = executor.loader.project_state(AFTER).apps.get_model("shop", "Candy")
    slugs = dict(new_candy.objects.values_list("name", "slug"))
    assert slugs == {
        "Sour Bricks": "sour-bricks", "Sour-Bricks": "sour-bricks-2", "!!!": "candy",
        "123": "candy-123",  # digits alone would read as the old /candy/<pk>/ address
    }
