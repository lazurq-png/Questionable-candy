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
    """The signed-in customer's name, e-mail and allergies."""

    allergies = allergies_field("Allergies")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "allergies")
