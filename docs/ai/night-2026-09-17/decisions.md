# Decisions — night-2026-09-17

Choices made during the run, with the alternatives and why they lost. Choices
the human settled are in `plan.md` ("Settled by the human") and are not
repeated here.

## D1. T1: a duplicate-code lint message left standing

`pylint` R0801 matches five lines of theme setup in
`tests/e2e/test_error_pages.py` (`_show`) against the parametrized body of
`tests/e2e/test_theme.py`. Removing it means moving that setup out of
`test_theme.py` into a shared helper, which changes an existing test file for a
refactor-class message, outside T1. It is a refactor note, not a warning or an
error, and the lint gate passes. Left for Exploration, where "duplicated code"
is an allowed category.

## D2. T1: 404 and CSRF pages extend base.html, the 500 page does not

Django's `page_not_found` and `csrf_failure` render with the request (context
processors run, `csrf_token` is fresh); `server_error` renders with nothing.
Extending base.html for the first two keeps the header, cart and theme toggle;
the 500 page must not depend on the request or a context processor, as the plan
requires.

## D3. T2: the allergen vocabulary lives in `shop/allergens.py`

Both `Candy.allergens` and `accounts.User.allergies` need it. Options:
- **`shop/allergens.py` (chosen):** a plain constants module. `accounts` imports
  it, but `shop` imports nothing from `accounts`, so there is no cycle, and
  nothing about models or a service layer (ADR 0003) is involved. Allergens
  are food data, which is the shop's domain.
- **`accounts/allergens.py`:** puts food vocabulary in the user app, and makes
  `shop` depend on `accounts` for a candy's own field.
- **A project-level module (`mysite/`):** `mysite` is settings and URLs; no
  domain data lives there today.

The choices are enforced by `clean_fields()`/`full_clean()` and forms, not by a
database constraint. A `<@ ARRAY[...]` check would need a migration for every
vocabulary change, and nothing writes these fields except forms and the seed.

## D4. T2: legacy free-text allergies are not migrated or guarded (reviewer, Low)

The reviewer found that `UserAdminChangeForm` renders only the 14 keys, so a
user whose `allergies` already held a free-text value (e.g. `"nuts"`) would
lose it silently on the next admin save. Not fixed in code:

- A form check that refuses the save deadlocks. The value is also rejected by
  the model's choices, so the admin could never save that user without
  removing it.
- Mapping legacy values to keys is a data decision per value ("nuts" could be
  tree nuts or peanuts).
- Measured exposure: the dev database has **0** users with any allergy (queried
  during T2). Before today the only way to write one was the admin's
  comma-separated text box.

Raised as questions.md Q2. `allergens.names()` skips unknown keys, so a legacy
value cannot break rendering or the later warning; it is simply not matched.

## D5. T3: the header's account control on a phone

The plan's T3 lists, for the header: logged out, "Log in" and "Sign up";
logged in, the username, "My allergies" and a "Log out" button. The existing
phone header must stay one row with no sideways scroll (tests/e2e/test_theme.py).

Measured at 375px before building: brand 108px, theme toggle 44px, cart 80px,
two 8px gaps, so about 87px of the 343px content width is free. "Log in" is
about 66px. "Log in" plus "Sign up" is about 150px, and a username plus a Log
out button is more.

- **Chosen:**
  - Logged out: "Log in" always. "Sign up" from 30rem up; below that it is
    hidden, and the login page links to sign-up ("Create an account").
  - Logged in: a native `<details>` named by the username, holding "My
    allergies" and "Log out". Every item the plan lists is in the header. On
    a phone, sign-up is one tap further away, and the logged-in items are one
    tap behind the username at every width.
- **Rejected:**
  - A second header row on phones: breaks an existing, tested layout rule.
  - Moving the theme toggle into the menu: changes an unrelated, settled
    control.
  - An Alpine dropdown: more script and focus handling for what `<details>`
    gives natively.

The reviewer confirmed the width at 375px: one row for a long username with a
3-digit cart count. Asked of the human as questions.md Q3. Not marked
PROVISIONAL: every later checkout task depends on T3's login, and the layout is
cheap to change without touching them.

## D6. T3: pylint R0901 on `SignUpForm` left standing

`too-many-ancestors (9/7)` comes from subclassing Django's `UserCreationForm`,
whose own hierarchy supplies the ancestors. Flattening it would mean
re-implementing the password handling the plan asks to reuse. Refactor-class
message; the lint gate passes.

## D7. T3: sign-up uses LoginView's decorators (reviewer, Low)

`SignUpView` is wrapped in `sensitive_post_parameters("password1",
"password2")`, `csrf_protect` and `never_cache`, as Django's `LoginView` is, so
an error report during sign-up (for example a unique-username race) never
carries a plain-text password. Tested, with a negative control.

## D8. T4: `shop/checkout.py` holds the warning's content and the acknowledgment

A module of plain functions and frozen dataclasses over the session, like
`shop/cart.py`: `health_warning(lines, user)`, `acknowledge`,
`is_acknowledged`. The alternatives:
- **Compute in the view:** about 40 lines of arithmetic and grouping in
  `views.py`, untestable without HTTP.
- **Model methods:** the warning is about a cart and a customer together, and
  neither `Candy` nor `User` owns that.

It extends the shape night-2026-09-16 questions.md Q1 asked about (is
`cart.py` a service layer under ADR 0003?). The reviewer suggested answering
Q1 for both modules together; noted there, not re-asked. The view imports it as
`checkout_state`, because a view is already named `checkout`.

## D9. T4: until T5 exists, acknowledging returns to the warning page

The plan's next step, the confirmation page, is T5. After a valid
acknowledgment the view redirects (post/redirect/get) back to the warning,
which then says it has been acknowledged and that confirming is not built yet.
T5 replaces that redirect.

## D10. T4: any cart write clears checkout progress (reviewer, Low)

At first the acknowledgment was checked only by fingerprint, so a change that
was later undone (add, then remove) made it valid again. The plan says "Any
change to the cart invalidates it", so `cart._save` now also removes
`request.session["checkout"]`. The fingerprint stays too: it covers what a cart
write does not, namely an administrator changing a candy's sugar or allergens,
and the customer changing their own allergies. One effect: an Update with an
unchanged quantity also clears it, because `set_quantity` always saves. That is
the conservative direction.

## D11. T5: how the three confirmations are made distinct, and what is enforced where

The plan settles one page with three controls: a checkbox worded with the
item count and total, the total typed back, and the Place my order button.
Choices made building it:

- **Server-side, all three always.** `ConfirmOrderForm` requires the checkbox,
  a typed total equal to the total shown, and `place_order=yes` (which only
  the button sends). Alpine's unlocking is presentation; without JavaScript
  all three controls are usable, and still all required.
- **Typed total leniency:** a leading `$`, a decimal comma and a dropped
  trailing zero are accepted ("$12,4" is 12.40); anything else, including
  NaN/Infinity, is refused, with the right amount named in the message.
- **Enter in the total field does not submit.** Otherwise, once the button
  unlocks, typing the total and pressing Enter would make controls 2 and 3 one
  keystroke. The first version used Alpine's `keydown.enter.prevent`, which
  fails before Alpine loads and without JavaScript. The reviewer's fix
  replaced it: the form's first submit button, its default button, is hidden
  and disabled, and HTML submits nothing through a disabled default button. A
  browser test with JavaScript switched off confirms it.
- **What was confirmed:** GET stores the shown order in
  `session["checkout"]["showing"]` (each line's candy, quantity, unit price,
  plus the total), and the page posts back its fingerprint (`shown`). A POST
  is refused with a notice if either differs from the order as it now stands,
  for example a price change or another tab showing another order. A valid
  POST stores `confirmed = {snapshot, at}`. T6 compares against the confirmed
  snapshot.
- **A stock cap or withdrawn candy while confirming** is a cart correction,
  which is a cart write, which clears checkout progress (D10). The customer is
  sent back to the warning, and the cart's notices go with them as messages,
  which the warning page now renders. (The first version dropped them; the
  reviewer found it.)
- **D9 superseded:** acknowledging the warning now redirects to
  `/checkout/confirm/`. Coming back to the warning after acknowledging shows
  "acknowledged" with a Continue link. Two T4 tests were updated to that
  behaviour: the redirect target, and the e2e path after Continue.

## D12. T6: placing an order is a manager method on `Order`

`Order.objects.place(user, snapshot, warning_acknowledged_at,
purchase_confirmed_at)` does the lock, the re-check, the writes and the stock
reduction in one `transaction.atomic()`. ADR 0003 puts business rules in
models, and this is the model's own invariant (an order matches what was
confirmed, and stock covers it). It raises `OrderChanged(candies)` naming what
differs; the view turns that into the cart-page message (UC-05 ext. 4a).
Alternatives: in the view (untestable without HTTP, and the view would then
own a transaction); in `shop/checkout.py` (that module is session state, and
this writes the database).

Other choices in T6:
- **Lock order:** candies are locked `ORDER BY pk`, so two orders over the same
  candies take locks in the same order and cannot deadlock.
- **`PROTECT` on `Order.user` and `OrderItem.candy`:** an order is a record. A
  candy that has been ordered is withdrawn with `is_published`, not deleted,
  and the admin's delete now refuses it. The data model gave no `on_delete`.
- **The receipt is a 404 for anyone but the owner**, not a 403.
- **Admin:** orders are view-only (no add, change or delete), because a placed
  order changes only through checkout, and payment and fulfilment are not
  built.
- **T5's interim "confirmed" record was removed** (`checkout.confirm`,
  `confirmed_order`, the "Confirmed. Placing orders is not built yet" state).
  A valid confirmation now places the order. T5's tests that asserted the
  record were updated to assert an order (or no order) instead; the
  refused-control and changed-order cases still refuse, now shown as "no order
  exists".
- **What is not tested:** two customers placing at the same moment. A test
  shows the `SELECT ... FOR UPDATE` on the candies is issued (with a negative
  control), but no test runs two transactions at once.

## D14. T6: one order per confirmation page (reviewer, Medium)

The reviewer found that a double-click places two orders. Both requests load
the session before either saves it, so both see the full cart; stock was taken
twice, and nothing can release it (the admin is read-only). My first write-up
(a questions.md entry) understated this as a two-tab race and proposed a unique
fingerprint per user, which would have blocked ordering the same thing twice.

Fixed:
- Every showing of the confirmation page gets a random token, stored with the
  shown order in the session and posted back.
- A POST whose token is not the one last shown is refused like a changed order.
- `Order.confirmation_token` is a unique UUID, and `place()` returns an order
  already placed with the token. It checks after taking the candy locks and
  before re-checking stock, so the second request of a double-click gets the
  first order back rather than a false "not placed" message.
- The same cart ordered again from a new showing is a new order (tested).

**Migrations:** the reviewer suggested folding the column into `0010`, but
`0010` was already applied to the dev database (dev.py migrates it), and
un-applying a migration is not something to do unattended. So it is additive
instead:
- `0011` adds the column nullable and gives each existing order its own UUID;
- `0012` makes it unique and required.

They are split so PostgreSQL never updates rows and alters the same table in one
transaction (pending deferred-trigger events). That risk is real: an ordinary
database test running both migrations in one transaction was refused by
PostgreSQL with exactly that error. `tests/integration/test_migration_order_confirmation_token.py`
therefore runs the deferred checks at the two points a real migrate commits.
With two pre-existing orders it gets two distinct tokens. Without 0011's data
step it fails with a NOT NULL violation (negative control).

The questions.md entry was removed, now that the question is settled in code.

## D13. T6: pylint R0903 on `OrderManager` left standing

`too-few-public-methods (1/2)`: the manager adds exactly one method, `place()`;
the rest of its public API is inherited from Django's `Manager`, which pylint
does not count. Refactor-class; the lint gate passes.

## D15. T7: slug URLs, unique names, and what each rule is enforced by

- **The slug is set once**, from the name, when a candy is first saved
  (`Candy.ensure_slug`, called from `clean()` and `save()`), and renaming does
  not change it, so a shared link keeps working. Collisions get `-2`, `-3`
  (two different names can slugify alike). A slug that would be digits alone
  gets a `candy-` prefix.
- **`/candy/<int:pk>/` keeps its own view** and answers 301 to the slug for a
  published candy. An unpublished or deleted one gets the same "no longer
  available" answer as its slug would, with no `Location` and without naming
  the slug: a redirect would disclose both the slug and that the candy exists.
- **Route order:** the number route is registered first. Since no slug is ever
  digits alone, the two cannot both match an address.
- **Migrations `0013`-`0014`** follow D14's pattern (add nullable and fill,
  then require), so rows are updated and the table altered in separate
  transactions. `0014` also makes `name` unique, and fails whole-or-nothing on
  a database holding two candies of one name. The dev database was checked
  first: 22 candies, no duplicate names, no colliding or empty slugs.
- **Migration `0013` holds a frozen copy of the slug rules**, rather than
  importing `unique_candy_slug`, because a migration must not change when the
  code does. Each copy has its own test.
- **A deleted test:** `test_candy_sharing_a_name_keep_a_stable_order` asserted
  the catalog's `("name", "pk")` tie-break using two candies of one name,
  which the unique constraint now makes impossible. The ordering property
  itself is still covered by `test_the_catalog_lists_candy_alphabetically`.
  The tie-break stays in the query, and the docstring now says why.

From the review (all four Low findings, and the nit):

- **`candy_list`'s docstring** said names are not unique. Corrected.
- **The prepopulated-fields test could not fail**: `'"slug"' in content`
  matched the field's own `name="slug"` attribute. It now asserts the admin's
  configuration and the element that carries it.
- **"Never digits alone" was only enforced in generation and forms.** A
  `CheckConstraint` (`candy_slug_is_not_all_digits`, migration `0015`,
  additive) now holds it in the database, as `flaw`'s non-blank check does.
  That constraint is also validated by `full_clean`, which runs before
  `save()`, so the slug is filled in `clean()` as well -- otherwise a form
  left blank reported a constraint violation the administrator never caused.
- **A cached 301 plus an editable slug** could pin a browser to an address
  that no longer exists. The slug is now read-only once the candy exists
  (`get_readonly_fields`), with `get_prepopulated_fields` returning nothing
  then, because the admin looks that field up on the form. The consequence,
  raised by the second review: a slug mistyped at creation cannot be corrected
  through any admin screen, and a candy that has been ordered cannot be deleted
  and recreated either (`OrderItem.candy` is PROTECT). Correcting one is a
  `manage.py shell` or data-migration operation, deliberately, since a cached
  301 cannot be recalled. Said so in the docstring.
- **Nit:** two browser tests now visit the slug address; the redirect has its
  own test.
