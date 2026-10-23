"""A candy's flaw severity: the model, the admin and the seed.

Null means "not rated yet" -- deliberately not the same as mild, so nothing
here or in the catalog treats an unrated candy as harmless.
"""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse

from shop.management.commands.seed_candy import CANDIES
from shop.models import Candy, FlawSeverity
from tests.integration.test_candy_admin import candy_form

pytestmark = pytest.mark.django_db


def make(**fields):
    """A saved candy with these fields overriding the defaults."""
    return Candy.objects.create(name="Sour Bricks", price=Decimal("1.00"), flaw="Hard.", **fields)


def test_ratings_run_from_least_to_most_damaging():
    """The values are the sort order for "least damaging first"."""
    assert FlawSeverity.MILD < FlawSeverity.AWKWARD < FlawSeverity.DENTAL


def test_a_new_candy_is_not_rated_until_someone_rates_it():
    assert make().flaw_severity is None


def test_the_database_refuses_a_rating_outside_the_list():
    """objects.create() skips the choices check, so the constraint is the guard."""
    with pytest.raises(IntegrityError), transaction.atomic():
        make(flaw_severity=4)


def test_model_validation_refuses_a_rating_outside_the_list():
    candy = Candy(name="Sour Bricks", price=Decimal("1.00"), flaw="Hard.", flaw_severity=9)
    with pytest.raises(ValidationError):
        candy.full_clean()


def test_an_administrator_rates_a_candy(admin_client):
    response = admin_client.post(
        reverse("admin:shop_candy_add"), candy_form(flaw_severity=str(FlawSeverity.DENTAL))
    )

    assert response.status_code == 302
    assert Candy.objects.get(name="Sour Bricks").flaw_severity == FlawSeverity.DENTAL


def test_an_administrator_may_leave_a_candy_unrated(admin_client):
    response = admin_client.post(reverse("admin:shop_candy_add"), candy_form())

    assert response.status_code == 302
    assert Candy.objects.get(name="Sour Bricks").flaw_severity is None


def test_the_admin_list_shows_and_filters_by_rating(admin_client):
    make(flaw_severity=FlawSeverity.AWKWARD)

    response = admin_client.get(reverse("admin:shop_candy_changelist"))

    assert b"column-flaw_severity" in response.content
    assert b"flaw_severity__exact" in response.content  # the list filter's links


def seed():
    """Run the seed command quietly."""
    call_command("seed_candy", stdout=StringIO())


def test_every_seeded_candy_is_rated():
    seed()
    assert not Candy.objects.filter(flaw_severity__isnull=True).exists()
    assert Candy.objects.count() == len(CANDIES)


def test_seeding_rates_an_existing_unrated_candy_but_never_changes_a_rating():
    """Like every other fillable field: empty is filled, set is left alone."""
    make()
    Candy.objects.create(
        name="Hollow Humbug", price=Decimal("9.00"), flaw="Hollow.", flaw_severity=FlawSeverity.DENTAL
    )

    seed()

    seeded = {c["name"]: c["flaw_severity"] for c in CANDIES}
    assert Candy.objects.get(name="Sour Bricks").flaw_severity == seeded["Sour Bricks"]
    assert Candy.objects.get(name="Hollow Humbug").flaw_severity == FlawSeverity.DENTAL
