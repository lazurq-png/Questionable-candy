import factory
from shop.models import CandyProduct

class CandyProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CandyProduct

    name = factory.Sequence(lambda n: f"Candy {n}")
    flavor = "sour"
    price = 2.50
    stock = 10
    flaw = "rotten"