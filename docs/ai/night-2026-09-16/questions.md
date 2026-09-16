# Questions — night-2026-09-16

The queue for a human. Each entry: the question, the options and their
consequences, a recommendation, and what was done in the meantime.

## Q1. Is `shop/cart.py` acceptable under ADR 0003's "no service layer"?

- **The question:** the session cart's rules live in a module of plain functions
  (decisions.md D3). The reviewer judged it not a service layer, but it is the
  shape a later `services.py` could grow from, and ADR 0003 is the human's call.
- **Option (a):** accept it, and say so in ADR 0003's confirmation. Cheap, and
  the rules stay in one tested place.
- **Option (b):** fold the functions into the cart views. Also cheap: about 80
  lines, 100% covered, no data involved. The views grow, which the backend rule
  also warns against.
- **Recommendation:** (a).
- **In the meantime:** built as (a) and merged. It is not provisional: moving
  the functions would change no behaviour and no test.

## Q2. An ADR for the site's styling and theme conventions

- **The question:** night-run §9.6 forbids writing an accepted ADR unattended,
  but T5 set real conventions: one hand-written stylesheet, the
  custom-property themes, and a small JavaScript file for the toggle
  (decisions.md D6, D7). ADR 0001's hand-written-CSS half is now exercised.
- **Option (a):** write "0008. Hand-written CSS with light and
  dark themes", accepted, recording D6 and D7, and mark ADR 0001's CSS half as
  exercised.
- **Option (b):** amend ADR 0006's confirmation section instead. Less
  ceremony, but ADR 0006 is about htmx and Alpine.
- **Recommendation:** (a).
- **In the meantime:** conventions recorded in `decisions.md`; no ADR written.

## Q3. Should visitors be able to go back to "follow the system setting"?

- **The question:** the toggle stores light or dark and that choice wins
  forever (settled decision 3 asked for an override, not a reset). A visitor
  who once clicked it no longer follows their operating system.
- **Option (a):** leave it. Two states, simplest.
- **Option (b):** a three-way control (system / light / dark), e.g. a small
  menu. More UI in a crowded phone header.
- **Option (c):** clicking the toggle back to the system's own theme removes
  the stored choice instead of storing it. Invisible, but no extra UI.
- **Recommendation:** (c), cheap and invisible; or (b) if the choice should be
  explicit.
- **In the meantime:** built as (a) and merged; not provisional, since (b) and
  (c) extend it rather than undo it.

## Q4. Records that still say "no CSS exists"

These are now false, and the protocol forbids editing some of them unattended.
Each wants a human's one-line correction:

- `docs/adr/0001-frontend.md:11` — "no CSS exists yet".
- `docs/adr/0006-frontend-htmx-alpine.md:31` — "no CSS of any kind exists yet".
- `.claude/skills/night-run/SKILL.md:858` — §9's premise, "no CSS of any kind
  exists in this project". §9 as a whole (its first discretionary task being
  "exploration, not CSS") assumes a site with no styling; a future run will
  start from a false picture.

The README's equivalent sentence was corrected in T5, since it is a status
description, not a decision record.
