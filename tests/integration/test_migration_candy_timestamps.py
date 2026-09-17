"""Migrations 0007-0008: what candy that predates the timestamps receives.

Django's schema editor fills an auto_now/auto_now_add column with the current
time for rows that already exist -- even while the column is nullable. So such
a row does not keep "unknown": it gets the moment the migration ran. This pins
that down, because it is the opposite of what the first version of this change
assumed (docs/ai/night-2026-09-16/decisions.md D9).
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

BEFORE = [("shop", "0006_candy_image")]
AFTER = [("shop", "0008_alter_candy_created_at_alter_candy_updated_at")]


@pytest.mark.django_db
def test_candy_older_than_the_timestamps_gets_the_migration_time_not_null():
    """The row is created on the pre-0007 schema, then migrated forward.

    An ordinary (not transactional) database test on purpose: PostgreSQL runs
    the migrations' DDL inside the test's transaction, and its rollback restores
    the schema. A transactional test would also be scheduled after the browser
    tests, where Playwright's event loop makes Django refuse database access
    outside tests/e2e/ (tests/e2e/conftest.py).
    """
    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE)
    old_candy = executor.loader.project_state(BEFORE).apps.get_model("shop", "Candy")
    old_candy.objects.create(name="Predates Timestamps", price="1.00", flaw="Old.")

    migrated_at = timezone.now()
    executor = MigrationExecutor(connection)
    executor.migrate(AFTER)

    new_candy = executor.loader.project_state(AFTER).apps.get_model("shop", "Candy")
    candy = new_candy.objects.get(name="Predates Timestamps")
    assert candy.created_at is not None
    assert candy.created_at >= migrated_at.replace(microsecond=0)
