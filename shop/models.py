from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

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
