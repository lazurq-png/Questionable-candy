"""Validation of what a customer submits about their own account."""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from shop.allergens import ALLERGENS

from .models import User

ALLERGIES_HELP = "Tick any you have, so checkout can warn you. You can change them later."


def allergies_field(label):
    """One checkbox per allergen in the shared vocabulary, none required."""
    return forms.MultipleChoiceField(
        label=label,
        choices=ALLERGENS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text=ALLERGIES_HELP,
    )


class SignUpForm(UserCreationForm):
    """A username, a password twice, and optionally the customer's allergies.

    UserCreationForm brings the password validators in settings and rejects a
    username that differs from an existing one only in case.
    """

    allergies = allergies_field("Allergies (optional)")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "allergies")


class ProfileForm(forms.ModelForm):
    """The signed-in customer's name, e-mail and allergies.

    The name and e-mail boxes start empty, with what is saved shown as a grey
    hint (a placeholder). An empty box means "keep it": only text the customer
    types replaces a saved value. The cost is that these fields cannot be
    cleared from this page.
    """

    # Field -> hint shown while nothing is saved for it.
    KEEP_IF_EMPTY = {"first_name": None, "last_name": "Your last name", "email": "name@example.com"}

    allergies = allergies_field("Allergies")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "allergies")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, fallback in self.KEEP_IF_EMPTY.items():
            saved = getattr(self.instance, name)
            # first_name falls back to the username.
            hint = saved or fallback or self.instance.get_username()
            self.fields[name].widget.attrs["placeholder"] = hint
            self.initial[name] = ""

    def clean(self):
        cleaned = super().clean()
        # self.instance still holds the saved values here: the form copies the
        # cleaned data onto it only after clean() returns.
        for name in self.KEEP_IF_EMPTY:
            if name in cleaned and not cleaned[name]:
                cleaned[name] = getattr(self.instance, name)
        return cleaned
