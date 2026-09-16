from django.db import models


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
        ]

    def __str__(self):
        return self.name