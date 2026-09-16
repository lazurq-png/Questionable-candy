import factory
from shop.models import Candy

class CandyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Candy

    name = factory.Sequence(lambda n: f"Candy {n}")
    description = "Chewy, fluorescent, and faintly medicinal."
    flavor = "sour"
    price = 2.50
    stock = 10
    flaw = "rotten"