# Questions — night-2026-09-17

The queue for a human. Each entry: the question, the options and their
consequences, a recommendation, and what was done in the meantime.

## Q1. A stale CSRF token on an htmx action does nothing visible

- **The question:** with JavaScript on, every cart action is an htmx POST. If
  the page's CSRF token has gone stale (the session expired, cookies cleared),
  Django answers 403 with the new "That form went stale" page, but htmx does not
  swap 4xx responses, so the customer presses + and nothing happens. The page
  from T1 only reaches customers without JavaScript.
- **Option (a):** leave it. Rare, and a reload fixes it.
- **Option (b):** a small `htmx:responseError` handler in base.html that, on
  403, replaces the page with the response (or reloads). About ten lines of
  JavaScript, but a new client-side behaviour.
- **Option (c):** configure htmx to swap 403 responses into a notice area.
- **Recommendation:** (b), as a supervised task; it is new behaviour, not a
  defect in T1.
- **In the meantime:** nothing built.

## Q2. What happens to free-text allergies stored before the vocabulary?

- **The question:** until T2, `User.allergies` accepted any text through the
  admin. Now only the EU 14 keys are valid, and the admin shows 14 checkboxes.
  A stored value outside them (e.g. "nuts") is invisible in the admin and lost
  on the next save of that user. The dev database has none. A database with
  real users might.
- **Option (a):** nothing, if no database with real users predates T2.
- **Option (b):** a one-off data migration that maps known spellings to keys
  and reports the rest for a person to resolve. Needs a mapping only a human
  can approve ("nuts" → tree-nuts or peanuts?).
- **Option (c):** show unknown stored values read-only above the checkboxes in
  the admin, so they are at least seen before a save drops them.
- **Recommendation:** (a) for now. There are no real users yet; revisit before
  any import of existing customer data.
- **In the meantime:** nothing built; decisions.md D4.
