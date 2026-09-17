"""Validation of what a customer submits (docs/adr/0003-backend.md)."""
from decimal import Decimal, InvalidOperation

from django import forms


class QuantityForm(forms.Form):
    """A cart line's new quantity: a whole number of at least 1 (UC-04 step 4).

    Stock is not checked here -- that rule belongs to the cart, which caps
    rather than rejects (shop/cart.py).
    """

    quantity = forms.IntegerField(
        min_value=1,
        error_messages={
            "required": "Enter a whole number.",
            "invalid": "Enter a whole number.",
            "min_value": "Quantity must be at least 1. Use Remove to take it out of the cart.",
        },
    )

    def first_error(self):
        """The one message to show the customer."""
        return next(iter(self.errors.get("quantity", [])), "")


class StepperQuantityForm(QuantityForm):
    """A number typed into a candy's add-to-cart stepper and confirmed with Ok.

    Unlike a cart line's, 0 is allowed: the stepper is how a candy gets into the
    cart and out of it, so 0 takes it out rather than being refused.

    Its messages are shorter than a cart line's because they are shown in a
    small bubble against the stepper, not as a notice above the cart.
    """

    quantity = forms.IntegerField(
        min_value=0,
        error_messages={
            "required": "Enter a number",
            "invalid": "Enter a number",
            "min_value": "Cannot be below 0",
        },
    )


class HealthWarningForm(forms.Form):
    """UC-07 step 3: the customer acknowledges the warning -- deliberately.

    A checkbox as well as the button, so a stray press of Continue is not an
    acknowledgment. `fingerprint` names the warning that was on the page; the
    view compares it with the warning as it stands now (shop/checkout.py).
    """

    acknowledge = forms.BooleanField(
        label="I have read this health warning",
        error_messages={"required": "Tick the box to confirm you have read the health warning."},
    )
    fingerprint = forms.CharField(widget=forms.HiddenInput)


class ConfirmOrderForm(forms.Form):
    """UC-08: three distinct, deliberate confirmations, all checked here.

    1. a checkbox, worded with the order's item count and total;
    2. the total typed back, which must equal the total shown;
    3. the Place my order button itself, which submits `place_order`.

    The page unlocks them one after another with Alpine, but nothing depends
    on that: without JavaScript all three are there, and each is still
    required. `total` is the total the page showed.
    """

    checked_order = forms.BooleanField(
        error_messages={"required": "Tick the box to confirm you have checked your order."},
    )
    typed_total = forms.CharField(
        error_messages={"required": "Type the total to confirm the amount."},
    )
    place_order = forms.CharField(
        error_messages={"required": "Press Place my order to place it."},
    )

    def __init__(self, *args, total, **kwargs):
        super().__init__(*args, **kwargs)
        self.total = total

    def clean_typed_total(self):
        """Equal to the total shown, allowing a leading $ and a decimal comma."""
        typed = self.cleaned_data["typed_total"].strip().removeprefix("$").strip().replace(",", ".")
        try:
            amount = Decimal(typed)
        except InvalidOperation:
            amount = None
        if amount is None or not amount.is_finite() or amount != self.total:
            raise forms.ValidationError(f"That is not the total. Type {self.total} to confirm.")
        return amount

    def clean_place_order(self):
        """Only the Place my order button sends this value."""
        if self.cleaned_data["place_order"] != "yes":
            raise forms.ValidationError("Press Place my order to place it.")
        return True
