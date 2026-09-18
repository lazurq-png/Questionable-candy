from django import forms
from django.contrib import admin

from .allergens import ALLERGENS
from .models import Candy, Order, OrderItem

FLAW_REQUIRED = "Every candy must disclose a flaw (UC-06). Describe its real downside."


class CandyAdminForm(forms.ModelForm):
    """UC-06 extension 2a: a save with no flaw is rejected with a prompt for one.

    The form field already strips whitespace and requires a value; this only
    replaces Django's generic "This field is required." with a message that says
    *why*. The database constraint behind it (candy_flaw_is_not_blank) still
    rejects a blank flaw from any path that skips this form.
    """

    # A checkbox per allergen rather than ArrayField's default comma-separated
    # text box, which would accept any spelling. The model's choices still
    # reject an unknown key from any path that skips this form.
    allergens = forms.MultipleChoiceField(
        choices=ALLERGENS, widget=forms.CheckboxSelectMultiple, required=False,
        help_text="The EU's 14 major allergens. Tick every one the candy contains.",
    )

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
    fields = (
        "name", "slug", "flaw", "description", "flavor", "price", "stock", "sugar_content_g", "allergens",
        "is_published", "image",
        "created_at", "updated_at",
    )
    readonly_fields = ("created_at", "updated_at")
    # Typed name, slug follows, on the add form only: prepopulated_fields
    # applies to fields that are editable, and the slug stops being editable
    # once the candy exists (get_readonly_fields).
    prepopulated_fields = {"slug": ("name",)}

    def get_prepopulated_fields(self, request, obj=None):
        """Nothing to prepopulate on an existing candy: its slug is read-only,
        and the admin looks the field up on the form, which no longer has it.
        """
        if obj is None:
            return self.prepopulated_fields
        return {}

    def get_readonly_fields(self, request, obj=None):
        """An existing candy's slug cannot be changed here.

        /candy/<pk>/ answers 301 to the slug, and a browser may cache that for
        as long as it likes. Editing the slug afterwards would leave those
        visitors pointed at an address that no longer exists, with nothing the
        server could do about it. So changing one afterwards -- a typo caught
        late, say -- is deliberately a `manage.py shell` or data-migration
        operation, taken knowing that a cached 301 cannot be recalled, rather
        than a field to retype. Renaming the candy is free; its address does
        not follow.
        """
        if obj is None:
            return self.readonly_fields
        return (*self.readonly_fields, "slug")


class OrderItemInline(admin.TabularInline):
    """An order's lines, as they were placed."""

    model = OrderItem
    fields = ("candy", "quantity", "unit_price", "subtotal")
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Orders, read-only: a placed order is a record, changed by checkout alone.

    Nothing here can create, edit or delete one; payment and fulfilment, which
    would change its status, are not built.
    """

    list_display = ("__str__", "user", "status", "total_amount", "created_at")
    list_filter = ("status",)
    fields = (
        "user", "status", "total_amount", "warning_acknowledged_at", "purchase_confirmed_at",
        "created_at", "paid_at",
    )
    readonly_fields = fields
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
