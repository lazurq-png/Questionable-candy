"""UC-01 extension 3a: the catalog's sort menu, on the server side.

The browser side -- htmx swapping the grid and the address bar following --
is tests/e2e/test_catalog_sort.py.
"""
from decimal import Decimal

import pytest
from django.urls import reverse

from shop.models import Candy, FlawSeverity
from shop.views import CATALOG_SORTS

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    """Four candy whose name, price and severity orders all differ."""
    rows = [
        ("Butterscotch Pillows", "4.60", FlawSeverity.MILD),
        ("Sour Bricks", "12.50", FlawSeverity.DENTAL),
        ("Ginger Snap Drops", "3.40", FlawSeverity.AWKWARD),
        ("Mystery Toffee", "4.60", None),  # unrated; same price as the pillows
    ]
    for name, price, severity in rows:
        Candy.objects.create(name=name, price=Decimal(price), flaw="Flawed.", stock=5,
                             flaw_severity=severity)


def names(client, **params):
    """The candy names the catalog lists for these query parameters."""
    response = client.get(reverse("candy_list"), params)
    assert response.status_code == 200
    return [candy.name for candy in response.context["candies"]]


@pytest.mark.usefixtures("catalog")
def test_with_no_choice_the_catalog_is_alphabetical(client):
    assert names(client) == [
        "Butterscotch Pillows", "Ginger Snap Drops", "Mystery Toffee", "Sour Bricks",
    ]


@pytest.mark.usefixtures("catalog")
def test_price_low_to_high_breaks_ties_by_name(client):
    assert names(client, sort="price") == [
        "Ginger Snap Drops", "Butterscotch Pillows", "Mystery Toffee", "Sour Bricks",
    ]


@pytest.mark.usefixtures("catalog")
def test_price_high_to_low_still_breaks_ties_alphabetically(client):
    assert names(client, sort="price-desc") == [
        "Sour Bricks", "Butterscotch Pillows", "Mystery Toffee", "Ginger Snap Drops",
    ]


@pytest.mark.usefixtures("catalog")
def test_least_damaging_first_puts_unrated_candy_last(client):
    """Not rated is not harmless, so it does not sort as the mildest."""
    assert names(client, sort="severity") == [
        "Butterscotch Pillows", "Ginger Snap Drops", "Sour Bricks", "Mystery Toffee",
    ]


@pytest.mark.parametrize("value", ["", "bogus", "-name", "price;drop"])
@pytest.mark.usefixtures("catalog")
def test_an_unknown_sort_gets_the_default_order_not_an_error(client, value):
    assert names(client, sort=value) == names(client)


@pytest.mark.usefixtures("catalog")
def test_the_menu_offers_every_order_and_marks_the_current_one(client):
    content = client.get(reverse("candy_list"), {"sort": "price-desc"}).content.decode()

    for key, (label, _) in CATALOG_SORTS.items():
        assert f'value="{key}"' in content
        assert label in content
    assert '<option value="price-desc" selected>' in content
    assert '<option value="name" selected>' not in content


@pytest.mark.usefixtures("catalog")
def test_the_menu_works_without_javascript(client):
    """A GET form naming the catalog, with a submit button for no-script."""
    content = client.get(reverse("candy_list")).content.decode()

    assert f'method="get" action="{reverse("candy_list")}"' in content
    assert '<noscript><button type="submit"' in content


def test_an_empty_catalog_offers_nothing_to_sort(client):
    content = client.get(reverse("candy_list")).content.decode()

    assert 'data-testid="catalog-empty"' in content
    assert 'data-testid="catalog-sort"' not in content


@pytest.mark.usefixtures("catalog")
def test_a_rated_candy_shows_its_badge_and_an_unrated_one_none(client):
    content = client.get(reverse("candy_list")).content.decode()

    assert content.count('data-testid="candy-severity"') == 3
    assert "Flaw severity: </span>Call your dentist" in content


@pytest.mark.usefixtures("catalog")
def test_the_detail_page_states_the_rating(client):
    candy = Candy.objects.get(name="Sour Bricks")

    content = client.get(candy.get_absolute_url()).content.decode()

    assert "Severity: Call your dentist" in content


@pytest.mark.usefixtures("catalog")
def test_the_detail_page_of_an_unrated_candy_says_nothing_about_severity(client):
    candy = Candy.objects.get(name="Mystery Toffee")

    content = client.get(candy.get_absolute_url()).content.decode()

    assert 'data-testid="candy-flaw-severity"' not in content
