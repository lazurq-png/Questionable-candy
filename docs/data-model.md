# Candy Ordering Website

Data Model Specification — Entity\-Relationship Model

|              |                                                                                                        |
| ------------ | ------------------------------------------------------------------------------------------------------ |
| **Status**   | Draft                                                                                                  |
| **Version**  | 0\.2                                                                                                   |
| **Date**     | 2026\-09\-14                                                                                           |
| **Database** | PostgreSQL                                                                                             |
| **ORM**      | Django ORM \(no Django REST Framework — see [ADR 0003](adr/0003-backend.md)\)                          |
| **Notation** | Entity\-Relationship Diagram (ERD) — the current, most widely used notation for relational data models |

## 1\. Overview

This document defines the data model for the Candy Ordering Website: the entities behind the Candy catalog, User accounts, the ShoppingCart, and Orders, and how they relate. It follows the entities named in the requirements specification (Candy, User, Cart, Order) and expands each into join tables where the relationship is many\-to\-many in practice (ShoppingCart–Candy via `ShoppingCartItem`, Order–Candy via `OrderItem`).

The requirements specification calls the entity "Cart"; this model and [`erd.png`](erd.png) call it **`ShoppingCart`**, and that is the name to use when it is built. No such model exists yet — see the status table in §3.

The model assumes Django's ORM mapped onto PostgreSQL, so it uses PostgreSQL\-specific field types (`ArrayField`) where they are a natural fit, consistent with the earlier decision to use PostgreSQL for its native array and JSON support.

## 2\. Entity\-Relationship Diagram

![Candy Ordering Website entity-relationship diagram](erd.png)

Diagram source: [`erd.excalidraw`](erd.excalidraw) — re\-export to `erd.png` after editing.

Boxes are entities (tables); each line's end labels give cardinality (`1`, `0..1`, `*`). `SocialAccount` would be provided by django\-allauth rather than defined by this project, and is currently deferred — see §3\.2. The diagram still draws it.

## 3\. Entity Definitions

**This section is the target model, not a description of the code.** The application is early; most of it is not built. Each entity below carries a status so the gap is visible rather than implied:

| Entity          | Status      | In code                                                                           |
| --------------- | ----------- | --------------------------------------------------------------------------------- |
| User            | implemented | `accounts.User`, a custom user model — [ADR 0007](adr/0007-custom-user-model.md)  |
| SocialAccount   | deferred    | Needs django\-allauth, deferred by [ADR 0002](adr/0002-middleware.md)              |
| Candy           | partial     | `shop.Candy` — see the note in §3\.3                                        |
| ShoppingCart    | not started | Cart state currently lives in `request.session["shoppingcart"]`, not in a table    |
| ShoppingCartItem| not started | —                                                                                  |
| Order           | not started | —                                                                                  |
| OrderItem       | not started | —                                                                                  |

`ArrayField` on `User.allergies` and `Candy.allergens` is viable: [ADR 0004](adr/0004-database.md) is implemented, the application runs on PostgreSQL, and `django.contrib.postgres` is installed.

### 3\.1 User

`accounts.User`, which subclasses Django's `AbstractUser` and adds `allergies` ([ADR 0007](adr/0007-custom-user-model.md)). Every stock field is kept; which of them to remove is an open decision. [ADR 0002](adr/0002-middleware.md) chose Django's session authentication and defers django\-allauth, which also works with a custom user model.

| Field            | Type                  | Constraints                   | Notes                                                                                                       |
| ---------------- | --------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| id               | BigAutoField          | PK                            |                                                                                                             |
| username         | CharField(150)        | unique, not null              | Stock login field.                                                                                          |
| email            | EmailField(254)       | not null, blank allowed       | **Open:** the earlier specification made this unique and the primary identifier; neither is implemented.   |
| password         | CharField(128)        | not null                      | Hash. Can be set unusable for accounts that never log in with a password.                                   |
| first_name       | CharField(150)        | not null, blank allowed       | `""` means no name; it is never `NULL`.                                                                     |
| last_name        | CharField(150)        | not null, blank allowed       | As `first_name`.                                                                                            |
| allergies        | ArrayField(CharField(100)) | not null, default empty  | `[]` is the only way to say "none"; "never asked" is not distinguishable. Cross\-referenced against `Candy.allergens` for the UC\-07 warning. No fixed vocabulary yet. |
| is_staff         | Boolean               | default false                 | Grants the admin site — the Site Administrator actor (UC\-06).                                              |
| is_superuser     | Boolean               | default false                 |                                                                                                             |
| is_active        | Boolean               | default true                  | `False` blocks login. The way to disable an account without deleting it.                                    |
| last_login       | DateTimeField         | nullable                      | Part of the password\-reset token: logging in invalidates an unused reset link.                             |
| date_joined      | DateTimeField         | not null, default now         | A default, not `auto_now_add` — it is editable.                                                             |
| groups, user_permissions | ManyToMany → auth | —                           | Stock permission tables.                                                                                    |

### 3\.2 SocialAccount _(deferred — not part of the current model)_

> Provided by django\-allauth, which [ADR 0002](adr/0002-middleware.md) defers, and needed only by UC\-02, which [`requirements.md`](requirements.md) demoted to *Should have* on 2026\-09\-14. Kept here so the shape is known if social login is adopted; it is **not** a table this project creates. `erd.png` still shows it — the diagram lags this text until `erd.excalidraw` is re\-exported.

| Field      | Type              | Constraints | Notes                                       |
| ---------- | ----------------- | ----------- | ------------------------------------------- |
| id         | BigAutoField      | PK          |                                             |
| user_id    | ForeignKey → User | not null    | One User can have several linked providers. |
| provider   | CharField         | not null    | e.g. `google`.                              |
| uid        | CharField         | not null    | Provider\-issued identifier.                |
| extra_data | JSONField         | nullable    | Raw profile payload from the provider.      |

### 3\.3 Candy

| Field           | Type                  | Constraints         | Notes                                                                                      |
| --------------- | --------------------- | ------------------- | ------------------------------------------------------------------------------------------ |
| id              | BigAutoField          | PK                  |                                                                                            |
| name            | CharField             | unique, not null    |                                                                                            |
| slug            | SlugField             | unique, not null    | Used in catalog/detail URLs.                                                               |
| description     | TextField             | not null            | Shown on the detail view (UC\-03). Implemented 2026\-09\-15 as `TextField(blank=True, default="")` — not null, but not mandatory; only `flaw` is. |
| flaw            | TextField             | **not null**        | Mandatory design/feature downside (UC\-06) — enforced at the model level, not just the UI. |
| price           | DecimalField          | not null            |                                                                                            |
| stock_quantity  | PositiveIntegerField  | not null, default 0 | Checked on every ShoppingCart mutation and at checkout.                                    |
| sugar_content_g | DecimalField          | nullable            | Feeds the checkout health warning (UC\-07).                                                |
| allergens       | ArrayField(CharField) | default empty       | PostgreSQL array; cross\-referenced against `User.allergies`.                           |
| is_published    | Boolean               | default true        | Unpublished items are hidden from the catalog.                                             |
| created_at      | DateTimeField         | auto                |                                                                                            |
| updated_at      | DateTimeField         | auto                |                                                                                            |

**Partially implemented as `shop.Candy`.** The code has an earlier, smaller model that this entity is the target for. The differences are deliberate and open, not drift to be silently tolerated:

| Aspect          | Target `Candy`                                                            | Current `shop.Candy`                |
| --------------- | ------------------------------------------------------------------------- | ----------------------------------- |
| Present         | `name`, `flaw`, `price`, `description`, `is_published`, timestamps        | same; rows older than migration `0007` carry its run time in both fields |
| `stock_quantity`| named `stock_quantity`                                                    | named `stock`                       |
| `flaw` type     | `TextField`, unbounded                                                    | `CharField(max_length=200)`         |
| Missing         | `slug`, `sugar_content_g`, `allergens`                                    | —                                   |
| Extra           | —                                                                         | `flavor` — in no specification; `image` — interim static path, see below |
| Constraints     | `name`/`slug` unique, `flaw` not null                                     | no uniqueness; `flaw` not null **and** non\-blank |

**`image` is interim, not part of the target.** It is a `CharField` naming a static file (e.g. `shop/candy/sour-bricks.svg`), blank meaning a placeholder, filled by `manage.py seed_candy`. It exists because candy needed pictures before the media\-storage decision [ADR 0004](adr/0004-database.md) leaves open was made; that decision should replace or keep it.

**UC\-06's "enforced at the model level" intent now holds.** Since 2026\-09\-15 `flaw` carries a `CheckConstraint` (`candy_flaw_is_not_blank` — added by migration `0003` as `candyproduct_flaw_is_not_blank`, renamed by `0004`) requiring at least one non\-whitespace character, so the empty string — which satisfies NOT NULL perfectly well, and which `objects.create()` would happily write — is rejected by the database rather than only by a form. §5's design note is therefore satisfied for `flaw`.

The uniqueness constraints on `name`/`slug` still do not exist, and the remaining fields are a migration, not an edit; it has not been scheduled. The rename from `CandyProduct` was migration `0004`.

> **Deployment precondition for migration `0003`.** `AddConstraint` compiles to a plain `ALTER TABLE ... ADD CONSTRAINT ... CHECK`, which PostgreSQL validates against every existing row. Rows with a blank `flaw` were legal before it, so on any database holding one, `migrate` aborts — transactionally, leaving the old schema intact, but with a Postgres error that names no row. Such a database predates migration `0004`, so the table still has its old name. Find them with:
>
> ```sql
> SELECT id, name FROM shop_candyproduct WHERE flaw !~ '\S';
> ```
>
> Each needs a real flaw before the migration can apply. **Do not backfill a placeholder:** a fabricated disclosure is precisely what UC\-06 exists to prevent, so this is a decision per row, not a data migration.

### 3\.4 ShoppingCart

| Field       | Type              | Constraints      | Notes                                                                 |
| ----------- | ----------------- | ---------------- | --------------------------------------------------------------------- |
| id          | BigAutoField      | PK               |                                                                       |
| user_id     | ForeignKey → User | nullable, unique | Null supports a guest cart; unique enforces one active cart per User. |
| session_key | CharField         | nullable         | Identifies a guest ShoppingCart before login.                         |
| created_at  | DateTimeField     | auto             |                                                                       |
| updated_at  | DateTimeField     | auto             |                                                                       |

### 3\.5 ShoppingCartItem

Join table resolving the many\-to\-many relationship between ShoppingCart and Candy.

| Field                          | Type                      | Constraints         | Notes                                                         |
| ------------------------------ | ------------------------- | ------------------- | ------------------------------------------------------------- |
| id                             | BigAutoField              | PK                  |                                                               |
| shopping_cart_id               | ForeignKey → ShoppingCart | not null            |                                                               |
| candy_id                       | ForeignKey → Candy        | not null            |                                                               |
| quantity                       | PositiveIntegerField      | not null, default 1 |                                                               |
| added_at                       | DateTimeField             | auto                |                                                               |
| _(shopping_cart_id, candy_id)_ | —                         | unique together     | One row per Candy per ShoppingCart; quantity holds the count. |

### 3\.6 Order

| Field                   | Type                | Constraints | Notes                                                   |
| ----------------------- | ------------------- | ----------- | ------------------------------------------------------- |
| id                      | BigAutoField        | PK          |                                                         |
| user_id                 | ForeignKey → User   | not null    |                                                         |
| status                  | CharField (choices) | not null    | `pending`, `paid`, `cancelled`, `fulfilled`.            |
| total_amount            | DecimalField        | not null    | Snapshot total at order creation.                       |
| warning_acknowledged_at | DateTimeField       | nullable    | Timestamp of the UC\-07 health\-warning acknowledgment. |
| purchase_confirmed_at   | DateTimeField       | nullable    | Timestamp of the final UC\-08 confirmation.             |
| created_at              | DateTimeField       | auto        |                                                         |
| paid_at                 | DateTimeField       | nullable    | Set once payment succeeds.                              |

### 3\.7 OrderItem

Join table resolving the many\-to\-many relationship between Order and Candy, with a price snapshot.

| Field      | Type                 | Constraints | Notes                                                               |
| ---------- | -------------------- | ----------- | ------------------------------------------------------------------- |
| id         | BigAutoField         | PK          |                                                                     |
| order_id   | ForeignKey → Order   | not null    |                                                                     |
| candy_id   | ForeignKey → Candy   | not null    |                                                                     |
| quantity   | PositiveIntegerField | not null    |                                                                     |
| unit_price | DecimalField         | not null    | Price at the time of purchase — Candy's own price may change later. |
| subtotal   | DecimalField         | not null    | `quantity × unit_price`, stored rather than recomputed.             |

## 4\. Relationship Summary

| Relationship         | Cardinality | Enforced By                          |
| -------------------- | ----------- | ------------------------------------ |
| User – SocialAccount | 1 : \*      | django\-allauth — deferred, see §3\.2 |
| User – ShoppingCart  | 1 : 0..1    | `ShoppingCart.user_id` (unique, nullable FK) |
| User – Order         | 1 : \*      | `Order.user_id`                      |
| ShoppingCart – Candy | \* : \*     | via `ShoppingCartItem`               |
| Order – Candy        | \* : \*     | via `OrderItem`                      |

## 5\. Design Notes

- The **Flaw** field on Candy is modeled as `NOT NULL` specifically so the requirement that every candy discloses a downside (UC\-06) is a database\-level guarantee, not just a form validation.
- **Allergens** (Candy) and **allergies** (User) are both PostgreSQL `ArrayField`s rather than a normalized join table, reflecting the ADR decision to use PostgreSQL for its native array/JSON support on small, list\-like attributes.
- **ShoppingCartItem** and **OrderItem** exist because ShoppingCart–Candy and Order–Candy are genuinely many\-to\-many relationships (a candy appears in many carts/orders and a cart/order holds many candies); `quantity` and, for orders, a `unit_price` snapshot live on the join table rather than on either parent.
- **ShoppingCart.user_id** is nullable to leave room for a guest cart keyed by `session_key`, matching the open question in the requirements specification about whether guest checkout is supported.
