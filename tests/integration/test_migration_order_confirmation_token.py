"""Migrations 0011-0012: orders placed before confirmation tokens existed.

A unique, required column cannot be given one default for existing rows, so
0011 adds it nullable and gives each order its own token, and 0012 makes it
unique and required (docs/ai/night-2026-09-17/decisions.md D14). No such order
exists anywhere yet; this pins down that one would survive the migration.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from tests.integration.migration_helpers import settle_deferred_checks

BEFORE = [("shop", "0010_orders"), ("accounts", "0002_user_allergies_vocabulary")]
TOKENS_GIVEN = [("shop", "0011_order_confirmation_token")]
AFTER = [("shop", "0012_order_confirmation_token_required")]


@pytest.mark.django_db
def test_orders_older_than_the_token_each_get_a_distinct_one():
    """Two orders created on the pre-0011 schema, then migrated forward.

    An ordinary database test, as test_migration_candy_timestamps.py explains:
    PostgreSQL runs the migrations' DDL inside the test's transaction. It
    refuses ALTER TABLE on a table whose rows were written in the same
    transaction while their deferred foreign-key checks are still pending --
    which is why 0011's updates and 0012's ALTER are two migrations. In a real
    database the orders were committed long ago, and 0011 commits before 0012;
    each commit runs those checks. settle_deferred_checks() stands in for them
    at the same two points.
    """
    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE)
    old_apps = executor.loader.project_state(BEFORE).apps
    user = old_apps.get_model("accounts", "User").objects.create(username="predates-tokens")
    old_order = old_apps.get_model("shop", "Order")
    old_order.objects.create(user=user, total_amount="1.00", status="pending")
    old_order.objects.create(user=user, total_amount="2.00", status="pending")
    settle_deferred_checks(connection)

    executor = MigrationExecutor(connection)
    executor.migrate(TOKENS_GIVEN)
    settle_deferred_checks(connection)
    executor = MigrationExecutor(connection)
    executor.migrate(AFTER)

    new_order = executor.loader.project_state(AFTER).apps.get_model("shop", "Order")
    tokens = list(new_order.objects.values_list("confirmation_token", flat=True))
    assert len(tokens) == 2
    assert None not in tokens
    assert len(set(tokens)) == 2
