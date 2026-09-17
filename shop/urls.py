from django.urls import path
from . import views

urlpatterns = [
    path("", views.candy_list, name="candy_list"),
    path("candy/<int:pk>/", views.candy_detail, name="candy_detail"),
    path("candy/<int:pk>/add-to-shoppingcart/", views.add_to_shoppingcart, name="add_to_shoppingcart"),
    path("candy/<int:pk>/set-in-shoppingcart/", views.set_in_shoppingcart, name="set_in_shoppingcart"),
    path(
        "candy/<int:pk>/remove-one-from-shoppingcart/",
        views.remove_one_from_shoppingcart,
        name="remove_one_from_shoppingcart",
    ),
    path("shoppingcart/", views.shoppingcart, name="shoppingcart"),
    path("shoppingcart/panel/", views.shoppingcart_panel, name="shoppingcart_panel"),
    path("shoppingcart/<int:pk>/update/", views.update_shoppingcart, name="update_shoppingcart"),
    path("shoppingcart/<int:pk>/remove/", views.remove_from_shoppingcart, name="remove_from_shoppingcart"),
    path("checkout/", views.checkout, name="checkout"),
]
