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
