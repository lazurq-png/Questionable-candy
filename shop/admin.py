import uuid
from collections import Counter

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .allergens import ALLERGENS
from .models import Candy, Order, OrderItem, move_stock

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


class OrderItemFormSet(BaseInlineFormSet):
    """Refuses lines that would take more stock than there is."""

    def clean(self):
        super().clean()
        if any(self.errors) or self.instance.status == Order.Status.FULFILLED:
            return
        wanted = Counter()
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                wanted[form.cleaned_data["candy"].pk] += form.cleaned_data["quantity"]
        taken = self.instance.line_counts() if self.instance.pk else Counter()
        short = [candy.name for candy in Candy.objects.filter(pk__in=wanted)
                 if wanted[candy.pk] - taken[candy.pk] > candy.stock]
        if short:
            raise ValidationError(f"Not enough stock: {', '.join(short)}.")


class CandyDetailsWidget(forms.Widget):
    """A saved order line's candy: its "2 x <candy>" title, whose name opens the
    candy's details in a dialog. It shows the quantity as saved.
    """

    template_name = "shop/admin/candy_details_widget.html"

    def __init__(self, line, attrs=None):
        super().__init__(attrs)
        self.line = line

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["line"] = self.line
        context["candy"] = self.line.candy
        return context


class OrderItemForm(forms.ModelForm):
    """An order line whose unit price, left blank, is the candy's current price.

    Only a new line offers the candy dropdown. An existing line's candy is fixed,
    shown as its "2 x <candy>" title, whose name opens its details. To change
    it, remove the line and add another.
    """

    class Meta:
        model = OrderItem
        fields = ("candy", "quantity", "unit_price")
        help_texts = {"unit_price": "Leave blank for the candy's current price."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit_price"].required = False
        if self.instance.pk:
            # Disabled, so the line keeps its candy whatever is posted.
            self.fields["candy"].disabled = True
            self.fields["candy"].widget = CandyDetailsWidget(self.instance)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("unit_price") is None and cleaned_data.get("candy"):
            cleaned_data["unit_price"] = cleaned_data["candy"].price
        return cleaned_data


class OrderItemInline(admin.TabularInline):
    """An order's lines. Stock follows them: see OrderAdmin.save_formset."""

    model = OrderItem
    # Django's tabular template with each line's cells centred on one axis,
    # the "2 x <candy>" title among them.
    template = "shop/admin/order_item_tabular.html"
    form = OrderItemForm
    formset = OrderItemFormSet
    fields = ("candy", "quantity", "unit_price", "subtotal")
    readonly_fields = ("subtotal",)
    # No empty row to start with: "Add another Order item" opens a dialog to
    # choose the candy and quantity (order_item_tabular.html).
    extra = 0

    @property
    def media(self):
        """order_lines.js in place of Django's inline script (admin/js/inlines.js).

        inlines.js adds and removes unsaved rows in the page. Here there are
        none to manage: the add dialog sends its line with a save of its own,
        so nothing is added in the page and nothing needs its "Add another"
        row or remove buttons.
        """
        return forms.Media(js=["shop/admin/order_lines.js"])

    def get_queryset(self, request):
        # Each existing line shows its candy's details.
        return super().get_queryset(request).select_related("candy")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """A new line's candy is picked from a list, with no add, change, view or delete
        icons beside it: editing a candy belongs on the candy's own page, not
        halfway through an order.
        """
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "candy":
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_view_related = False
            formfield.widget.can_delete_related = False
        return formfield


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Orders, which an administrator can add, edit and delete.

    Stock follows the lines of any order that is not fulfilled (not yet sent):
    adding or raising a line takes stock, and removing or lowering one --
    or deleting the whole order -- returns it. A fulfilled order's stock has
    left the shop, so changing or deleting it moves none. Payment and
    fulfilment, which would change an order's status on their own, are not
    built.
    """

    list_display = ("__str__", "user", "status", "total_amount", "created_at")
    # Each order's name is its customer's username (Order.__str__).
    list_select_related = ("user",)
    list_filter = ("status",)
    fields = (
        "user", "status", "total_amount", "warning_acknowledged_at", "purchase_confirmed_at",
        "created_at", "paid_at",
    )
    readonly_fields = ("total_amount", "created_at")
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        if not change:
            # Both are NOT NULL and not on the form; the lines set the real total.
            obj.confirmation_token = uuid.uuid4()
            obj.total_amount = 0
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Save the lines, then recompute the total and move stock by the difference.

        A new line for a candy the order already has a line for adds its
        quantity to that line, at that line's unit price, rather than becoming
        a second line; two new lines for one candy become one line the same way.

        The admin runs this inside the same transaction as the order's save.
        """
        order = form.instance
        before = order.line_counts()
        items = formset.save(commit=False)
        for item in formset.deleted_objects:
            item.delete()
        # One line per candy: the order's remaining lines, as edited on this form.
        lines = {line.candy_id: line for line in order.items.all()}
        lines.update((item.candy_id, item) for item in items if item.pk)
        for item in items:
            if item.pk is None:
                if item.candy_id in lines:
                    lines[item.candy_id].quantity += item.quantity
                else:
                    lines[item.candy_id] = item
        for line in lines.values():
            line.subtotal = line.quantity * line.unit_price
            line.save()
        order.total_amount = sum(item.subtotal for item in order.items.all())
        order.save(update_fields=["total_amount"])
        if order.status != Order.Status.FULFILLED:
            after = order.line_counts()
            move_stock({pk: after[pk] - before[pk] for pk in before | after})

    def delete_model(self, request, obj):
        Order.objects.delete_and_restock([obj])

    def delete_queryset(self, request, queryset):
        """The changelist's "Delete selected orders" action, which would
        otherwise bulk-delete without returning any stock.
        """
        Order.objects.delete_and_restock(queryset)
