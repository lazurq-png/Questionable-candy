"""Validation of what a customer submits (docs/adr/0003-backend.md)."""
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
