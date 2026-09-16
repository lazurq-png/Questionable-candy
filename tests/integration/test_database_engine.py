"""ADR 0004: the application runs on PostgreSQL 17 or later.

The ADR's confirmation section said nothing checked the engine version. This
asserts it against the connection the suite actually uses -- which is the same
DATABASE_URL the application uses (ADR 0004, ADR 0005), locally and in CI.
"""
import pytest
from django.db import connection

pytestmark = pytest.mark.django_db

MINIMUM_POSTGRESQL = 170000  # connection.pg_version encodes 17.0 as 170000


def test_the_database_is_postgresql():
    """ArrayField (User.allergies) exists only on PostgreSQL."""
    assert connection.vendor == "postgresql"


def test_the_postgresql_version_is_the_one_adr_0004_chose():
    """A minimum, not an exact match, so a planned upgrade does not fail the suite."""
    connection.ensure_connection()
    assert connection.pg_version >= MINIMUM_POSTGRESQL, connection.pg_version
