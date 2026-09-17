"""The user admin's allergies, one checkbox per allergen (night-2026-09-17 plan T2)."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db


def user_form(user, **overrides):
    """A complete, valid change form for `user` in the admin."""
    data = {
        "username": user.username,
        "first_name": "",
        "last_name": "",
        "email": "",
        "is_active": "on",
        "date_joined_0": "2026-09-17",
        "date_joined_1": "12:00:00",
        "_save": "Save",
    }
    data.update(overrides)
    return data


def test_the_user_admin_offers_a_checkbox_per_allergen(admin_client):
    """Allergies are ticked from the vocabulary, not typed."""
    user = get_user_model().objects.create_user(username="ada")

    response = admin_client.get(reverse("admin:accounts_user_change", args=[user.pk]))

    assert response.status_code == 200
    assert response.content.decode().count('type="checkbox" name="allergies"') == 14


def test_an_administrator_can_record_a_users_allergies(admin_client):
    """Ticked allergies are saved on the user."""
    user = get_user_model().objects.create_user(username="ada")

    response = admin_client.post(
        reverse("admin:accounts_user_change", args=[user.pk]),
        user_form(user, allergies=["peanuts", "milk"]),
    )

    assert response.status_code == 302
    user.refresh_from_db()
    assert sorted(user.allergies) == ["milk", "peanuts"]


def test_the_user_admin_rejects_an_allergy_outside_the_vocabulary(admin_client):
    """A crafted post with an unknown allergy is not saved."""
    user = get_user_model().objects.create_user(username="ada")

    response = admin_client.post(
        reverse("admin:accounts_user_change", args=[user.pk]),
        user_form(user, allergies=["lactose"]),
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.allergies == []
