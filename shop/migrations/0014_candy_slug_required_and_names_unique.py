# The second half of 0013: every candy has a slug, so slugs become unique and
# required, and names unique. Fails, changing nothing, on a database holding two
# candies of one name -- that is a decision about real rows, not a migration's
# to make (the night run checked the development database had none).

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0013_candy_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="candy",
            name="slug",
            field=models.SlugField(
                help_text="The candy's web address, filled in from the name. Set once: /candy/<number>/ "
                "redirects here permanently, and browsers cache that.",
                blank=True,
                max_length=220,
                unique=True,
                validators=[django.core.validators.RegexValidator(
                    "\\D", "A slug needs a letter or a dash; digits alone read as a number."
                )],
            ),
        ),
        migrations.AlterField(
            model_name="candy",
            name="name",
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
