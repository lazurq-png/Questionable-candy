"""Seed the catalog with the shop's candy.

    python manage.py seed_candy

Safe to run any number of times. Each candy is matched by name: a missing one
is created, and an existing one only has its *empty* text fields filled in.
Nothing that already has a value is overwritten -- an administrator's edit to a
price or a flaw survives every later seed.

Candy data lives here rather than in a data migration so that nothing reaches a
database unless someone runs this on purpose.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Candy

# Only text fields count as "empty": a stock of 0 or a price is a real value.
FILLABLE_TEXT_FIELDS = ("description", "flavor", "flaw", "image")

CANDIES = [
    # The first two existed in the development database before this command,
    # with no description or image; their other values are theirs.
    {
        "name": "Sour Bricks",
        "description": "Dense, brick-shaped sour candy with a crackling sugar crust "
        "that gives way to a sharp citrus tang.",
        "flavor": "sour",
        "price": Decimal("12.50"),
        "stock": 10,
        "flaw": "Chips a tooth on contact.",
        "image": "shop/candy/sour-bricks.svg",
    },
    {
        "name": "Hollow Humbug",
        "description": "A glossy striped peppermint humbug with a bracing, "
        "old-fashioned mint finish.",
        "flavor": "mint",
        "price": Decimal("9.00"),
        "stock": 3,
        "flaw": "Entirely hollow inside.",
        "image": "shop/candy/hollow-humbug.svg",
    },
    {
        "name": "Fizzing Lemon Drops",
        "description": "Bright boiled lemon drops with a sherbet centre that fizzes "
        "when the shell cracks.",
        "flavor": "lemon",
        "price": Decimal("3.50"),
        "stock": 40,
        "flaw": "The fizz is gone in ten seconds and leaves a long, faintly soapy aftertaste.",
        "image": "shop/candy/fizzing-lemon-drops.svg",
    },
    {
        "name": "Midnight Licorice Coils",
        "description": "Tightly wound coils of soft black licorice with a deep "
        "anise flavour.",
        "flavor": "licorice",
        "price": Decimal("4.25"),
        "stock": 25,
        "flaw": "Stains teeth and tongue grey-black for the better part of an hour.",
        "image": "shop/candy/midnight-licorice-coils.svg",
    },
    {
        "name": "Strawberry Cloud Marshmallows",
        "description": "Pillowy pink marshmallows whipped with real strawberry purée.",
        "flavor": "strawberry",
        "price": Decimal("5.00"),
        "stock": 30,
        "flaw": "Melts into a sticky puddle within minutes in a warm pocket.",
        "image": "shop/candy/strawberry-cloud-marshmallows.svg",
    },
    {
        "name": "Salted Caramel Chews",
        "description": "Slow-cooked caramel chews finished with flakes of sea salt, "
        "each twisted in wax paper.",
        "flavor": "salted caramel",
        "price": Decimal("6.75"),
        "stock": 18,
        "flaw": "Chewy enough to pull out loose fillings.",
        "image": "shop/candy/salted-caramel-chews.svg",
    },
    {
        "name": "Blue Raspberry Ropes",
        "description": "Long, pull-apart candy ropes in an electric blue raspberry "
        "flavour.",
        "flavor": "blue raspberry",
        "price": Decimal("3.25"),
        "stock": 50,
        "flaw": "The dye rubs off on fingers, lips and any light-coloured fabric.",
        "image": "shop/candy/blue-raspberry-ropes.svg",
    },
    {
        "name": "Dark Chocolate Sea Pebbles",
        "description": "Smooth dark chocolate shaped and speckled like pebbles from "
        "a shingle beach.",
        "flavor": "dark chocolate",
        "price": Decimal("8.90"),
        "stock": 12,
        "flaw": "Looks so much like real pebbles that people throw them out by mistake.",
        "image": "shop/candy/dark-chocolate-sea-pebbles.svg",
    },
    {
        "name": "Cinnamon Fire Hearts",
        "description": "Small red cinnamon hearts with a slow, building heat.",
        "flavor": "cinnamon",
        "price": Decimal("4.00"),
        "stock": 22,
        "flaw": "The burn keeps building for a full minute after swallowing.",
        "image": "shop/candy/cinnamon-fire-hearts.svg",
    },
    {
        "name": "Peach Gummy Rings",
        "description": "Soft peach gummy rings rolled in a light sugar dusting.",
        "flavor": "peach",
        "price": Decimal("3.75"),
        "stock": 35,
        "flaw": "Fuse into one solid lump if the bag is stored anywhere warm.",
        "image": "shop/candy/peach-gummy-rings.svg",
    },
    {
        "name": "Maple Fudge Squares",
        "description": "Crumbly, melt-in-the-mouth fudge made with dark maple syrup.",
        "flavor": "maple",
        "price": Decimal("7.50"),
        "stock": 8,
        "flaw": "So sweet the back of the throat aches by the second square.",
        "image": "shop/candy/maple-fudge-squares.svg",
    },
    {
        "name": "Watermelon Slice Jellies",
        "description": "Two-tone jellies shaped like watermelon wedges, green rind "
        "and all.",
        "flavor": "watermelon",
        "price": Decimal("3.95"),
        "stock": 28,
        "flaw": "The black 'seeds' are poppy seeds that lodge between teeth all day.",
        "image": "shop/candy/watermelon-slice-jellies.svg",
    },
    {
        "name": "Honeycomb Crunch Bars",
        "description": "Airy golden honeycomb toffee that shatters into shards.",
        "flavor": "honey",
        "price": Decimal("5.50"),
        "stock": 16,
        "flaw": "Draws moisture from the air and turns chewy within a day of opening.",
        "image": "shop/candy/honeycomb-crunch-bars.svg",
    },
    {
        "name": "Green Apple Sour Belts",
        "description": "Flat, tangy green apple belts with a heavy sour sugar coat.",
        "flavor": "green apple",
        "price": Decimal("3.60"),
        "stock": 45,
        "flaw": "The sour coating sheds everywhere and leaves the tongue sore.",
        "image": "shop/candy/green-apple-sour-belts.svg",
    },
    {
        "name": "Coconut Snowballs",
        "description": "Soft coconut fondant balls rolled in toasted desiccated coconut.",
        "flavor": "coconut",
        "price": Decimal("4.80"),
        "stock": 20,
        "flaw": "Loose coconut flakes catch in the throat and start a coughing fit.",
        "image": "shop/candy/coconut-snowballs.svg",
    },
    {
        "name": "Cola Bottle Gummies",
        "description": "Classic fizzy cola bottles with a sugared outside.",
        "flavor": "cola",
        "price": Decimal("3.10"),
        "stock": 60,
        "flaw": "Only the sugar coating tastes of cola; the inside is plain gelatin.",
        "image": "shop/candy/cola-bottle-gummies.svg",
    },
    {
        "name": "Lavender Rock Candy",
        "description": "Purple sugar crystals grown on a wooden stick, scented with "
        "lavender.",
        "flavor": "lavender",
        "price": Decimal("6.20"),
        "stock": 10,
        "flaw": "Tastes like soap to roughly half the people who try it.",
        "image": "shop/candy/lavender-rock-candy.svg",
    },
    {
        "name": "Espresso Bean Toffees",
        "description": "Buttery toffees wrapped around a crushed espresso bean.",
        "flavor": "coffee",
        "price": Decimal("7.25"),
        "stock": 14,
        "flaw": "Each piece carries as much caffeine as half a cup of coffee.",
        "image": "shop/candy/espresso-bean-toffees.svg",
    },
    {
        "name": "Rainbow Lollipop Swirls",
        "description": "Flat spiral lollipops in every colour of the rainbow.",
        "flavor": "mixed fruit",
        "price": Decimal("2.95"),
        "stock": 38,
        "flaw": "Every colour tastes exactly the same.",
        "image": "shop/candy/rainbow-lollipop-swirls.svg",
    },
    {
        "name": "Ginger Snap Drops",
        "description": "Amber boiled drops made with fresh root ginger.",
        "flavor": "ginger",
        "price": Decimal("3.40"),
        "stock": 26,
        "flaw": "The ginger is strong enough to make eyes water on the first suck.",
        "image": "shop/candy/ginger-snap-drops.svg",
    },
    {
        "name": "Butterscotch Pillows",
        "description": "Soft-centred butterscotch pillows in a glossy hard shell.",
        "flavor": "butterscotch",
        "price": Decimal("4.60"),
        "stock": 1,
        "flaw": "Weld together in the tin and only come apart by shattering.",
        "image": "shop/candy/butterscotch-pillows.svg",
    },
    {
        "name": "Chili Mango Chews",
        "description": "Chewy mango pieces dusted with chili and lime.",
        "flavor": "chili mango",
        "price": Decimal("5.25"),
        "stock": 0,
        "flaw": "The chili dust puffs up when unwrapped and stings the eyes.",
        "image": "shop/candy/chili-mango-chews.svg",
    },
]


class Command(BaseCommand):
    """Implements `manage.py seed_candy`; see the module docstring."""

    help = "Create the shop's candy, filling empty fields on existing rows only."

    @transaction.atomic
    def handle(self, *args, **options):
        created = filled = unchanged = 0
        for data in CANDIES:
            defaults = {key: value for key, value in data.items() if key != "name"}
            candy, was_created = Candy.objects.get_or_create(name=data["name"], defaults=defaults)
            if was_created:
                created += 1
                continue

            empty = [f for f in FILLABLE_TEXT_FIELDS if not getattr(candy, f) and data.get(f)]
            for field in empty:
                setattr(candy, field, data[field])
            if empty:
                candy.save(update_fields=empty)
                filled += 1
            else:
                unchanged += 1

        self.stdout.write(
            f"seed_candy: {created} created, {filled} filled in, {unchanged} unchanged."
        )
