from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_POST

from . import cart
from .forms import QuantityForm, StepperQuantityForm
from .models import Candy

# Sent as HX-Trigger on every response that changed the cart. The header's cart
# dropdown listens for it and reloads while it is open, and the cart and
# checkout pages reload when the change came from the detail popup
# (templates/base.html, shop/templates/shop/shoppingcart.html).
CART_CHANGED = "shoppingcart-changed"

# The id of the element in base.html that a candy's detail popup is loaded into.
DETAIL_POPUP = "candy-popup-contents"


def candy_list(request):
    """UC-01: the published candy, alphabetically.

    Without an ORDER BY, PostgreSQL returns rows in whatever order is cheapest,
    which can change between requests. The primary key breaks ties between
    candies that share a name, since names are not unique.
    """
    candies = list(Candy.objects.published().order_by("name", "pk"))
    _mark_in_cart(request, candies)
    return render(request, "shop/candy_list.html", {"candies": candies})


def candy_detail(request, pk):
    """UC-03: one candy's full detail -- as a page, or inside the detail popup.

    A candy's name link opens the popup (templates/base.html) by fetching this
    URL with htmx; its own request says so through HX-Target, and gets just
    the popup's contents. Anything else -- no JavaScript, a shared link, a
    reload -- gets the page. Vary keeps a cache from handing one to the other.

    Extension 2a: an unpublished or deleted item shows "no longer available".
    The page answers 404 -- it is not there for this customer either way -- and
    shares one response for both, so it does not reveal whether an unpublished
    item exists. The popup says the same with 200, because htmx does not swap
    4xx responses and the popup would never open.
    """
    candy = Candy.objects.published().filter(pk=pk).first()
    if candy is not None:
        _mark_in_cart(request, [candy])
    if request.headers.get("HX-Target") == DETAIL_POPUP:
        response = render(request, "shop/partials/candy_popup.html", {"candy": candy})
    elif candy is None:
        response = render(request, "shop/candy_unavailable.html", status=404)
    else:
        response = render(request, "shop/candy_detail.html", {"candy": candy})
    patch_vary_headers(response, ["HX-Target"])
    return response


@require_POST
def add_to_shoppingcart(request, pk):
    """UC-04 steps 1-3: add one, within stock, and show the result in place.

    Always answers 200 with the stepper partial, which htmx swaps in -- a
    refusal too, because htmx does not swap 4xx responses and the customer
    would see nothing happen (UC-04 ext. 2a requires saying so). That includes
    a candy unpublished or deleted since the page was loaded.
    """
    candy = Candy.objects.published().filter(pk=pk).first()
    if candy is None:
        added, message = False, "This candy is no longer available."
    else:
        added, message = cart.add_one(request, candy)
    announcement = f"Added {candy.name} to your cart." if added else message
    context = {"pk": pk, "candy": candy, "message": message, "announcement": announcement}
    return _stepper_response(request, added, context)


@require_POST
def set_in_shoppingcart(request, pk):
    """UC-04 steps 1-4 from the stepper: type a number and press Ok (or Enter).

    Adds, changes or -- at 0 -- removes, within stock (cart.set_or_add). A
    number that is not a whole number of at least 0 is refused with a message
    and the cart is left alone. Answers 200 throughout, as add_to_shoppingcart
    does and for the same reason.
    """
    candy = Candy.objects.published().filter(pk=pk).first()
    form = StepperQuantityForm(request.POST)
    if candy is None:
        changed, message = False, "This candy is no longer available."
    elif not form.is_valid():
        changed, message = False, form.first_error()
    else:
        changed, message = cart.set_or_add(request, candy, form.cleaned_data["quantity"])
    if message or not changed:
        announcement = message
    else:
        announcement = f"{cart.quantities(request).get(candy.pk, 0)} of {candy.name} in your cart."
    context = {"pk": pk, "candy": candy, "message": message, "announcement": announcement}
    return _stepper_response(request, changed, context)


@require_POST
def remove_one_from_shoppingcart(request, pk):
    """UC-04 step 4 from the catalog: the stepper's minus takes one out.

    A candy unpublished or deleted since the page was loaded still leaves the
    cart -- taking something out is never refused -- but its stepper is
    replaced by the same notice an add would get.
    """
    removed = cart.remove_one(request, pk)
    candy = Candy.objects.published().filter(pk=pk).first()
    if candy is None:
        message = announcement = "This candy is no longer available."
    else:
        message, announcement = "", (f"Removed one {candy.name} from your cart." if removed else "")
    context = {"pk": pk, "candy": candy, "message": message, "announcement": announcement}
    return _stepper_response(request, removed, context)


def _stepper_response(request, changed, context):
    """Every copy of the candy's stepper, the header count and the announcement.

    All of it out of band: a candy's stepper can be on the page and in the
    detail popup at once, and both must show the new quantity. `context` holds
    `pk` as well as `candy`, because `candy` is None once it is no longer
    available; and `message` and `announcement`.
    """
    if context["candy"] is not None:
        _mark_in_cart(request, [context["candy"]])
    response = render(request, "shop/partials/cart_stepper_response.html", context)
    if changed:
        response["HX-Trigger"] = CART_CHANGED
    return response


def _mark_in_cart(request, candies):
    """Give each candy an `in_cart` quantity for its stepper to show."""
    in_cart = cart.quantities(request)
    for candy in candies:
        candy.in_cart = in_cart.get(candy.pk, 0)


def shoppingcart(request):
    """UC-04 step 5: review every item, its quantity and the total."""
    return render(request, "shop/shoppingcart.html", _cart_context(request))


def shoppingcart_panel(request):
    """The header's cart dropdown: every item, the total, and the way to checkout.

    A fragment, fetched by htmx each time the dropdown opens and again while it
    is open whenever a response announces CART_CHANGED -- never while it is
    closed, because cart.lines() reports a stale cart's changes only once, and
    a notice rendered into a hidden panel is a notice nobody reads.
    """
    return render(request, "shop/partials/shoppingcart_panel.html", _cart_context(request))


def checkout(request):
    """UC-05 step 1: the order to be placed, and where its amounts are changed.

    Every line carries the catalog's stepper, so each candy needs the quantity
    to show in it -- read after cart.lines() has reconciled the cart with the
    shop, so a capped line's stepper shows what the cart now holds.

    Only the review. The health warning, the confirmations and payment (UC-05,
    UC-07, UC-08) are not built yet, so this page offers no way to pay.
    """
    context = _cart_context(request)
    _mark_in_cart(request, [line.candy for line in context["lines"]])
    return render(request, "shop/checkout.html", context)


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
        response = render(request, "shop/partials/shoppingcart_contents.html", context)
        response["HX-Trigger"] = CART_CHANGED
        return response
    for text in notices:
        messages.info(request, text)
    return redirect("shoppingcart")
