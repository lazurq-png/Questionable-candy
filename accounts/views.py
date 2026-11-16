"""Signing up, editing the customer's information, and deleting the account.

Logging in and out are Django's own LoginView and LogoutView (accounts/urls.py);
logout accepts POST only, so a link or a prefetch cannot sign anyone out.
"""

from axes.models import AccessAttempt, AccessLog
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import RedirectURLMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import FormView

from shop.models import Order

from .forms import DeleteAccountForm, ProfileForm, SignUpForm
from .signup_limit import claim_sign_up


@method_decorator([sensitive_post_parameters("password1", "password2"), csrf_protect, never_cache], name="dispatch")
class SignUpView(RedirectURLMixin, FormView):
    """Create an account and sign straight in, then go back where the customer was.

    RedirectURLMixin is the same `next` handling LoginView uses: a `next` that
    points at another site is ignored in favour of LOGIN_REDIRECT_URL. The
    decorators are LoginView's too: the passwords are masked in any error
    report, and the form is never served from a cache.

    One address may make settings.SIGNUP_MAX_PER_DAY accounts a day
    (signup_limit.py). Only a form that would have made an account is counted,
    so mistyping a password costs nothing; past the limit the answer is 429,
    as a locked-out login's is, and no account is made.
    """

    template_name = "accounts/signup.html"
    form_class = SignUpForm
    next_page = settings.LOGIN_REDIRECT_URL

    def form_valid(self, form):
        if not claim_sign_up(self.request):
            form.add_error(None, "Too many accounts were created from here today. Try again tomorrow.")
            response = self.form_invalid(form)
            response.status_code = 429
            return response
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.redirect_field_name] = self.get_redirect_url()
        return context


@never_cache
@login_required
def profile(request):
    """The signed-in customer changes their details and allergies.

    The form is bound to request.user and the URL carries no id, so there is no
    way to name somebody else's record.
    """
    form = ProfileForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile was saved.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@never_cache
@login_required
def orders(request):
    """The signed-in customer's own orders, newest first.

    Read from request.user, like profile(): the URL carries no id to swap.
    """
    customer_orders = request.user.orders.order_by("-created_at")
    return render(request, "accounts/orders.html", {"orders": customer_orders})


class PasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    """Django's own password change, returning to the profile with a message."""

    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your password was changed."


@sensitive_post_parameters("password")
@never_cache
@login_required
def delete_account(request):
    """The signed-in customer deletes their account, their orders with it.

    Like profile(), the URL carries no id: the account deleted is the session's.
    The password is asked for again, so an unattended, signed-in browser is not
    enough. Orders go first, through the same path the admin uses, so any that
    were never sent return their candy to stock; then the session ends and the
    account is deleted, with the log-in records django-axes kept under its
    username. All of it or none.

    Staff accounts are refused: one deleting itself here could leave the shop
    with nobody able to sign in to the admin, which is where they are removed.
    """
    if request.user.is_staff:
        messages.info(request, "Staff accounts are removed in the admin, not here.")
        return redirect("accounts:profile")
    form = DeleteAccountForm(request.user, request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = request.user
        with transaction.atomic():
            Order.objects.delete_and_restock(user.orders.all())
            logout(request)
            # django-axes keys its log-in records on the username text, not on
            # a foreign key, so deleting the user would leave them behind.
            AccessLog.objects.filter(username=user.get_username()).delete()
            AccessAttempt.objects.filter(username=user.get_username()).delete()
            user.delete()
        return redirect("accounts:deleted")
    return render(request, "accounts/delete_account.html", {"form": form, "orders": request.user.orders.count()})
