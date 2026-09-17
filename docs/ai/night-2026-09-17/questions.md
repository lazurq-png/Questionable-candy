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

## Q3. Is the header's account control acceptable on a phone?

- **The question:** the plan puts "Log in", "Sign up", the username, "My
  allergies" and "Log out" in the header. A phone header has room for about
  87px more, so T3 shows only "Log in" below 30rem (sign-up is linked from the
  login page), and logged in, puts "My allergies" and "Log out" in a menu
  opened from the username at every width (decisions.md D5).
- **Option (a):** keep it.
- **Option (b):** show "My allergies" and "Log out" directly on wide screens
  and use the menu only on phones.
- **Option (c):** a second header row on phones, so everything is visible.
- **Recommendation:** (a); look at it on a phone first.
- **In the meantime:** built as (a) and merged. Changing it touches only
  `account_nav.html` and `site.css`.

## Q4. Three records the run could not correct itself

T9 was given four sentences to fix. These turned up beside them and are outside
what it was asked to change:

- **`.claude/skills/night-run/SKILL.md` §9.3** says adding a CSS dependency
  "would fail `adr_guards.py` anyway". It would not: the guards read
  `requirements.txt`, and a CSS framework arrives through npm or a CDN tag.
  That sentence is a **rule**, not a premise, and T9's instruction was to leave
  §9's rules alone. ADR 0008's Confirmation section records the true position.
- **`.claude/skills/night-run/SKILL.md` §9.6** tells a run to raise the styling
  ADR as a question because none exists. ADR 0008 is now written (proposed), so
  the next run should be pointed at it instead — again, a rule to change, not a
  premise.
- **`README.md`** still says "Most of what the specification describes —
  accounts, orders, payment, the health warning and the triple-confirmation
  gate — is not built yet", and lists `shop` as the only app. After T1-T6 that
  is false: `accounts` exists, and so do orders, the warning and the
  confirmations. Payment is still not built.
- **Recommendation:** correct all three; the README one is the most visible.
- **In the meantime:** none was corrected. The two `SKILL.md` items are rules
  T9 was told to leave alone, and the README's stale Status paragraph is not
  one of T9's four sentences -- T9 edited README only to add ADR 0008 to its
  index.

## Q5. Two records still say the scripts have no integrity hash

T10a added them, but correcting a decision record was granted to T9 only, so
these were left alone:

- `docs/adr/0006-frontend-htmx-alpine.md:51` — "Bad, because CDN script tags
  are an unpinned runtime dependency on unpkg with no integrity hash and no
  offline story". The no-integrity-hash half is now false; the rest still
  holds.
- `docs/adr/0008-hand-written-css-themes.md`, under "Adopt a classless CSS
  framework from a CDN" — "they were pinned by version in the URL alone when
  this was written, with no integrity hash". True as written, and dated, but it
  reads as the current state.
- `docs/adr/0006-frontend-htmx-alpine.md`, Confirmation section — "Nothing
  pins the htmx or Alpine versions beyond the literal URLs in `base.html`; a
  CDN outage or a deleted version breaks the page at runtime with no
  build-time signal." The first clause is now false: each script is pinned to
  one file and its sha384. The outage half still holds. That section also lists
  what enforces the decision, and does not yet mention
  `tests/integration/test_script_integrity.py`.
- **Recommendation:** amend all three when ADR 0008 is accepted or rejected,
  since
  that decision touches the same paragraph. The exact wording: htmx and Alpine
  are pinned to one file each with a sha384 integrity hash (2026-09-17); what
  remains unsolved is availability and staleness.
- **In the meantime:** nothing edited; `decisions.md` D17 and this entry are
  the record.
