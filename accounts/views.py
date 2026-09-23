"""Signing up and the customer's own allergies.

Logging in and out are Django's own LoginView and LogoutView (accounts/urls.py);
logout accepts POST only, so a link or a prefetch cannot sign anyone out.
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import RedirectURLMixin
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import FormView

from .forms import AllergiesForm, SignUpForm


@method_decorator([sensitive_post_parameters("password1", "password2"), csrf_protect, never_cache], name="dispatch")
class SignUpView(RedirectURLMixin, FormView):
    """Create an account and sign straight in, then go back where the customer was.

    RedirectURLMixin is the same `next` handling LoginView uses: a `next` that
    points at another site is ignored in favour of LOGIN_REDIRECT_URL. The
    decorators are LoginView's too: the passwords are masked in any error
    report, and the form is never served from a cache.
    """

    template_name = "accounts/signup.html"
    form_class = SignUpForm
    next_page = settings.LOGIN_REDIRECT_URL

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.redirect_field_name] = self.get_redirect_url()
        return context


@never_cache
@login_required
def my_allergies(request):
    """The signed-in customer changes their own allergies.

    The form is bound to request.user and the URL carries no id, so there is no
    way to name somebody else's record.
    """
    form = AllergiesForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your allergies are saved.")
        return redirect("accounts:my_allergies")
    return render(request, "accounts/my_allergies.html", {"form": form})

@never_cache
@login_required
def my_profile(request):
    """The signed-in customer changes their own allergies.

    The form is bound to request.user and the URL carries no id, so there is no
    way to name somebody else's record.
    """
    form = AllergiesForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your allergies are saved.")
        return redirect("accounts:my_allergies")
    return render(request, "accounts/my_allergies.html", {"form": form})
