"""The UC-07 health warning's content, computed from cart lines (shop/checkout.py).

No database: candies and users are built in memory, because the warning is
arithmetic and grouping over what the cart already loaded.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model

from shop.cart import Line
from shop.checkout import health_warning
from shop.models import Candy


def candy(pk, name, sugar=None, allergens=()):
    """An unsaved candy with a primary key, as cart.lines() would load it."""
    return Candy(pk=pk, name=name, price=Decimal("1.00"), sugar_content_g=sugar, allergens=list(allergens))


def customer(*allergies):
    """An unsaved customer with the given allergies."""
    return get_user_model()(username="ada", allergies=list(allergies))


def test_total_sugar_counts_each_bag_as_100g():
    """Sugar per 100 g times bags, summed over the lines."""
    lines = [Line(candy(1, "Toffee", Decimal("48.0")), 2), Line(candy(2, "Drops", Decimal("92.5")), 1)]

    warning = health_warning(lines, customer())

    assert warning.total_sugar_g == Decimal("188.5")  # 48 x 2 + 92.5
    assert [line.grams for line in warning.sugar_lines] == [Decimal("96.0"), Decimal("92.5")]


def test_a_candy_with_unknown_sugar_is_named_and_not_counted_as_zero():
    """Unknown stays visible instead of silently lowering the total."""
    lines = [Line(candy(1, "Toffee", Decimal("48.0")), 1), Line(candy(2, "Mystery Chews"), 3)]

    warning = health_warning(lines, customer())

    assert warning.total_sugar_g == Decimal("48.0")
    assert warning.unknown_sugar == ["Mystery Chews"]
    assert warning.sugar_lines[1].grams is None


def test_zero_sugar_is_known_not_unknown():
    """0 g is a value; only None is unknown."""
    warning = health_warning([Line(candy(1, "Sugar-free Mints", Decimal("0")), 4)], customer())

    assert not warning.unknown_sugar
    assert warning.total_sugar_g == Decimal("0.0")


def test_allergens_are_listed_in_vocabulary_order_with_the_candies_containing_them():
    """One entry per allergen, naming every candy in the order that has it."""
    lines = [
        Line(candy(1, "Fudge", allergens=["milk", "soy"]), 1),
        Line(candy(2, "Licorice", allergens=["gluten"]), 1),
        Line(candy(3, "Toffee", allergens=["milk"]), 1),
    ]

    warning = health_warning(lines, customer())

    assert [(a.key, a.candies) for a in warning.allergens] == [
        ("gluten", ["Licorice"]),
        ("soy", ["Fudge"]),
        ("milk", ["Fudge", "Toffee"]),
    ]


def test_allergens_the_customer_listed_are_marked_as_theirs():
    """Matches against the customer's own allergies are flagged."""
    lines = [Line(candy(1, "Fudge", allergens=["milk", "soy"]), 1)]

    warning = health_warning(lines, customer("milk", "peanuts"))

    assert [(a.key, a.yours) for a in warning.allergens] == [("soy", False), ("milk", True)]
    assert [a.key for a in warning.matches] == ["milk"]
    assert warning.your_allergies == ["Peanuts", "Milk"]


def test_the_fingerprint_is_stable_for_the_same_order_and_customer():
    """The same warning twice gives the same fingerprint, or nothing could be acknowledged."""
    def build():
        """The warning for one fixed order and customer."""
        return health_warning([Line(candy(1, "Fudge", Decimal("70"), ["milk"]), 2)], customer("milk"))

    assert build().fingerprint == build().fingerprint


def test_the_fingerprint_changes_with_anything_the_warning_shows():
    """Quantity, sugar, allergens, another line, or the customer's own allergies."""
    base_candy = {"pk": 1, "name": "Fudge", "sugar": Decimal("70"), "allergens": ["milk"]}
    base = health_warning([Line(candy(**base_candy), 2)], customer("milk")).fingerprint

    variants = [
        health_warning([Line(candy(**base_candy), 3)], customer("milk")),
        health_warning([Line(candy(**{**base_candy, "sugar": Decimal("71")}), 2)], customer("milk")),
        health_warning([Line(candy(**{**base_candy, "allergens": ["milk", "soy"]}), 2)], customer("milk")),
        health_warning([Line(candy(**base_candy), 2), Line(candy(2, "Drops"), 1)], customer("milk")),
        health_warning([Line(candy(**base_candy), 2)], customer("milk", "eggs")),
    ]

    assert all(variant.fingerprint != base for variant in variants)
