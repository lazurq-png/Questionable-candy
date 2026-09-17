"""The custom user model -- docs/adr/0007-custom-user-model.md."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction


def test_the_active_user_model_is_accounts_user():
    """Every get_user_model() and ForeignKey to AUTH_USER_MODEL resolves here.

    If this regresses to auth.User, allergies silently has nowhere to live.
    """
    assert get_user_model()._meta.label == "accounts.User"


@pytest.mark.django_db
def test_a_new_user_has_no_allergies_rather_than_unknown_allergies():
    """Not null, default empty: [] is the only way to store "none"."""
    user = get_user_model().objects.create_user(username="ada")
    user.refresh_from_db()
    assert user.allergies == []


@pytest.mark.django_db
def test_allergies_round_trip_as_a_list():
    """Stored as a PostgreSQL array, read back as a Python list in order."""
    user_model = get_user_model()
    user_model.objects.create_user(username="ada", allergies=["peanuts", "gluten"])
    assert user_model.objects.get(username="ada").allergies == ["peanuts", "gluten"]


@pytest.mark.django_db
def test_the_database_refuses_null_allergies():
    """The single-representation choice holds below the ORM, not only in forms."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            get_user_model().objects.create_user(username="ada", allergies=None)


@pytest.mark.django_db
def test_users_can_be_found_by_a_shared_allergy():
    """The reason for ArrayField: matching against a cart's allergens (UC-07)."""
    user_model = get_user_model()
    user_model.objects.create_user(username="ada", allergies=["peanuts", "gluten"])
    user_model.objects.create_user(username="bob", allergies=["lactose"])

    matched = user_model.objects.filter(allergies__overlap=["gluten", "soy"])

    assert [u.username for u in matched] == ["ada"]
