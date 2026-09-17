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

from .checkout import SESSION_KEY as CHECKOUT_SESSION_KEY
from .models import Candy

SESSION_KEY = "shoppingcart"

# What the stepper says when nothing more of a candy can go in the cart --
# whether none is left or the cart already holds every one. Shown in a bubble
# beside that candy's own stepper, so it needs no name and no explanation.
OUT_OF_STOCK = "Out of stock"


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
    """Write the cart back -- and forget any checkout progress made for the old one.

    The health warning (UC-07) and the confirmations after it were for the
    order as it was; any change to the cart means reading them again, even a
    change that is later undone (shop/checkout.py).
    """
    request.session[SESSION_KEY] = stored
    request.session.pop(CHECKOUT_SESSION_KEY, None)
    request.session.modified = True


def count(request):
    """Total number of items, for the header. Reads only; checks nothing."""
    return sum(_stored(request).values())


def add_one(request, candy):
    """Add a single `candy`. Returns (added, message).

    Rejected -- not capped -- when the cart already holds every one in stock,
    because there is nothing smaller to cap an addition of one to. That covers
    a candy with no stock at all, where the cart holds every one of nothing.
    """
    stored = _stored(request)
    in_cart = stored.get(str(candy.pk), 0)
    if in_cart >= candy.stock:
        return False, OUT_OF_STOCK
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


def set_or_add(request, candy, quantity):
    """Set a candy's quantity from its stepper. Returns (changed, message).

    Unlike set_quantity(), the candy need not be in the cart yet -- the stepper
    is the add-to-cart control -- so add_one()'s rules apply as well: nothing
    goes in once stock is 0, and a quantity above stock is capped and said so.
    `quantity` is an already-validated whole number of at least 0; 0 takes the
    candy out.

    The messages here name no candy, and say only what changed: they are shown
    in a bubble against that candy's own stepper (site.css). A cart line's
    notices (set_quantity, lines) do name it -- they appear above a list of
    lines, where the customer cannot otherwise tell which one is meant.
    """
    stored = _stored(request)
    key = str(candy.pk)
    before = stored.get(key, 0)
    message = ""
    if quantity == 0:
        stored.pop(key, None)
    elif candy.stock == 0:
        stored.pop(key, None)
        message = OUT_OF_STOCK
    else:
        if quantity > candy.stock:
            quantity = candy.stock
            message = f"Only {candy.stock} in stock"
        stored[key] = quantity
    changed = stored.get(key, 0) != before
    if changed:
        _save(request, stored)
    return changed, message


def quantities(request):
    """Each candy's quantity by primary key, for the add-to-cart steppers.

    Reads only and checks nothing, like count(): the stepper shows what the
    session holds, and the cart page is where it is reconciled with the shop.
    """
    return {int(key): value for key, value in _stored(request).items()}


def remove(request, pk):
    """Take a candy out of the cart, whether or not it still exists."""
    stored = _stored(request)
    if stored.pop(str(pk), None) is not None:
        _save(request, stored)


def remove_one(request, pk):
    """Take one of a candy out of the cart. Returns whether anything changed.

    Taking the last one removes the entry, so the cart never holds a zero.
    Works whether or not the candy still exists, like remove().
    """
    stored = _stored(request)
    key = str(pk)
    if key not in stored:
        return False
    if stored[key] > 1:
        stored[key] -= 1
    else:
        del stored[key]
    _save(request, stored)
    return True


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
