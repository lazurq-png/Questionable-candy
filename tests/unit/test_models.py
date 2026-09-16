from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from shop.models import Candy


def test_str_is_the_candy_name():
    """__str__ drives the admin list and any {{ candy }} in a template."""
    assert str(Candy(name="Sour Gummy Worms")) == "Sour Gummy Worms"


@pytest.mark.django_db
def test_price_round_trips_as_decimal():
    """Money must not become a float on the way through the database."""
    Candy.objects.create(name="Hollow Humbug", price=Decimal("9.95"), flaw="hollow")

    stored = Candy.objects.get(name="Hollow Humbug")

    assert stored.price == Decimal("9.95")
    assert isinstance(stored.price, Decimal)


@pytest.mark.django_db
def test_stock_defaults_to_zero():
    """A candy with no stock stated is out of stock, not unbounded."""
    Candy.objects.create(name="Regrettable Toffee", price=Decimal("1.00"), flaw="stale")

    assert Candy.objects.get(name="Regrettable Toffee").stock == 0


# --- UC-06: a flaw can never be silently omitted ---------------------------
#
# UC-06's Constraint is explicit that this holds "at the data-model level, not
# only in the form". NOT NULL does not deliver it: the empty string satisfies
# NOT NULL, and objects.create() never runs form validation. These tests go
# through the manager for exactly that reason -- a test that called full_clean
# would be checking the half of the guarantee that was never in doubt.

@pytest.mark.django_db
def test_a_candy_cannot_be_saved_without_a_flaw():
    """The whole premise of the shop is that every candy discloses one."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Candy.objects.create(
                name="Suspiciously Perfect Truffle", price=Decimal("3.00"), flaw=""
            )


@pytest.mark.django_db
def test_whitespace_does_not_count_as_a_flaw():
    """Otherwise the constraint is defeated by pressing the space bar.

    Django's form field strips whitespace before testing for blank, so the form
    already rejects this; the database has to agree or the two disagree about
    what "has a flaw" means.
    """
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Candy.objects.create(
                name="Suspiciously Perfect Truffle", price=Decimal("3.00"), flaw="   "
            )


@pytest.mark.django_db
def test_a_candy_with_a_flaw_saves_normally():
    """The constraint must not reject the ordinary case."""
    candy = Candy.objects.create(
        name="Hollow Humbug", price=Decimal("9.95"), flaw="Hollow, and not on purpose."
    )

    assert Candy.objects.get(pk=candy.pk).flaw == "Hollow, and not on purpose."


@pytest.mark.django_db
def test_model_validation_also_rejects_a_missing_flaw():
    """UC-06 extension 2a's "prompts for one" half.

    The constraint above stops a bad row reaching the table; this is what turns
    it into a message on a form rather than an IntegrityError page.

    Marked django_db even though it passes without the mark today. That is an
    accident of ordering: clean_fields() fails first, which puts `flaw` in
    full_clean()'s exclude set, which makes constraint validation skip it
    without ever querying. Lose `blank=False` -- the very regression this test
    guards -- and clean_fields() passes, validate_constraints() runs real SQL,
    and the failure becomes "Database access not allowed" instead of the
    assertion below. Still red, but pointing at the wrong thing.
    """
    candy = Candy(name="Suspiciously Perfect Truffle", price=Decimal("3.00"), flaw="")

    with pytest.raises(ValidationError) as raised:
        candy.full_clean()

    assert "flaw" in raised.value.error_dict


@pytest.mark.django_db
def test_model_validation_rejects_a_whitespace_flaw_via_the_constraint():
    """The one path where the new CheckConstraint's own validation does the work.

    "   " passes clean_fields() -- it is not blank as far as the field is
    concerned -- so it survives to validate_constraints(), which runs the
    constraint as a query. That is behaviour this constraint introduced, and it
    is the only route by which it is reached.

    The error lands under __all__ rather than on `flaw`, because a constraint
    is not attached to a field. That is what makes violation_error_message
    worth setting: without it the user is shown Django's generic text for a
    constraint they have never heard of.
    """
    candy = Candy(name="Suspiciously Perfect Truffle", price=Decimal("3.00"), flaw="   ")

    with pytest.raises(ValidationError) as raised:
        candy.full_clean()

    assert "Every candy must disclose a flaw (UC-06)." in raised.value.messages
