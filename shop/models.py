from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

from . import allergens


class CandyQuerySet(models.QuerySet):
    """Query helpers, so every view shares one definition of available."""

    def published(self):
        """The candy a customer may see or buy (UC-01 step 2, UC-03 ext. 2a)."""
        return self.filter(is_published=True)


class Candy(models.Model):
    name = models.CharField(max_length=200)
    # UC-03 step 2 renders this on the detail page. Not null (docs/data-model.md
    # section 3.3) but not mandatory: UC-06 singles out `flaw` as the field that
    # may never be omitted, and holding description to that bar is a tightening
    # nobody has asked for. default="" so the migration needs no answer about
    # existing rows.
    description = models.TextField(blank=True, default="")
    flavor = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    flaw = models.CharField(max_length=200)
    # docs/data-model.md section 3.3. Default True so rows that existed before
    # the field keep appearing in the catalog; hiding them is a per-row decision.
    is_published = models.BooleanField(default=True)
    # A path under static/, e.g. "shop/candy/sour-bricks.svg" -- not an upload.
    # Media storage is undecided (docs/adr/0004-database.md), so images ship as
    # static files and this names one. Blank means the placeholder is shown.
    image = models.CharField(max_length=200, blank=True, default="")
    # docs/data-model.md section 3.3; the UC-07 health warning reads both.
    # Grams of sugar per 100 g of candy. Null means unknown, which is not zero:
    # the warning names a candy with unknown sugar rather than counting it as
    # sugar-free. The database holds it to 0-100 as well (Meta.constraints).
    sugar_content_g = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Grams of sugar per 100 g. Leave empty if unknown.",
    )
    # Keys from shop.allergens, the EU's 14 major allergens. The choices are
    # checked by full_clean() and forms, not by the database.
    allergens = ArrayField(
        models.CharField(max_length=allergens.KEY_LENGTH, choices=allergens.ALLERGENS),
        blank=True, default=list,
    )
    # docs/data-model.md section 3.3. Rows that existed before migration 0007
    # hold the time that migration ran, not when they were really created:
    # Django's schema editor fills auto_now/auto_now_add columns with "now" for
    # existing rows, even when the column is nullable
    # (docs/ai/night-2026-09-16/decisions.md D9).
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CandyQuerySet.as_manager()

    class Meta:
        # Django would otherwise pluralise the class name to "candys".
        verbose_name_plural = "candies"
        constraints = [
            # UC-06's Constraint: "Required at the data-model level, not only in
            # the form, so it can never be silently omitted."
            #
            # NOT NULL alone does not deliver that -- it is satisfied by the
            # empty string, and Candy.objects.create(flaw="") bypasses
            # form validation entirely. This closes the gap docs/data-model.md
            # section 3.3 records as still open.
            #
            # Matched on \S rather than != "" so that a flaw of "   " is
            # rejected too. That is not extra strictness: Django's form field
            # strips whitespace before checking blank, so the form already
            # rejects it, and the constraint would otherwise be the more
            # permissive of the two.
            models.CheckConstraint(
                condition=models.Q(flaw__regex=r"\S"),
                name="candy_flaw_is_not_blank",
                violation_error_message="Every candy must disclose a flaw (UC-06).",
            ),
            models.CheckConstraint(
                condition=models.Q(sugar_content_g__isnull=True)
                | models.Q(sugar_content_g__gte=0, sugar_content_g__lte=100),
                name="candy_sugar_per_100g_in_range",
                violation_error_message="Sugar per 100 g must be between 0 and 100.",
            ),
        ]

    def __str__(self):
        return self.name

    def allergen_names(self):
        """The allergens' labels, in the vocabulary's order, for display."""
        return allergens.names(self.allergens)


class OrderChanged(Exception):
    """Placing an order found the shop no longer matches what was confirmed.

    `candies` names each affected candy, for the customer (UC-05 ext. 4a).
    """

    def __init__(self, candies):
        super().__init__(", ".join(candies))
        self.candies = candies


class OrderManager(models.Manager):
    """Orders are created only through place(), never by hand."""

    def place(self, user, snapshot, warning_acknowledged_at, purchase_confirmed_at, confirmation_token):
        """UC-05 steps 4 and 7: re-validate the confirmed order, then record it.

        `snapshot` is what the customer confirmed (shop.checkout.order_snapshot):
        each line's candy primary key, quantity and unit price, and the total.

        In one transaction, the candies are locked (SELECT ... FOR UPDATE, in
        primary-key order so two orders cannot deadlock) and each line checked
        again: still published, enough stock, the same price. If anything
        differs, OrderChanged is raised and nothing is written. Otherwise the
        order is created as pending -- payment is not connected -- with each
        line's price as it was confirmed, and stock is reduced while the lock is
        held, so two customers cannot both buy the last bag.

        `confirmation_token` identifies the confirmation page that was submitted.
        The same page submitted twice -- a double-click, whose two requests both
        still see the full cart -- must place one order, not two: once the locks
        are held, an order already placed with this token is returned instead,
        before any check that its own stock reduction would now fail.
        """
        lines = [(pk, quantity, Decimal(price)) for pk, quantity, price in snapshot["lines"]]
        total = Decimal(snapshot["total"])
        if not lines or sum(price * quantity for _, quantity, price in lines) != total:
            raise ValueError("A confirmed order must have lines that add up to its total.")

        with transaction.atomic():
            candies = {
                candy.pk: candy
                for candy in Candy.objects.select_for_update().filter(pk__in=[pk for pk, _, _ in lines]).order_by("pk")
            }
            order = self.filter(user=user, confirmation_token=confirmation_token).first()
            if order is not None:
                return order  # this confirmation page was placed already

            changed = []
            for pk, quantity, price in lines:
                candy = candies.get(pk)
                if candy is None:
                    changed.append("a candy that is no longer sold")
                elif not candy.is_published or candy.stock < quantity or candy.price != price:
                    changed.append(candy.name)
            if changed:
                raise OrderChanged(changed)

            order = self.create(
                user=user,
                total_amount=total,
                warning_acknowledged_at=warning_acknowledged_at,
                purchase_confirmed_at=purchase_confirmed_at,
                confirmation_token=confirmation_token,
            )
            OrderItem.objects.bulk_create(
                OrderItem(order=order, candy=candies[pk], quantity=quantity, unit_price=price,
                          subtotal=price * quantity)
                for pk, quantity, price in lines
            )
            for pk, quantity, _ in lines:
                candy = candies[pk]
                candy.stock -= quantity
                candy.save(update_fields=["stock", "updated_at"])
        return order


class Order(models.Model):
    """A customer's order (docs/data-model.md section 3.6).

    Only `pending` is ever set today: payment is not connected (UC-05 step 6),
    so nothing is charged and no order is paid.
    """

    class Status(models.TextChoices):
        """An order's lifecycle; only PENDING is reachable today."""

        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        FULFILLED = "fulfilled", "Fulfilled"

    # PROTECT: an order is a record of what happened, so a customer with
    # orders cannot be deleted out from under them.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    warning_acknowledged_at = models.DateTimeField(null=True, blank=True)
    purchase_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    # The confirmation page this order was placed from (shop/checkout.py), so
    # submitting that page twice cannot place it twice. Unique in the database
    # as well as checked in place() (docs/data-model.md section 3 status table).
    confirmation_token = models.UUIDField(unique=True, editable=False)

    objects = OrderManager()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(total_amount__gte=0), name="order_total_not_negative"),
        ]

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    """One candy in an order, at the price it was confirmed at (section 3.7)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # PROTECT: a candy that has been ordered stays, so the order can still say
    # what was bought. Withdrawing it from sale is is_published's job.
    candy = models.ForeignKey(Candy, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name="orderitem_quantity_at_least_one"),
            models.CheckConstraint(
                condition=models.Q(subtotal=models.F("quantity") * models.F("unit_price")),
                name="orderitem_subtotal_is_quantity_times_price",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.candy}"
