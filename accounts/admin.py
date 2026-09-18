from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as StockUserAdmin
from django.contrib.auth.forms import UserChangeForm

from shop.allergens import ALLERGENS

from .models import User


class UserAdminChangeForm(UserChangeForm):
    """The stock change form, with allergies as one checkbox per allergen.

    ArrayField's default widget is a comma-separated text box, which would take
    any spelling; the model's choices would then reject it with a message about
    a list index.
    """

    allergies = forms.MultipleChoiceField(
        choices=ALLERGENS, widget=forms.CheckboxSelectMultiple, required=False
    )

    class Meta(UserChangeForm.Meta):
        model = User


@admin.register(User)
class UserAdmin(StockUserAdmin):
    form = UserAdminChangeForm
    # The stock fieldsets list only the stock fields, so without this the
    # admin would silently offer no way to see or edit allergies.
    fieldsets = StockUserAdmin.fieldsets + (("Allergies", {"fields": ("allergies",)}),)
