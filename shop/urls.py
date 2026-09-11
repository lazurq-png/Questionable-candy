from django.urls import path
from . import views

urlpatterns = [
    path("", views.candy_list, name="candy_list"),
    path("candy/<int:pk>/add-to-cart/", views.add_to_cart, name="add_to_cart"),
]