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

## D6. Visual reference: Pico CSS's look, rebuilt by hand

Research: read-only, about five minutes of the ~30 granted, 15:20–15:25.
Candidates, with what each needs to run:

| Candidate | URL | License | Needs | Verdict |
| --------- | --- | ------- | ----- | ------- |
| Cartzio (fashion store) | https://adminlte.io/blog/django-website-templates/ | paid | Tailwind v4, build | rejected: Tailwind, build, paid |
| Ecommerce Marketplace Template | https://github.com/Zadigo/ecommerce_marketplace_template | not stated | Bootstrap | rejected: Bootstrap |
| django-oscar storefront | https://github.com/django-oscar/django-oscar | BSD | Bootstrap (sandbox "built with Twitter's Bootstrap") | rejected: Bootstrap |
| Saleor storefront | https://adminlte.io/blog/django-website-templates/ | BSD | GraphQL + Next.js | rejected: React/Next build |
| CodeRed CMS, Vany, Incrave, Cuba, Vuexy | same list | free/paid | Bootstrap 5, build | rejected: Bootstrap |
| daisyUI, Flowbite, FlyonUI, SaaS Pegasus, Apex/Zenith (Tailwind + HTMX) | same list | MIT/paid | Tailwind, build | rejected: Tailwind |
| Wagtail bakerydemo | https://github.com/wagtail/bakerydemo | BSD-3 | Wagtail; front-end tooling config, CSS approach not stated | rejected: a CMS, and its CSS approach could not be confirmed from the page |
| **Pico CSS** | https://picocss.com/docs/color-schemes, https://picocss.com/docs/css-variables | MIT | nothing: plain CSS, no build | **chosen as the reference** |

Every Django-specific template on the lists found needs Bootstrap, Tailwind or
a JS build, which the stack rules out. Pico is not a Django template, but it is
what those sites' clean, card-based storefront look reduces to, and it runs on
plain CSS.

What was taken is the *look*: system font stack, generous spacing, quiet
bordered cards, one accent colour. Also the *mechanism* the human had already
settled: `data-theme` on `<html>` overriding `prefers-color-scheme`. **No Pico
code, variable names or values were copied.** The palette is this site's own
(a candy magenta/pink accent), chosen to pass the contrast check in both
themes.

## D7. Styling conventions set by T5

- **One stylesheet**, `shop/static/shop/site.css`, loaded from `base.html` via
  `{% static %}` (night-run §9.3). Colours are custom properties; the dark
  values are written twice, once under the media query (system) and once for
  `[data-theme="dark"]` (toggle), because CSS cannot share a rule block
  between a media query and an attribute selector without a preprocessor.
- **Theme JavaScript** is `shop/static/shop/theme.js` (the toggle) plus a
  six-line inline script in `<head>` that applies a stored choice before first
  paint. No Alpine: the toggle needs no reactivity, and vanilla keeps the theme
  working if the Alpine CDN is slow.
- **No-JS behaviour:** the toggle ships `hidden` and is revealed by theme.js;
  without it the page still follows the system setting. `[hidden]` is forced
  to `display: none !important`, because the toggle's own `display` rule had
  beaten the browser's default and shown the hidden button (caught by an e2e
  test).
- **No "back to system" control.** Once toggled, the stored choice wins until
  toggled again; clearing it needs clearing site data. Raised as Q3.
- **The sun/moon glyph** is CSS generated content with empty alt text
  (`content: "..." / ""`), so the button is named "Dark theme", not
  "☼ Dark theme" (a test asserts the name). Below 30rem only the glyph shows;
  the label stays in the accessibility tree.
- **Markup changes beyond adding classes**, none touching an element with a
  `data-testid`, role or heading:
  - the catalog price is wrapped in a `<span>` and the " — " separator
    dropped;
  - the toggle's label is a `<span>` inside its button;
  - `base.html` gained a `main_class` block;
  - `announcer.html`'s inline style became the `.visually-hidden` class.
  - A wrapper `<div>` briefly added around the empty-cart message was taken
    out again, because it moved a `data-testid` element.
- **Standalone links are controls.** Candy names on cards and cart lines and
  `.page-actions` links get a 44px tap box. The first version measured only
  buttons, inputs and header links; the reviewer found the body links at
  about 24px high, masked in the test by a long candy name that wrapped. The
  check now covers every link in `main`, and the fixture includes a one-word
  name.
- **Two columns on phones** (from `minmax(9.5rem, 1fr)`), wider cards from
  48rem. One card per screen made 22 candies a very long scroll.

## D8. The catalog is ordered by name in the view, and follows the database collation

- **Chosen:** `candy_list` uses `.order_by("name", "pk")`. The primary key
  breaks ties because names are not unique.
- **Rejected — `Meta.ordering`:** it adds a migration and an `ORDER BY` to
  every query, including the cart's `in_bulk` and the admin, for one page that
  needs it. The catalog is the only customer-facing list of candy.
- **Alphabetical, not "newest first" or by price:** no requirement names an
  order. Alphabetical is the least surprising, and one line to change.
- **Collation, recorded not fixed** (from the reviewer):
  - The order follows the database collation, which nothing sets. The local
    cluster is `Swedish_Sweden.1252`, where Å/Ä/Ö sort after Z; CI's
    `postgres:17` is probably `en_US.utf8`.
  - The cart sorts in Python by code point, so for mixed-case or non-ASCII
    names the two can disagree.
  - All 22 seeded names are ASCII Title Case, and the tests use names that sort
    the same under any collation, so nothing differs today or between local and
    CI.

## D9. Candy timestamps: rows older than 0007 got its run time, not NULL

- **What was intended:** migration `0007` added `created_at` (`auto_now_add`)
  and `updated_at` (`auto_now`) as *nullable*, so that rows older than the
  fields would hold NULL, "unknown", instead of an invented creation date.
- **What happened:** Django's schema editor fills an `auto_now`/`auto_now_add`
  column with `timezone.now()` for existing rows even when the column is
  nullable (`_effective_default`, `django/db/backends/base/schema.py`;
  `sqlmigrate shop 0007` shows `ADD COLUMN ... DEFAULT '<now>'` then
  `DROP DEFAULT`). Found by querying the dev database after the gate: all 22
  rows had one identical `created_at`. The first version's comment, data-model
  note and one test all said NULL; that test passed only because it set NULL
  by hand.
- **Corrected forward, not by editing `0007`:** `0007` was already applied to
  the development database, and undoing it means dropping columns, which an
  unattended run may not do. Migration `0008` makes both fields NOT NULL,
  matching the target model's "auto". It is safe because `0007` left no NULLs,
  and every ORM path sets both fields on save.
- **Consequence, stated plainly:** every candy that existed before `0007` has
  its run time in both fields, not its real creation time. In the dev
  database that is all 22 seeded candies (one shared timestamp). A test now
  migrates a pre-`0007` row forward and asserts exactly this.
- **Rejected — a data migration setting old rows to NULL:** it would need the
  fields to stay nullable forever to express "unknown", for data nobody reads
  yet.
