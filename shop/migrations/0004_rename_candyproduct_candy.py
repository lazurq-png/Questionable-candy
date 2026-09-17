"""Rename CandyProduct to Candy, including every database object named after it.

Written by hand. Non-interactively, makemigrations cannot tell a rename from a
removal and would emit DeleteModel plus CreateModel -- dropping the table and
its rows. RenameModel keeps them, and also renames the content type.

RenameModel renames only the table. PostgreSQL keeps the names the other
objects were created with, so those are renamed here in plain SQL. The flaw
constraint in particular is renamed rather than removed and re-added: AddConstraint
would validate every row again, reopening the deployment precondition migration
0003 carries (docs/data-model.md section 3.3).
"""
from django.db import migrations, models

# (object kind, old name, new name). Run after the table rename, so every
# statement addresses shop_candy.
RENAMES = [
    ("CONSTRAINT", "shop_candyproduct_pkey", "shop_candy_pkey"),
    ("CONSTRAINT", "shop_candyproduct_stock_check", "shop_candy_stock_check"),
    ("CONSTRAINT", "candyproduct_flaw_is_not_blank", "candy_flaw_is_not_blank"),
    ("SEQUENCE", "shop_candyproduct_id_seq", "shop_candy_id_seq"),
]


def rename_sql(kind, old, new):
    if kind == "SEQUENCE":
        return f"ALTER SEQUENCE {old} RENAME TO {new};"
    return f"ALTER TABLE shop_candy RENAME CONSTRAINT {old} TO {new};"


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0003_candyproduct_candyproduct_flaw_is_not_blank"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RenameModel(old_name="CandyProduct", new_name="Candy"),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=[rename_sql(kind, old, new) for kind, old, new in RENAMES],
                    reverse_sql=[rename_sql(kind, new, old) for kind, old, new in reversed(RENAMES)],
                ),
            ],
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="candy",
                    name="candyproduct_flaw_is_not_blank",
                ),
                migrations.AddConstraint(
                    model_name="candy",
                    constraint=models.CheckConstraint(
                        condition=models.Q(("flaw__regex", "\\S")),
                        name="candy_flaw_is_not_blank",
                        violation_error_message="Every candy must disclose a flaw (UC-06).",
                    ),
                ),
            ],
        ),
        migrations.AlterModelOptions(
            name="candy",
            options={"verbose_name_plural": "candies"},
        ),
    ]
