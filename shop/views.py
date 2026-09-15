from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import CandyProduct


def candy_list(request):
    candies = CandyProduct.objects.all()
    return render(request, "shop/candy_list.html", {"candies": candies})


@require_POST
def add_to_shoppingcart(request, pk):
    candy = get_object_or_404(CandyProduct, pk=pk)
    shoppingcart = request.session.setdefault("shoppingcart", {})
    shoppingcart[str(pk)] = shoppingcart.get(str(pk), 0) + 1
    request.session.modified = True
    return render(request, "shop/partials/cart_button.html", {"candy": candy})
