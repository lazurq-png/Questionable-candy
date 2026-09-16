from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Candy


def candy_list(request):
    candies = Candy.objects.all()
    return render(request, "shop/candy_list.html", {"candies": candies})


def candy_detail(request, pk):
    """UC-03: one candy's full detail.

    Extension 2a asks for "no longer available" on a deleted item; a 404 is
    what this gives instead, and publication state is not modelled at all --
    see docs/ai/night-2026-09-15/questions.md Q2.
    """
    candy = get_object_or_404(Candy, pk=pk)
    return render(request, "shop/candy_detail.html", {"candy": candy})


@require_POST
def add_to_shoppingcart(request, pk):
    candy = get_object_or_404(Candy, pk=pk)
    shoppingcart = request.session.setdefault("shoppingcart", {})
    shoppingcart[str(pk)] = shoppingcart.get(str(pk), 0) + 1
    request.session.modified = True
    return render(request, "shop/partials/cart_button.html", {"candy": candy})
