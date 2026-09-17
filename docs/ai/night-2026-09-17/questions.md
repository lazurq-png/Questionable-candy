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
