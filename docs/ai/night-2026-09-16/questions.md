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
