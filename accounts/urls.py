"""Account URLs, under /accounts/ (mysite/urls.py)."""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

# The namespace also tells the header (accounts/partials/account_nav.html) not
# to send a customer back to an account page after logging in.
app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("profile/", views.profile, name="profile"),
    path("orders/", views.orders, name="orders"),
    path("password/", views.PasswordChangeView.as_view(), name="password_change"),
]
