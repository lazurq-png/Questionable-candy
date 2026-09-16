from django.urls import path
from . import views

urlpatterns = [
    path("", views.candy_list, name="candy_list"),
    path("candy/<int:pk>/", views.candy_detail, name="candy_detail"),
    path("candy/<int:pk>/add-to-shoppingcart/", views.add_to_shoppingcart, name="add_to_shoppingcart"),
    path("shoppingcart/", views.shoppingcart, name="shoppingcart"),
    path("shoppingcart/<int:pk>/update/", views.update_shoppingcart, name="update_shoppingcart"),
    path("shoppingcart/<int:pk>/remove/", views.remove_from_shoppingcart, name="remove_from_shoppingcart"),
]
