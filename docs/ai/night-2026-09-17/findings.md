# Findings — night-2026-09-17 exploration

Written after every requested task (T1-T10b) was complete, verified, reviewed,
merged and pushed, under the plan's Exploration grant. Each finding carries
evidence, the command that would prove a fix, a size estimate, and a rank.
Ranked by what a customer or a reader loses, divided by cost.

Re-ranked after each task, because the code changes underneath.

**Built so far:** F1 (T12), F2 (T13), F4 (T14), F3 (T15). **Remaining, in order:** F5, F6.

## F1 — Pages showing a customer's cart, order or allergies can be cached

- **Category:** bug (privacy).
- **Evidence:** measured with a probe over real responses:

  | Page | `Cache-Control` | `Vary` |
  | ---- | --------------- | ------ |
  | `/shoppingcart/`, `/shoppingcart/panel/`, `/checkout/`, `/checkout/warning/`, `/accounts/allergies/` | *(absent)* | `Cookie` |
  | `/accounts/login/` | `max-age=0, no-cache, no-store, must-revalidate, private` | `Cookie` |

  The login page has it because Django wraps `LoginView` in `never_cache`, and
  `SignUpView` was given the same in T3 (`accounts/views.py`). Nothing else
  customer-specific has it.
- **Why it matters:** with no `Cache-Control`, a browser may serve these pages
  from its own cache after the customer logs out — the back button then shows
  another person, on a shared computer, the cart, the order under confirmation,
  or the allergies of the one before them. `Vary: Cookie` keeps a *shared*
  proxy from mixing customers up, but says nothing about the browser's own
  history cache.
- **Proof:** an integration test per view asserting `no-store` in
  `Cache-Control`. Control: removing the decorator from one view fails it.
- **Size:** small — a `@never_cache` on `shoppingcart`, `shoppingcart_panel`,
  `checkout`, `checkout_warning`, `checkout_confirm`, `order_received` and
  `accounts.my_allergies`, plus one test.
- **Deliberately not included:** the catalog and the detail page. They do show
  cart quantities, but they are the pages worth caching, and `Vary: Cookie`
  already separates a visitor with a session from one without. Changing that is
  a performance decision, not a defect fix.

## F2 — The confirmation page's controls are not linked to their error messages

- **Category:** accessibility.
- **Evidence:** after a refused submit, the warning page renders
  `<input type="checkbox" name="acknowledge" required aria-invalid="true"
  aria-describedby="id_acknowledge_error">` — Django adds both, because the
  template renders the widget (`{{ form.acknowledge }}`). The confirmation page
  writes its controls as raw HTML
  (`shop/templates/shop/checkout_confirm.html`), so the same refusal produces
  `<input type="checkbox" id="confirm-checked" name="checked_order">` and
  `<input type="text" id="confirm-typed-total" name="typed_total">` with
  neither attribute, though `<ul class="errorlist" id="id_checked_order_error">`
  and `id="id_typed_total_error"` sit right above them.
- **Why it matters:** a screen reader announces the field as valid and never
  reads the reason it was refused. This is the page where money is about to be
  spent, and where refusals are routine by design (three controls, each
  required).
- **Proof:** an integration test that a refused submit marks each control
  `aria-invalid="true"` and points `aria-describedby` at the id of its own
  error list. Control: revert the template to raw inputs and it fails.
- **Size:** small-medium — render the two inputs through the form while keeping
  the ids the Alpine bindings and labels use.

## F3 — The two deployment entry points and both settings guards are untested

- **Category:** test gap.
- **Evidence:** `python scripts/dev.py test` reports `mysite/asgi.py` and
  `mysite/wsgi.py` at **0%** (4 statements each, lines 10-16), and
  `mysite/settings.py` at 94%, missing lines 38 and 116 — the two
  `ImproperlyConfigured` raises for a missing `DJANGO_SECRET_KEY` and a missing
  `DATABASE_URL`.
- **Why it matters:** the two guards exist to turn a silent misconfiguration
  into a clear message, and nothing checks the message still appears. The
  entry-point modules are what a deployment imports; an import error there is
  invisible to a suite that never imports them.
- **Proof:** a test importing each application object, and two that reload the
  settings module with the variable removed and assert the message. Both fail
  if the guard or the module is broken.
- **Size:** small.

## F4 — README describes a site that no longer exists

- **Category:** documentation contradicting the code.
- **Evidence:** `README.md` still says "Most of what the specification
  describes — accounts, orders, payment, the health warning and the
  triple-confirmation gate — is not built yet", and lists `shop` as the only
  app. After T1-T6 there is an `accounts` app, orders, the health warning and
  the confirmations; only payment is still absent. Raised during T9 as
  questions.md Q4 because it was outside that task.
- **Why it matters:** the README is the first thing a reader meets, and it
  currently understates the project by six tasks.
- **Proof:** quoting the corrected sentences against the code; no test.
- **Size:** small. Exploration may not touch `docs/requirements.md`,
  `docs/data-model.md` or any ADR, and does not need to here.

## F5 — One duplicated block, carried as a lint message

- **Category:** duplicated code.
- **Evidence:** `pylint` R0801 between `tests/e2e/test_error_pages.py`
  `[21:26]` and `tests/e2e/test_theme.py` `[137:142]` — the five lines that set
  the viewport, emulate the colour scheme and store a theme choice. Recorded as
  decisions.md D1 during T1 and left ever since.
- **Why it matters:** least of the five. It is the only lint message this run
  introduced, so clearing it makes "no new messages" mean something again.
- **Proof:** the message disappears and both suites still pass.
- **Size:** small — one shared helper in `test_theme.py`.

## F6 — The pages left cacheable still name the signed-in customer

- **Category:** bug (privacy), the residual of F1.
- **Evidence:** `accounts/templates/accounts/partials/account_nav.html` renders
  `<span class="site-account-name">{{ user.get_username }}</span>` into the
  header of every page, the catalog and detail pages included, and their
  steppers show that customer's quantities. F1 deliberately left those two
  pages cacheable, so a Back navigation on a shared computer can still show the
  previous customer's username.
- **Why it matters:** the same class of exposure F1 closes, on the pages where
  it is least sensitive but most likely to be revisited. Found by T12's
  reviewer.
- **Options, none free:** `never_cache` on the catalog and detail pages, which
  gives up caching the two pages worth caching; or render the header's account
  control from JavaScript, which is a new mechanism and a flash of the wrong
  state; or accept it.
- **Proof:** whichever is chosen, an assertion on the header of a cached
  response.
- **Size:** small to build, but it is a performance-versus-privacy trade-off on
  the site's main pages -- closer to a product decision than the other
  findings, so it is **ranked last and may be one for the human**.

## Checked and found sound (not findings)

- **Query counts**, measured: catalog 1 query at both 12 and 24 candies (so no
  N+1 as the catalog grows), detail 1, cart 2, checkout 2, warning 3, admin
  order list 5.
- **A blank slug cannot reach the database**: `candy_slug_is_not_all_digits`
  (`slug ~ '\D'`) rejects the empty string too, so `save(update_fields=[...])`
  cannot leave a candy without one.
- **Form errors elsewhere**: every field Django renders itself already carries
  `aria-invalid` and `aria-describedby` (checked on sign-up).
