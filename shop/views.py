from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import CandyProduct

def candy_list(request):
    candies = CandyProduct.objects.all()
    return render(request, "shop/candy_list.html", {"candies": candies})

def add_to_cart(request, pk):
    candy = get_object_or_404(CandyProduct, pk=pk)
    cart = request.session.setdefault("cart", {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session.modified = True
    return render(request, "shop/partials/cart_button.html", {"candy": candy})