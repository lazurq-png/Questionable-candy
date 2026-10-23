from collections import Counter
from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from . import allergens


class CandyQuerySet(models.QuerySet):
    """Query helpers, so every view shares one definition of available."""

    def published(self):
        """The candy a customer may see or buy (UC-01 step 2, UC-03 ext. 2a)."""
        return self.filter(is_published=True)


def unique_candy_slug(name, taken):
    """A slug for `name` that `taken(slug)` says is free.

    slugify(name), with "-2", "-3", ... when that is taken, since two different
    names can slugify alike ("Sour Bricks", "Sour-Bricks"). A slug of digits
    alone gets a "candy-" prefix: /candy/<digits>/ is the old number URL, so
    such a slug could never be reached. Kept free of the model so migration
    0013 can use a frozen copy of the same rules.
    """
    base = slugify(name)[:200] or "candy"
    if base.isdigit():
        base = f"candy-{base}"
    slug, suffix = base, 2
    while taken(slug):
        slug, suffix = f"{base}-{suffix}", suffix + 1
    return slug


class Candy(models.Model):
    # Unique (docs/data-model.md section 3.3): two candies of one name could not
    # be told apart in the catalog, and their slugs would need suffixes.
    name = models.CharField(max_length=200, unique=True)
    # The candy's URL, /candy/<slug>/. Set from the name when the candy is
    # first saved and never changed by renaming it, so a shared link keeps
    # working. The admin fills it in as the name is typed; left blank, save()
    # makes one.
    slug = models.SlugField(
        max_length=220, unique=True, blank=True,
        validators=[RegexValidator(r"\D", "A slug needs a letter or a dash; digits alone read as a number.")],
        help_text="The candy's web address, filled in from the name. Set once: /candy/<number>/ "
                  "redirects here permanently, and browsers cache that.",
    )
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
            # A slug of digits alone would be read as /candy/<pk>/ and could
            # never reach its candy -- and would point at another candy if that
            # primary key exists. unique_candy_slug never makes one and the
            # field's validator rejects one, but neither reaches
            # objects.create(slug="123") or queryset.update(), exactly as with
            # flaw above.
            models.CheckConstraint(
                condition=models.Q(slug__regex=r"\D"),
                name="candy_slug_is_not_all_digits",
                violation_error_message="A slug needs a letter or a dash; digits alone read as a number.",
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

    def ensure_slug(self):
        """Give the candy its slug from its name, if nobody set one."""
        if not self.slug:
            self.slug = unique_candy_slug(
                self.name, lambda slug: Candy.objects.filter(slug=slug).exclude(pk=self.pk).exists()
            )

    def clean(self):
        """Fill the slug before validation, not after.

        full_clean() checks the constraints -- including candy_slug_is_not_all_digits
        -- and a slug left blank on a form would still be blank by then, so the
        form would report a constraint the customer never touched.
        """
        self.ensure_slug()
        super().clean()

    def save(self, *args, **kwargs):
        """As clean(), for the paths that never validate: objects.create() and friends."""
        self.ensure_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """The candy's own page, by slug (UC-03)."""
        return reverse("candy_detail", args=[self.slug])

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


def move_stock(changes):
    """Take stock (positive quantity) or return it (negative), per candy pk.

    Call inside a transaction: the candies are locked, in primary-key order as
    place() locks them, so this cannot deadlock against a checkout. Stock is a
    PositiveIntegerField, so the database refuses any change that would take it
    below zero.
    """
    changes = {pk: quantity for pk, quantity in changes.items() if quantity}
    for candy in Candy.objects.select_for_update().filter(pk__in=changes).order_by("pk"):
        candy.stock -= changes[candy.pk]
        candy.save(update_fields=["stock", "updated_at"])


class OrderManager(models.Manager):
    """Customers' orders are created through place(); administrators' in the admin."""

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

    def delete_and_restock(self, orders):
        """Delete orders; any not fulfilled (not yet sent) return their items to stock.

        The orders are locked first, so two admins deleting the same order at
        once cannot return its stock twice: the second finds it already gone.
        """
        with transaction.atomic():
            locked = list(self.select_for_update().filter(pk__in=[o.pk for o in orders]).order_by("pk"))
            returned = Counter()
            for order in locked:
                if order.status != Order.Status.FULFILLED:
                    returned.update(order.line_counts())
            move_stock({pk: -quantity for pk, quantity in returned.items()})
            self.filter(pk__in=[o.pk for o in locked]).delete()


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

    def line_counts(self):
        """{candy pk: total quantity} across this order's lines."""
        counts = Counter()
        for candy_pk, quantity in self.items.values_list("candy", "quantity"):
            counts[candy_pk] += quantity
        return counts

    def __str__(self):
        """"<username> <yyyy-mm-dd>": who placed it, and the day, in the site's
        time zone (settings.TIME_ZONE). Not unique -- one customer's two orders
        on one day share it. An order not yet saved is dated today.
        """
        placed = timezone.localdate(self.created_at or timezone.now())
        return f"{self.user.username} {placed:%Y-%m-%d}"


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
