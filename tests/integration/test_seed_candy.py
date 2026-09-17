"""`python manage.py seed_candy` -- safe to run any number of times."""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from shop.management.commands.seed_candy import CANDIES
from shop.models import Candy

pytestmark = pytest.mark.django_db


def seed():
    """Run the command, keeping its summary line out of the test output."""
    out = StringIO()
    call_command("seed_candy", stdout=out)
    return out.getvalue()


def test_seeding_creates_every_candy():
    """All of them, and all published."""
    seed()
    assert Candy.objects.count() == len(CANDIES)
    assert Candy.objects.published().count() == len(CANDIES)


def test_seeding_twice_creates_nothing_new():
    """Matched by name, so a second run finds every row already there."""
    seed()
    seed()
    assert Candy.objects.count() == len(CANDIES)


def test_seeding_never_overwrites_a_value_that_is_already_set():
    """An administrator's later edit survives every re-seed."""
    seed()
    Candy.objects.filter(name="Sour Bricks").update(price=Decimal("99.00"), flaw="Edited flaw.")

    seed()

    candy = Candy.objects.get(name="Sour Bricks")
    assert candy.price == Decimal("99.00")
    assert candy.flaw == "Edited flaw."


def test_seeding_fills_only_the_empty_fields_of_an_existing_candy():
    """How the two candies that predate the seed get a description and picture."""
    Candy.objects.create(
        name="Hollow Humbug", price=Decimal("1.23"), stock=7, flavor="mint",
        flaw="An existing flaw.", description="",
    )

    seed()

    candy = Candy.objects.get(name="Hollow Humbug")
    assert candy.description  # was empty, now filled
    assert candy.image == "shop/candy/hollow-humbug.svg"
    assert candy.price == Decimal("1.23")  # was set, kept
    assert candy.stock == 7
    assert candy.flaw == "An existing flaw."


# --- Sugar and allergens (night-2026-09-17 plan T2) -------------------------

def test_every_seeded_candy_has_known_sugar_and_valid_allergens():
    """The UC-07 warning names candies with unknown sugar; seeded ones have none."""
    seed()
    for candy in Candy.objects.all():
        assert candy.sugar_content_g is not None, candy.name
        candy.clean_fields()  # sugar in range, allergens from the vocabulary


def test_seeding_fills_empty_sugar_and_allergens_on_an_existing_candy():
    """A candy created before these fields gets the seed's values."""
    Candy.objects.create(name="Salted Caramel Chews", price=Decimal("1.00"), flaw="Sticky.")

    seed()

    candy = Candy.objects.get(name="Salted Caramel Chews")
    assert candy.sugar_content_g == Decimal("48.0")
    assert candy.allergens == ["milk"]


def test_seeding_keeps_a_sugar_content_of_zero_and_edited_allergens():
    """0 g is a real value, not an empty one, so a re-seed must not replace it."""
    seed()
    Candy.objects.filter(name="Salted Caramel Chews").update(sugar_content_g=Decimal("0"), allergens=["eggs"])

    seed()

    candy = Candy.objects.get(name="Salted Caramel Chews")
    assert candy.sugar_content_g == Decimal("0.0")
    assert candy.allergens == ["eggs"]
