from django.db import models

# Create your models here.
class CandyProduct(models.Model):
    name = models.CharField(max_length=200)
    # UC-03 step 2 renders this on the detail page. Not null (docs/data-model.md
    # section 3.4) but not mandatory: UC-06 singles out `flaw` as the field that
    # may never be omitted, and holding description to that bar is a tightening
    # nobody has asked for. default="" so the migration needs no answer about
    # existing rows.
    description = models.TextField(blank=True, default="")
    flavor = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    flaw = models.CharField(max_length=200)

    class Meta:
        constraints = [
            # UC-06's Constraint: "Required at the data-model level, not only in
            # the form, so it can never be silently omitted."
            #
            # NOT NULL alone does not deliver that -- it is satisfied by the
            # empty string, and CandyProduct.objects.create(flaw="") bypasses
            # form validation entirely. This closes the gap docs/data-model.md
            # section 3.4 records as still open.
            #
            # Matched on \S rather than != "" so that a flaw of "   " is
            # rejected too. That is not extra strictness: Django's form field
            # strips whitespace before checking blank, so the form already
            # rejects it, and the constraint would otherwise be the more
            # permissive of the two.
            models.CheckConstraint(
                condition=models.Q(flaw__regex=r"\S"),
                name="candyproduct_flaw_is_not_blank",
                violation_error_message="Every candy must disclose a flaw (UC-06).",
            ),
        ]

    def __str__(self):
        return self.name