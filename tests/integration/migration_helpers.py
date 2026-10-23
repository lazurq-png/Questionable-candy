"""Shared by the migration tests. Not collected by pytest: not a test_*.py."""


def settle_deferred_checks(connection):
    """Run the deferred constraint checks a commit would run, and keep deferring.

    A migration test runs the migrations' DDL inside the test's transaction
    (see test_migration_candy_timestamps.py). PostgreSQL refuses ALTER TABLE on
    a table whose rows were written in that same transaction while their
    deferred foreign-key checks are still pending -- which a real `migrate`
    never hits, because each migration commits. Calling this where those
    commits would happen is what stands in for them.
    """
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("SET CONSTRAINTS ALL DEFERRED")
