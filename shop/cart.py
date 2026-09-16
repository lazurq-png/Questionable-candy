"""The shopping cart, kept in the session (ADR 0002): UC-04.

`request.session["shoppingcart"]` maps a candy's primary key, as a string, to a
quantity. Every function here reads that mapping, applies the rules UC-04 sets,
and writes it back -- so the rules live in one place rather than in each view:

- only published candy can be in the cart (UC-01 step 2, UC-03 ext. 2a);
- a quantity is at least 1 (the form, shop/forms.py, rejects anything else
  before it reaches here);
- a quantity never exceeds stock -- it is capped, or the addition is rejected,
  and either way the customer is told (UC-04 ext. 2a).

Functions return the messages to show rather than writing them anywhere, so a
view can hand them to an htmx partial or to the messages framework alike.
"""
from dataclasses import dataclass
from decimal import Decimal

from .models import Candy

SESSION_KEY = "shoppingcart"


@dataclass
class Line:
    """One candy in the cart, with its quantity and line total."""

    candy: Candy
    quantity: int

    @property
    def total(self):
        """The line's price: unit price times quantity."""
        return self.candy.price * self.quantity


def _stored(request):
    """The session mapping, dropping anything that is not a positive count."""
    raw = request.session.get(SESSION_KEY, {})
    clean = {}
    for key, value in raw.items() if isinstance(raw, dict) else ():
        if str(key).isdigit() and isinstance(value, int) and value > 0:
            clean[str(key)] = value
    return clean


def _save(request, stored):
    request.session[SESSION_KEY] = stored
    request.session.modified = True


def count(request):
    """Total number of items, for the header. Reads only; checks nothing."""
    return sum(_stored(request).values())


def add_one(request, candy):
    """Add a single `candy`. Returns (added, message).

    Rejected -- not capped -- when the cart already holds every one in stock,
    because there is nothing smaller to cap an addition of one to.
    """
    stored = _stored(request)
    in_cart = stored.get(str(candy.pk), 0)
    if candy.stock == 0:
        return False, f"{candy.name} is out of stock."
    if in_cart >= candy.stock:
        return False, f"Only {candy.stock} in stock, and they are all in your cart."
    stored[str(candy.pk)] = in_cart + 1
    _save(request, stored)
    return True, ""


def set_quantity(request, candy, quantity):
    """Set the quantity of a candy already in the cart. Returns a message or "".

    `quantity` is an already-validated whole number of at least 1. Only a candy
    already in the cart can be changed, so a crafted post cannot add one past
    add_one's rules.
    """
    stored = _stored(request)
    key = str(candy.pk)
    if key not in stored:
        return f"{candy.name} is not in your cart."
    if candy.stock == 0:
        del stored[key]
        _save(request, stored)
        return f"{candy.name} is out of stock and was removed from your cart."
    message = ""
    if quantity > candy.stock:
        quantity = candy.stock
        message = f"Only {candy.stock} of {candy.name} in stock, so the quantity is {candy.stock}."
    stored[key] = quantity
    _save(request, stored)
    return message


def remove(request, pk):
    """Take a candy out of the cart, whether or not it still exists."""
    stored = _stored(request)
    if stored.pop(str(pk), None) is not None:
        _save(request, stored)


def lines(request):
    """The cart's lines and total, after bringing it back in line with the shop.

    Returns (lines, total, messages). Entries whose candy was deleted or
    unpublished are dropped, and quantities above current stock are capped,
    because the cart may have been filled days ago. Either change is reported.
    """
    stored = _stored(request)
    candies = Candy.objects.published().in_bulk([int(pk) for pk in stored])
    result, messages = [], []
    unavailable = 0
    for key, quantity in list(stored.items()):
        candy = candies.get(int(key))
        if candy is None:
            del stored[key]
            unavailable += 1
            continue
        if candy.stock == 0:
            del stored[key]
            messages.append(f"{candy.name} is out of stock and was removed from your cart.")
            continue
        if quantity > candy.stock:
            quantity = stored[key] = candy.stock
            messages.append(
                f"Only {candy.stock} of {candy.name} left in stock, so the quantity is {candy.stock}."
            )
        result.append(Line(candy, quantity))
    if unavailable:
        noun = "item is" if unavailable == 1 else "items are"
        messages.insert(0, f"{unavailable} {noun} no longer available and removed from your cart.")
    if stored != _stored(request):
        _save(request, stored)
    result.sort(key=lambda line: line.candy.name)
    total = sum((line.total for line in result), Decimal("0.00"))
    return result, total, messages
