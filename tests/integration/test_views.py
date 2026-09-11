import pytest
from django.urls import reverse
from tests.factories.candy_factory import CandyProductFactory

pytestmark = pytest.mark.django_db

def test_add_to_cart_returns_partial_with_added_label(client):
    candy = CandyProductFactory(name="Sour Gummy Worms")
    url = reverse("add_to_cart", args=[candy.id])
    response = client.post(url)
    assert response.status_code == 200
    assert b"Added" in response.content
    assert b"<html" not in response.content  # confirms it's a partial, not a full page

def test_candy_list_shows_all_candies(client):
    CandyProductFactory(name="Sour Gummy Worms")
    CandyProductFactory(name="Chocolate Fudge")

    response = client.get(reverse("candy_list"))

    assert response.status_code == 200
    assert b"Sour Gummy Worms" in response.content
    assert b"Chocolate Fudge" in response.content