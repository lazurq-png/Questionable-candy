"""UC-08's three confirmations, as the server checks them (shop.forms.ConfirmOrderForm).

Each control is required on its own: the other two being right never makes up
for one that is missing or wrong.
"""
from decimal import Decimal

import pytest

from shop.forms import ConfirmOrderForm

TOTAL = Decimal("12.40")
ALL_THREE = {"checked_order": "on", "typed_total": "12.40", "place_order": "yes"}


def form(**changes):
    """The form bound to all three confirmations, with `changes` applied (None removes one)."""
    data = {**ALL_THREE, **changes}
    return ConfirmOrderForm({key: value for key, value in data.items() if value is not None}, total=TOTAL)


def test_all_three_confirmations_are_accepted():
    """The checkbox ticked, the total typed back, and the button pressed."""
    assert form().is_valid()


@pytest.mark.parametrize("missing", ["checked_order", "typed_total", "place_order"])
def test_each_confirmation_is_required_even_when_the_other_two_are_right(missing):
    """UC-08: three deliberate actions, so any one missing refuses the whole."""
    bound = form(**{missing: None})
    assert not bound.is_valid()
    assert missing in bound.errors


@pytest.mark.parametrize("typed", ["12.40", "12.4", "$12.40", " $ 12.40 ", "12,40"])
def test_the_total_may_be_typed_as_people_write_it(typed):
    """A leading $, a missing trailing zero or a decimal comma still say the same amount."""
    assert form(typed_total=typed).is_valid()


@pytest.mark.parametrize("typed", ["12.41", "1240", "12", "abc", "NaN", "Infinity", "-12.40"])
def test_any_other_total_is_refused_and_the_message_names_the_right_one(typed):
    """Typing the amount is only a confirmation if it is the amount."""
    bound = form(typed_total=typed)
    assert not bound.is_valid()
    assert bound.errors["typed_total"] == ["That is not the total. Type 12.40 to confirm."]


def test_place_order_must_carry_the_buttons_value():
    """A crafted post with some other value is not the button being pressed."""
    bound = form(place_order="no")
    assert not bound.is_valid()
    assert "place_order" in bound.errors
