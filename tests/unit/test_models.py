from decimal import Decimal

import pytest

from shop.models import CandyProduct


def test_str_is_the_candy_name():
    """__str__ drives the admin list and any {{ candy }} in a template."""
    assert str(CandyProduct(name="Sour Gummy Worms")) == "Sour Gummy Worms"


@pytest.mark.django_db
def test_price_round_trips_as_decimal():
    """Money must not become a float on the way through the database."""
    CandyProduct.objects.create(name="Hollow Humbug", price=Decimal("9.95"), flaw="hollow")

    stored = CandyProduct.objects.get(name="Hollow Humbug")

    assert stored.price == Decimal("9.95")
    assert isinstance(stored.price, Decimal)


@pytest.mark.django_db
def test_stock_defaults_to_zero():
    """A candy with no stock stated is out of stock, not unbounded."""
    CandyProduct.objects.create(name="Regrettable Toffee", price=Decimal("1.00"), flaw="stale")

    assert CandyProduct.objects.get(name="Regrettable Toffee").stock == 0
