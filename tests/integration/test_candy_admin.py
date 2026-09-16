"""UC-06 steps 1-2 and extension 2a, on the administrator's side."""
from decimal import Decimal

import pytest
from django.urls import reverse

from shop.admin import FLAW_REQUIRED
from shop.models import Candy

pytestmark = pytest.mark.django_db


def candy_form(**overrides):
    """A complete, valid add/change form for the Candy admin."""
    data = {
        "name": "Sour Bricks",
        "flaw": "Chips a tooth on contact.",
        "description": "Dense and sour.",
        "flavor": "sour",
        "price": "12.50",
        "stock": "10",
        "is_published": "on",
        "image": "",
        "_save": "Save",
    }
    data.update(overrides)
    return data


def test_an_administrator_can_record_a_candy_with_its_flaw(admin_client):
    """Step 1: creating a candy records its flaw."""
    response = admin_client.post(reverse("admin:shop_candy_add"), candy_form())

    assert response.status_code == 302
    assert Candy.objects.get(name="Sour Bricks").flaw == "Chips a tooth on contact."


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_saving_a_new_candy_without_a_flaw_is_rejected_with_a_prompt(admin_client, blank):
    """Extension 2a: rejected, and the form says what is missing and why."""
    response = admin_client.post(reverse("admin:shop_candy_add"), candy_form(flaw=blank))

    assert response.status_code == 200  # the form is shown again, not saved
    assert FLAW_REQUIRED in response.content.decode()
    assert not Candy.objects.exists()


def test_editing_a_candy_to_remove_its_flaw_is_rejected(admin_client):
    """Extension 2a on the edit path, which keeps the flaw it had."""
    candy = Candy.objects.create(name="Sour Bricks", price=Decimal("1.00"), flaw="Hard.")

    response = admin_client.post(
        reverse("admin:shop_candy_change", args=[candy.pk]), candy_form(flaw="  ")
    )

    assert response.status_code == 200
    assert FLAW_REQUIRED in response.content.decode()
    assert Candy.objects.get(pk=candy.pk).flaw == "Hard."


def test_the_admin_list_shows_publication_state(admin_client):
    """So an administrator can find what is hidden from the catalog."""
    Candy.objects.create(name="Withdrawn Toffee", price=Decimal("1.00"), flaw="Stale.", is_published=False)

    response = admin_client.get(reverse("admin:shop_candy_changelist"))

    assert response.status_code == 200
    assert b"Withdrawn Toffee" in response.content
    # The column header class, which only list_display renders -- the list
    # filter's links contain "is_published" whether or not the column exists.
    assert b"column-is_published" in response.content
