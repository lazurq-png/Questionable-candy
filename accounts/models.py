from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models


class User(AbstractUser):
    """The site's user: Django's stock user plus the customer's allergies.

    docs/adr/0007-custom-user-model.md. Subclassing AbstractUser keeps every stock field, manager and admin form
    working unchanged; which of those fields to drop is a separate decision.

    This model must stay in the *first* migration of its own app. The admin
    migration depends on AUTH_USER_MODEL through swappable_dependency, which
    resolves to that app's first migration -- so a user model added in a later
    migration of an existing app would not exist yet when admin creates its
    foreign key to it on a fresh database.
    """

    # Not null, default empty: an empty list is the single way to say "none".
    # docs/data-model.md section 3.1 records that this loses the distinction
    # between "never asked" and "no allergies".
    allergies = ArrayField(models.CharField(max_length=100), blank=True, default=list)
