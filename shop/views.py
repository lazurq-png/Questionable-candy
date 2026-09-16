from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import cart
from .forms import QuantityForm
from .models import Candy


def candy_list(request):
    """UC-01: the published candy, alphabetically.

    Without an ORDER BY, PostgreSQL returns rows in whatever order is cheapest,
    which can change between requests. The primary key breaks ties between
    candies that share a name, since names are not unique.
    """
    candies = Candy.objects.published().order_by("name", "pk")
    return render(request, "shop/candy_list.html", {"candies": candies})


def candy_detail(request, pk):
    """UC-03: one candy's full detail.

    Extension 2a: an unpublished or deleted item shows "no longer available"
    and a way back to the catalog. Both answer 404 -- the page is not there for
    this customer either way -- and they share one response, so the page does
    not reveal whether an unpublished item exists.
    """
    candy = Candy.objects.published().filter(pk=pk).first()
    if candy is None:
        return render(request, "shop/candy_unavailable.html", status=404)
    return render(request, "shop/candy_detail.html", {"candy": candy})


@require_POST
def add_to_shoppingcart(request, pk):
    """UC-04 steps 1-3: add one, within stock, and show the result in place.

    Always answers 200 with the button partial, which htmx swaps in -- a
    refusal too, because htmx does not swap 4xx responses and the customer
    would see nothing happen (UC-04 ext. 2a requires saying so). That includes
    a candy unpublished or deleted since the page was loaded.
    """
    candy = Candy.objects.published().filter(pk=pk).first()
    if candy is None:
        added, message = False, "This candy is no longer available."
    else:
        added, message = cart.add_one(request, candy)
    return render(
        request,
        "shop/partials/cart_button.html",
        {"candy": candy, "added": added, "message": message},
    )


def shoppingcart(request):
    """UC-04 step 5: review every item, its quantity and the total."""
    return render(request, "shop/shoppingcart.html", _cart_context(request))


@require_POST
def update_shoppingcart(request, pk):
    """UC-04 step 4: change a quantity, validated against stock."""
    candy = Candy.objects.published().filter(pk=pk).first()
    if candy is None:
        # cart.lines() drops the entry and says so; a second notice here would
        # tell the customer the same thing twice.
        return _cart_response(request, "")
    form = QuantityForm(request.POST)
    if not form.is_valid():
        return _cart_response(request, form.first_error())
    return _cart_response(request, cart.set_quantity(request, candy, form.cleaned_data["quantity"]))


@require_POST
def remove_from_shoppingcart(request, pk):
    """UC-04 step 4: take an item out; ext. 4a is the empty state that follows.

    The pressed Remove button disappears with its line, so keyboard focus is
    handed on: to the line that moved into its place (or the new last line), or
    to "Browse the candy" once the cart is empty. Lines are sorted by name, so
    the removed candy's name locates that place -- looked up without the
    published filter, so a candy unpublished while the page was open still has
    one.
    """
    cart.remove(request, pk)
    removed_name = Candy.objects.filter(pk=pk).values_list("name", flat=True).first()
    return _cart_response(request, "", removed_name=removed_name, removed=True)


def _cart_context(request, notices=(), removed_name=None):
    """The cart for a template. Calls cart.lines() once: it reports each change
    it makes to a stale cart only once, so a second call would lose the notices.

    After a removal, focus goes to the first remaining line whose name sorts at
    or after the removed one -- the line now in its place -- else the last line.
    A candy deleted while the page was open has no name to look up, so focus
    goes to the last line.
    """
    lines, total, cart_notices = cart.lines(request)
    focus = None
    if lines:
        later = [line for line in lines if removed_name is not None and line.candy.name >= removed_name]
        focus = (later[0] if later else lines[-1]).candy.pk
    return {
        "lines": lines,
        "total": total,
        "cart_notices": [*notices, *cart_notices],
        "focus": focus,
    }


def _cart_response(request, notice, removed_name=None, removed=False):
    """htmx gets the cart partial back; a plain form post is redirected.

    The redirect keeps the page working without JavaScript and keeps a reload
    from re-submitting the change; the notice rides across it in messages.
    """
    notices = [notice] if notice else []
    if request.headers.get("HX-Request") == "true":
        context = _cart_context(request, notices, removed_name)
        context.update(oob=True, removed=removed)
        return render(request, "shop/partials/shoppingcart_contents.html", context)
    for text in notices:
        messages.info(request, text)
    return redirect("shoppingcart")
