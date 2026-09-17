# The second half of 0011: every order now has a token, so it becomes unique
# and required.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0011_order_confirmation_token"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="confirmation_token",
            field=models.UUIDField(editable=False, unique=True),
        ),
    ]
