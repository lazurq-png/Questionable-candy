# Written by hand: a unique, non-null column cannot take one default for rows
# that already exist, so it is added nullable here and each existing row gets
# its own token; 0012 then makes it unique and required. Two migrations, so the
# rows are updated and the table altered in separate transactions -- PostgreSQL
# refuses ALTER TABLE on a table with pending deferred-constraint trigger events
# from updates in the same transaction. Additive throughout.

import uuid

from django.db import migrations, models


def give_existing_orders_a_token(apps, schema_editor):
    """Orders placed before tokens existed each get a distinct one."""
    order_model = apps.get_model("shop", "Order")
    for order in order_model.objects.filter(confirmation_token__isnull=True).only("pk"):
        order.confirmation_token = uuid.uuid4()
        order.save(update_fields=["confirmation_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0010_orders"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="confirmation_token",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(give_existing_orders_a_token, migrations.RunPython.noop),
    ]
