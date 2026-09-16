from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Candy


def candy_list(request):
    candies = Candy.objects.published()
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
    candy = get_object_or_404(Candy.objects.published(), pk=pk)
    shoppingcart = request.session.setdefault("shoppingcart", {})
    shoppingcart[str(pk)] = shoppingcart.get(str(pk), 0) + 1
    request.session.modified = True
    return render(request, "shop/partials/cart_button.html", {"candy": candy})
