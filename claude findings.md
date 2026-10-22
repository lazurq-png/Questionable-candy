I analysed dev against master in Questionable-candy (I took “this project” to mean that repo, compared with what Xenocats went through). master has nothing dev lacks; it only holds the merge commits of PRs #1, #2 and #5. dev is 36 commits ahead: 106 files, +10,117 / −1,009 lines.

What dev adds

Shop features

Candy health data: sugar per 100 g and the EU’s 14 major allergens (migration 0009). The seed data is updated to match.
Accounts: log in, log out (POST only), sign up, a profile page where customers record their allergies, password change, and “My orders”.
Checkout, last three steps:
UC-07 is a health warning tied to a fingerprint of the cart. If the cart changes, the customer has to acknowledge it again.
UC-08 is a triple confirmation.
Placing the order locks the candy rows, re-checks price, stock and published state, and reduces stock in the same transaction. A one-time token per confirmation page stops a double submit from creating two orders (Order.objects.place). Migrations 0010–0012.
Slug URLs: each candy gets a slug address and names must be unique. The old /candy/<pk>/ links redirect permanently to the slug (0013–0015).
Error pages: 404, 500 and CSRF pages in the site’s style.
Caching and scripts: pages that show one customer’s cart, order or account are no longer cached by the browser. The htmx and Alpine scripts now load with integrity hashes. The theme toggle can hand control back to the system setting.
Order admin (unfinished): the last commit is titled “almost finished the admin pages, will need 1 more day”. Admins can create and edit orders, stock follows the order lines, deleting an order returns its stock, and the line editing has its own JS (order_lines.js).

Tooling and docs

The full test suite now fails below 95% coverage.
dev.py starts the local PostgreSQL cluster if it is down.
New ADR 0008 (hand-written CSS themes) and a docs/README.md with one row per ADR.
docs/overview.html is a plain-language page derived from the ADRs. adr_guards.py now fails CI if an ADR changes without that page being updated. It no longer counts test packages for ADR 0005.
The night-run skill was rewritten: a human writes the plan, the run pushes a branch per task, polls CI, and tries to fix failures.
About 50 new unit, integration and end-to-end test files.
Same kinds of issue Xenocats had
CI runs the full suite more often than needed
The same code gets tested 2–4 times. CI runs on pushes to master, dev and night-**, and also on PRs into master and dev.
A dev→master PR is tested, then the merge push to master tests the same code again. Xenocats fixed this with “CI on pull requests, not on the merge into main”, and by skipping a dev→master PR whose commit already passed on dev.
Every night-run task pushes its task branch and then the run branch, so each finished task is tested twice. The ci.yml comment admits this.
The concurrency group is per branch, so it doesn’t stop duplicate runs across branches.
There is no way to pick tests by change. CI always runs dev.py test: every suite, including Playwright, plus the coverage gate.
Locally, a task only counts as done after the full dev.py test (night-run SKILL.md:229, reviewer.md:32).
The 95% gate only applies to the full run, so the gate itself forces full runs.
test:unit, test:int and test:e2e exist, but nothing works out which tests a change can reach. That is what Xenocats added with test:affected.
No Playwright traces are uploaded when CI fails, so a CI-only failure can’t be investigated afterwards. Xenocats uploads them.
No permissions: block in ci.yml, so the CI token gets the repository’s default permissions. Xenocats restricts them.
Docs that contradict the code or each other
The ADR 0005 package-count check is gone, but three places still say it exists:
requirements.txt:7 says the stack is capped at 3–5 packages and that adr_guards.py enforces the count in CI.
requirements-dev.txt:5 mentions “the ADR 0005 package budget it enforces”.
.claude/README.md:31 calls the script the “ADR 0003 / 0005 guards”.
adr_guards.py, ADR 0005 itself and docs/README.md all say nothing counts packages any more.
References to night-run sections point at the wrong sections since the skill was renumbered:
ci.yml says provisional branches are described in “SKILL.md §4”; §4 is now “Ambiguity”, and branches are in §1.3.
docs/ai/README.md says the integration branch is in “§1.4”; that’s now §1.3 Branches (§1.4 is Remote).
The same file says the lint baseline is in “§1.3”; that’s now §1.6 Baseline.
Old night-run folders weren’t removed. docs/ai/README.md says to delete a run’s folder once its branch is merged. night-2026-09-15, -16 and -17 are all still there, and the first two are already in master.
.claude/README.md says CI runs “on push to master, dev and night-**” and leaves out the pull-request triggers.
Security and code quality
Nothing limits login or sign-up attempts. There is no throttle, lockout or rate limit anywhere, so the new accounts can be brute-forced. Xenocats added login and sign-up limits for this.
Order admin (the unfinished part):
Phantom stock (plausible, not tested). Stock rules depend on the status the admin is saving. If an order is changed from fulfilled back to pending, no stock is taken back, and deleting it later returns stock that already left the shop.
Error page instead of a message. The stock check in OrderItemFormSet.clean runs before the rows are locked. If a customer’s checkout takes the stock in between, the database refuses the write and the admin sees a server error page instead of “Not enough stock”.
Production security settings are missing: no SECURE_SSL_REDIRECT, HSTS or SECURE_PROXY_SSL_HEADER. Nothing is deployed yet, so this is low priority, but check --deploy will flag it.
dev.py writes migrations without asking. Every task runs makemigrations, so an agent running tests can silently create a migration file. This is documented as deliberate, and CI’s drift check catches it before merge.

The customer-facing code is otherwise careful. I found no unsafe HTML in templates or JS. Customers’ orders and profiles are always looked up through the signed-in user, so one customer can’t open another’s. Order placement is locked and safe against a double submit, and redirect targets after login or sign-up are checked.

What I ran: only python scripts/adr_guards.py, which passed (“no DRF; docs/overview.html is current”). Everything else is from reading the code. I didn’t run the tests or lint, so I can’t say whether the unfinished admin commit passes CI.
