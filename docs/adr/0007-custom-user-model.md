---
status: "accepted"
date: "2026-09-16"
decision-makers: "Martin Larsson"
---

# 0007. A custom user model, so that allergies can live on User

## Context and Problem Statement

`User` is the only account entity in `docs/data-model.md`, and it carries the
customer's `allergies`. Django's stock `django.contrib.auth.models.User` cannot
take a new field: it belongs to Django, not to this project. Putting `allergies`
on `User` therefore means pointing `AUTH_USER_MODEL` at a user model this
project owns — which Django recommends doing at the start of a project, because
switching later cannot be migrated automatically.

## Decision Drivers

- No model references `User` yet, and the development database holds no users,
  so this is the cheapest the switch will ever be
- Do not decide more than was asked: which stock user fields to drop is a
  separate, open question

## Considered Options

- Subclass `AbstractUser` and add `allergies`
- Subclass `AbstractBaseUser` and `PermissionsMixin`, declaring only the fields
  wanted

## Decision Outcome

Chosen option: "Subclass `AbstractUser` and add `allergies`", because it keeps
every stock field, the stock manager and the stock admin working, and leaves the
question of which fields to drop open rather than deciding it by accident.

The model is `accounts.User` in a new `accounts` app, not in `shop`. Django
resolves the admin app's `swappable_dependency(AUTH_USER_MODEL)` to the user
app's **first** migration, so the user model must be created by that migration.
In `shop`, whose `0001` is long applied, a user model in `0004` would not yet
exist when admin creates its foreign key on a fresh database.

`allergies` is `ArrayField(CharField(max_length=100), blank=True, default=list)`,
**not null**. An empty list is the only way to store "none", at the cost of not
distinguishing "never asked" from "no allergies". It is cheap to change while no
user rows exist.

### Confirmation

- `tests/unit/test_user_model.py` fails if `get_user_model()` is not
  `accounts.User`, and checks that `allergies` defaults to `[]`, rejects `NULL`
  at the database, and supports overlap queries.
- `tests/integration/test_views.py::test_admin_user_page_lets_an_administrator_edit_allergies`
  fails if the admin form omits `allergies` — which the stock `UserAdmin`
  fieldsets do.
- Nothing prevents a later change to `AUTH_USER_MODEL`; the comment above it in
  `mysite/settings.py` points here.

### Existing development databases

A database migrated before this change has `admin.0001_initial` applied ahead of
its new dependency `accounts.0001_initial`, and every `migrate` or
`makemigrations` against it raises `InconsistentMigrationHistory`. Test
databases and CI are created fresh and are unaffected.

To repair one: confirm `django_admin_log` is empty or disposable, then run the
following. Stashing only `mysite/settings.py` puts back the stock `User` for the
one command that needs it. No comments are inlined: cmd.exe passes a `#` and
everything after it as arguments. Used on the author's database on 2026-09-16.

```
git stash push mysite/settings.py
python manage.py migrate admin zero
git stash pop
python manage.py migrate
```

The old `auth_user`, `auth_user_groups` and `auth_user_user_permissions` tables
are left behind unused. The alternative is to recreate the database. Neither is
safe on a database with real admin history or users; that case needs a
hand-written data migration.

## Pros and Cons of the Options

### Subclass `AbstractUser` and add `allergies`

- Good, because the stock manager, forms and admin keep working; the admin only
  needs `allergies` added to its fieldsets
- Good, because stock fields can still be removed later, one at a time, by
  overriding them in the subclass
- Bad, because existing development databases need the repair above
- Bad, because it keeps `username`, `first_name`, `last_name`, `is_active` and
  `date_joined` until someone decides otherwise

### Subclass `AbstractBaseUser` and `PermissionsMixin`

- Good, because only wanted fields exist, and email can be the login
- Bad, because it needs a custom manager and admin, and decides the open
  field-removal questions as a side effect

## More Information

Related: [0002](0002-middleware.md) chose Django's session authentication,
which works unchanged with a custom user model; django-allauth, deferred there,
supports custom user models too. [0004](0004-database.md) supplies the
`ArrayField`.

Revisit when deciding whether to remove stock fields — that is where the
`AbstractBaseUser` option becomes relevant again.
