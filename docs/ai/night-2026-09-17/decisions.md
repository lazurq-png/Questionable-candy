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
