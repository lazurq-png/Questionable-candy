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

    def __str__(self):
        return self.name