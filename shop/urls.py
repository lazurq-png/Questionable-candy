from django.urls import path
from . import views

urlpatterns = [
    path("", views.candy_list, name="candy_list"),
    path("candy/<int:pk>/add-to-shoppingcart/", views.add_to_shoppingcart, name="add_to_shoppingcart"),
]