# Decisions — night-2026-09-16

Choices with consequences, and the options that lost. Obvious choices are
omitted. Decisions the human settled in the run request are in `plan.md` and
are not repeated here.

## D1. Unpublished and deleted candy share one 404 page

UC-03 ext. 2a: "Item unpublished or deleted: System shows 'no longer available'
and returns to the catalog."

- **Chosen:** render `candy_unavailable.html` with status 404 for both cases:
  the message plus a link back.
- **Rejected — redirect to the catalog with a flash message:** the explanation
  lives on a different page than the one requested, and a redirect answers 302
  for a URL that no longer has content.
- **Rejected — 410 Gone for deleted items:** a deleted row can't be told apart
  from one that never existed without keeping tombstones.
- **Rejected — 200 for unpublished items:** it would tell anyone probing ids
  that the row exists. The shared page does not name the candy.

## D2. The seed treats only text fields as fillable, and matches by name

- Settled by the human: fill "fields that are empty", never overwrite. For
  `price` and `stock`, 0 is a real value (a free sample, an out-of-stock item)
  rather than "empty", so only `description`, `flavor`, `flaw` and `image` are
  ever filled. Numbers on an existing row are never touched.
- Matching is by `name`, which the database does not enforce as unique. If a
  database ever holds two rows with one seeded name, `get_or_create` raises
  `MultipleObjectsReturned` and the whole seed rolls back (it runs in one
  transaction). Failing loudly was preferred over guessing which row to fill.
  Making names unique is an open product decision (parked in the run request).
- `Chili Mango Chews` is seeded with stock 0 on purpose: T3's stock validation
  has a real out-of-stock item to meet.

## D3. The cart's rules live in `shop/cart.py`, which is not a service layer

ADR 0003 and `.claude/rules/backend.md` put business logic in models and forms,
and rule out a service layer, repositories and `services.py`.

- **The constraint:** the human settled that the cart stays in the session, so
  there is no cart model to hold its rules (publication, stock caps, stale
  entries).
- **Rejected — the rules in `views.py`:** they would be spread across four
  views, which is exactly the "accumulating in views" the backend rule warns
  against.
- **Rejected — a `SessionCart` class with its own persistence API:** it starts
  to look like the repository abstraction the ADR declined.
- **Chosen:** `shop/cart.py`, a handful of plain functions over
  `request.session["shoppingcart"]`, the same kind of module as Django's own
  `contrib.messages` storage. It does no general ORM access for callers.
  Untrusted input is validated by `shop/forms.py` (`QuantityForm`) before it
  reaches `cart.py`, per the documented form layer. Raised by the reviewer; if a
  human sees it as the start of a service layer, it is small to fold into views.

## D4. Cart refusals answer 200, not 4xx

htmx swaps no 4xx response by default, so a refused add would do nothing
visible. UC-04 ext. 2a requires the refusal to be *said*.

- Every add answers 200 with a message: over stock, out of stock, and a candy
  unpublished or deleted since the page loaded.
- T1's test for an unpublished add asserted 404. That was a deliberate behaviour
  change, not a weakened test: it now asserts 200, the message, and that the
  session is unchanged. A deleted-candy twin was added.
- **Rejected — `htmx.config.responseHandling` to swap 4xx:** a global change to
  htmx behaviour made for one endpoint.
- The quantity input has no `min`/`max`. htmx runs HTML form validation before
  posting, so a `max` would block an over-stock quantity with the browser's own
  tooltip, and the server's cap and its message would never be reached.

## D5. One persistent live region, filled out of band

Messages that appear inside a freshly swapped element are not reliably announced
by screen readers. A live region is announced when its *content* changes, and
the element must already exist.

- `announcer.html` is included once in `base.html`, visually hidden with an
  inline style until the stylesheet exists (T5 moves it).
- Every cart response fills it with `hx-swap-oob="innerHTML"`, so the element is
  never replaced. Visible messages stay where the action happened.
- The Update button has a stable `id`, so htmx restores focus to it after the
  swap. A negative control showed focus is lost without the id. A removed line
  has no button to return to, and focus falls back to the page.
- An e2e test asserts the live region's text changes. Whether a screen reader
  actually speaks it has **not** been verified; no assistive technology is
  available to the run.
