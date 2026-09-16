from django import forms
from django.contrib import admin

from .models import Candy

FLAW_REQUIRED = "Every candy must disclose a flaw (UC-06). Describe its real downside."


class CandyAdminForm(forms.ModelForm):
    """UC-06 extension 2a: a save with no flaw is rejected with a prompt for one.

    The form field already strips whitespace and requires a value; this only
    replaces Django's generic "This field is required." with a message that says
    *why*. The database constraint behind it (candy_flaw_is_not_blank) still
    rejects a blank flaw from any path that skips this form.
    """

    class Meta:
        model = Candy
        fields = "__all__"
        error_messages = {"flaw": {"required": FLAW_REQUIRED}}
        help_texts = {"flaw": "Required. A specific, honest downside, shown on the candy's page."}


@admin.register(Candy)
class CandyAdmin(admin.ModelAdmin):
    """The Site Administrator's side of UC-06: record a flaw when creating or editing."""

    form = CandyAdminForm
    list_display = ("name", "price", "stock", "is_published")
    list_filter = ("is_published",)
    search_fields = ("name", "flaw")
    fields = ("name", "flaw", "description", "flavor", "price", "stock", "is_published", "image")
