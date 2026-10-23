# Written by hand: every existing candy needs its own slug before the column
# can be unique and required, so it is added nullable and filled here, and 0014
# then requires it -- in separate transactions, as 0011/0012 are
# (docs/ai/night-2026-09-17/decisions.md D14). Additive throughout.

from django.db import migrations, models
from django.utils.text import slugify


def fill_slugs(apps, schema_editor):
    """Each candy gets slugify(name), made unique the way Candy.save() makes it.

    A frozen copy of shop.models.unique_candy_slug, since a migration must not
    import code that may change after it.
    """
    candy_model = apps.get_model("shop", "Candy")
    taken = set(candy_model.objects.exclude(slug__isnull=True).values_list("slug", flat=True))
    for candy in candy_model.objects.filter(slug__isnull=True).order_by("pk"):
        base = slugify(candy.name)[:200] or "candy"
        if base.isdigit():
            base = f"candy-{base}"
        slug, suffix = base, 2
        while slug in taken:
            slug, suffix = f"{base}-{suffix}", suffix + 1
        taken.add(slug)
        candy.slug = slug
        candy.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0012_order_confirmation_token_required"),
    ]

    operations = [
        migrations.AddField(
            model_name="candy",
            name="slug",
            field=models.SlugField(max_length=220, null=True),
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
    ]
