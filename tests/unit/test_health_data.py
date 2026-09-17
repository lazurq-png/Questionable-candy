"""Sugar and allergens on Candy, and the allergen vocabulary (plan T2).

The vocabulary is what lets the UC-07 warning match a customer's allergies to
a candy's allergens exactly, so both fields are held to it -- by clean_fields()
here, and by the admin forms in tests/integration.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from shop import allergens
from shop.models import Candy


def test_the_vocabulary_is_the_eu_fourteen_with_unique_keys_that_fit_the_column():
    """Fourteen distinct keys, each short enough for Candy.allergens' column."""
    keys = [key for key, _ in allergens.ALLERGENS]
    assert len(keys) == 14
    assert len(set(keys)) == 14
    assert max(len(key) for key in keys) <= allergens.KEY_LENGTH


def test_allergen_names_are_labels_in_vocabulary_order():
    """Order follows the vocabulary, not the stored list; unknown keys are skipped."""
    candy = Candy(allergens=["soy", "milk", "not-an-allergen"])
    assert candy.allergen_names() == ["Soybeans", "Milk"]


def test_a_candy_accepts_allergens_from_the_vocabulary():
    """Keys from shop.allergens pass field validation."""
    Candy(name="Toffee", price=Decimal("1.00"), flaw="Sticks.", allergens=["milk", "soy"]).clean_fields()


def test_a_candy_rejects_an_allergen_outside_the_vocabulary():
    """A key outside the vocabulary fails validation on the allergens field."""
    candy = Candy(name="Toffee", price=Decimal("1.00"), flaw="Sticks.", allergens=["milk", "nuts"])
    with pytest.raises(ValidationError) as error:
        candy.clean_fields()
    assert "allergens" in error.value.message_dict


def test_a_user_rejects_an_allergy_outside_the_vocabulary():
    """The same vocabulary as Candy.allergens, or the two cannot be matched."""
    user = get_user_model()(username="ada", password="x", allergies=["tree-nuts", "lactose"])
    with pytest.raises(ValidationError) as error:
        user.clean_fields()
    assert "allergies" in error.value.message_dict


def test_a_user_accepts_allergies_from_the_vocabulary():
    """The user's allergies take the same keys as a candy's allergens."""
    get_user_model()(username="ada", password="x", allergies=["tree-nuts", "milk"]).clean_fields()


@pytest.mark.parametrize("sugar", [Decimal("0"), Decimal("48.5"), Decimal("100"), None])
def test_sugar_per_100g_may_be_anything_from_0_to_100_or_unknown(sugar):
    """Both ends of the range, a value between, and unknown are all valid."""
    Candy(name="Toffee", price=Decimal("1.00"), flaw="Sticks.", sugar_content_g=sugar).clean_fields()


@pytest.mark.parametrize("sugar", [Decimal("-0.1"), Decimal("100.1")])
def test_sugar_per_100g_outside_0_to_100_is_rejected_by_validation(sugar):
    """No candy is less than 0% or more than 100% sugar."""
    candy = Candy(name="Toffee", price=Decimal("1.00"), flaw="Sticks.", sugar_content_g=sugar)
    with pytest.raises(ValidationError) as error:
        candy.clean_fields()
    assert "sugar_content_g" in error.value.message_dict


@pytest.mark.django_db
@pytest.mark.parametrize("sugar", [Decimal("-1"), Decimal("100.5")])
def test_the_database_refuses_sugar_outside_0_to_100(sugar):
    """Through the manager, which runs no validation: the check constraint holds."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Candy.objects.create(name="Toffee", price=Decimal("1.00"), flaw="Sticks.", sugar_content_g=sugar)


@pytest.mark.django_db
def test_unknown_sugar_and_no_allergens_are_the_defaults_and_round_trip():
    """Defaults are unknown and empty; 0 g and a list survive the database."""
    candy = Candy.objects.create(name="Toffee", price=Decimal("1.00"), flaw="Sticks.")
    candy.refresh_from_db()
    assert candy.sugar_content_g is None
    assert candy.allergens == []

    Candy.objects.filter(pk=candy.pk).update(sugar_content_g=Decimal("0"), allergens=["eggs", "milk"])
    candy.refresh_from_db()
    assert candy.sugar_content_g == Decimal("0.0")
    assert candy.allergens == ["eggs", "milk"]
