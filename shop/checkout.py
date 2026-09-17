"""Checkout past the review page: the health warning (UC-07).

Kept in the session beside the cart (ADR 0002), as `cart.py` keeps the cart:
`request.session["checkout"]` records what the customer has acknowledged.

An acknowledgment is tied to a fingerprint of exactly what the warning showed
-- each line's candy, quantity, sugar and allergens, and the customer's own
allergies. If any of that changes, the fingerprint no longer matches and the
warning has to be read again: UC-07 asks that the warning be acknowledged,
and a warning about a different order was not.
"""
import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal

from django.utils import timezone

from . import allergens

SESSION_KEY = "checkout"

# How much candy one bag is, for turning sugar per 100 g into grams. The shop
# records no bag weights, so every bag counts as 100 g, and the warning says so.
GRAMS_PER_BAG = Decimal("100")


@dataclass(frozen=True)
class SugarLine:
    """One cart line's sugar: None when the candy's sugar is unknown."""

    name: str
    quantity: int
    per_100g: Decimal | None
    grams: Decimal | None


@dataclass(frozen=True)
class AllergenInOrder:
    """One allergen present in the order, and which candies contain it."""

    key: str
    label: str
    candies: list[str]
    yours: bool


@dataclass(frozen=True)
class HealthWarning:
    """Everything the UC-07 warning shows, computed from the cart's lines."""

    sugar_lines: list[SugarLine]
    total_sugar_g: Decimal
    unknown_sugar: list[str]
    allergens: list[AllergenInOrder]
    fingerprint: str
    your_allergies: list[str] = field(default_factory=list)

    @property
    def matches(self):
        """The allergens in the order that the customer said they are allergic to."""
        return [allergen for allergen in self.allergens if allergen.yours]


def health_warning(lines, user):
    """The warning for `lines` (cart.Line) and the signed-in `user`."""
    yours = set(user.allergies)
    sugar_lines, unknown = [], []
    total = Decimal("0.0")
    for line in lines:
        per_100g = line.candy.sugar_content_g
        if per_100g is None:
            unknown.append(line.candy.name)
            grams = None
        else:
            grams = per_100g * GRAMS_PER_BAG / 100 * line.quantity
            total += grams
        sugar_lines.append(SugarLine(line.candy.name, line.quantity, per_100g, grams))

    in_order = []
    for key, label in allergens.ALLERGENS:
        candies = [line.candy.name for line in lines if key in line.candy.allergens]
        if candies:
            in_order.append(AllergenInOrder(key, label, candies, key in yours))

    return HealthWarning(
        sugar_lines=sugar_lines,
        total_sugar_g=total.quantize(Decimal("0.1")),
        unknown_sugar=unknown,
        allergens=in_order,
        fingerprint=_fingerprint(lines, yours),
        your_allergies=allergens.names(yours),
    )


def _fingerprint(lines, your_allergies):
    content = {
        "lines": sorted(
            [line.candy.pk, line.quantity, str(line.candy.sugar_content_g), sorted(line.candy.allergens)]
            for line in lines
        ),
        "yours": sorted(your_allergies),
    }
    return hashlib.sha256(json.dumps(content).encode()).hexdigest()


def acknowledge(request, warning):
    """Record that the customer acknowledged exactly this warning, and when."""
    request.session[SESSION_KEY] = {
        "warning": {"fingerprint": warning.fingerprint, "at": timezone.now().isoformat()},
    }


def is_acknowledged(request, warning):
    """Whether this warning, as it now stands, has been acknowledged."""
    stored = request.session.get(SESSION_KEY, {})
    acknowledged = stored.get("warning", {}) if isinstance(stored, dict) else {}
    return isinstance(acknowledged, dict) and acknowledged.get("fingerprint") == warning.fingerprint
