from django.db import models

# Create your models here.
class CandyProduct(models.Model):
    name = models.CharField(max_length=200)
    flavor = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    flaw = models.CharField(max_length=200)

    def __str__(self):
        return self.name