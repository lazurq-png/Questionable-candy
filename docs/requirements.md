# Candy Ordering Website

Requirements Specification — Use Cases (Cockburn format)

|                  |                                                                       |
| ---------------- | --------------------------------------------------------------------- |
| **Status**       | Draft                                                                 |
| **Version**      | 0.2                                                                   |
| **Date**         | 2026-09-10                                                            |
| **System**       | Candy Ordering Website                                                |
| **Architecture** | See [`docs/adr/`](adr/) — this document is implementation-independent |

## 1. Introduction

### 1.1 Purpose

Specifies what the Candy Ordering Website must do, as use cases, independent of how it is built.

### 1.2 Scope

The customer-facing ordering flow — browsing, viewing, cart, checkout, payment — plus the three mandated safeguards: flaw disclosure, a health warning, and a triple-confirmation gate. Back-office tooling beyond Candy record entry is out of scope.

### 1.3 Actors

| Actor              | Role                                                            |
| ------------------ | --------------------------------------------------------------- |
| Customer           | Primary actor; browses, orders, and pays.                       |
| Site Administrator | Maintains the Candy catalog, including the required Flaw field. |
| Identity Provider  | Supporting actor; authenticates Customers (Google for UC-02).   |
| Payment Processor  | Supporting actor; authorizes and settles payment.               |

## 2. Features and Traceability

| Priority    | Feature                                            | Use Case | Depends on          |
| ----------- | -------------------------------------------------- | -------- | ------------------- |
| Must have   | Show candy in a professional interface             | UC-01    | —                   |
| Must have   | Log in with a Google account                       | UC-02    | —                   |
| Must have   | View a candy's description on click/tap            | UC-03    | UC-01               |
| Must have   | Add, edit, and remove candy in a cart              | UC-04    | UC-01, UC-03        |
| Must have   | Place an order and pay                             | UC-05    | UC-04, UC-07, UC-08 |
| Should have | Every candy discloses a significant flaw           | UC-06    | UC-03               |
| Should have | Warn about sugar intake or other risks at checkout | UC-07    | UC-05               |
| Should have | Triple-confirm before charging                     | UC-08    | UC-05, UC-07        |
| Could have  | Register or log in by a method other than Google   | UC-09    | UC-02               |

## 3. Cross-Cutting Requirements

- Layouts are mobile-first; the site is usable on phone and desktop.
- Authentication and payment occur over HTTPS; session cookies are secure and HTTPS-only.

## 4. Use Cases

### UC-01: Browse Candy Catalog

**Actor:** Customer
**Precondition:** At least one Candy item is published.
**Success guarantee:** Customer sees a mobile-first listing of available candy.

1. Customer opens the catalog page.
2. System retrieves the published Candy items.
3. System renders them as a mobile-first grid.

**Extensions**

- 2a. Nothing published: System shows a "nothing available right now" state rather than an empty page.

### UC-02: Log In with Google

**Actor:** Customer · **Supporting:** Google (OAuth 2.0 / OIDC)
**Precondition:** Customer is not authenticated.
**Success guarantee:** Customer holds an authenticated session backed by a local User record.

1. Customer selects "Log in with Google."
2. System redirects to Google's consent screen.
3. Customer authenticates and grants consent.
4. System exchanges the returned code for identity information.
5. System creates or matches a local User, starts a session, and returns Customer to their original destination.

**Extensions**

- 3a. Customer declines consent: no session is created; System returns to the login page.
- 5a. The Google email matches an existing local account: System links the two identities.

### UC-03: View Candy Description

**Actor:** Customer · **Supports:** UC-01
**Precondition:** Customer is viewing the catalog.
**Success guarantee:** Customer sees the item's full detail, including its disclosed flaw.

1. Customer selects a Candy item.
2. System renders name, description, price, and Flaw.
3. Customer returns to the catalog or adds the item to the Cart.

**Extensions**

- 2a. Item unpublished or deleted: System shows "no longer available" and returns to the catalog.

### UC-04: Manage Shopping Cart

**Actor:** Customer
**Precondition:** Customer is viewing the catalog or a detail page.
**Success guarantee:** The Cart reflects the chosen items, quantities, and current total.

1. Customer adds an item to the Cart.
2. System validates available stock.
3. System updates the Cart and shows the change.
4. Customer adds, edits a quantity, or removes an item — each repeating steps 2–3.
5. Customer opens the Cart to review all items and the total.

**Extensions**

- 2a. Requested quantity exceeds stock: System caps or rejects the addition and says so.
- 4a. Last item removed: System shows an empty-cart state.

### UC-05: Place Order and Pay

**Actor:** Customer · **Supporting:** Payment Processor
**Precondition:** Cart holds at least one available item; Customer is authenticated.
**Success guarantee:** A paid Order exists, the Cart is cleared, and the Order can be tracked.

1. Customer proceeds to checkout.
2. System shows the health warning and requires acknowledgment (UC-07).
3. System runs the triple-confirmation flow (UC-08).
4. System re-validates stock and price for every Cart item.
5. Customer submits payment details.
6. System charges the Payment Processor.
7. System creates the Order as "Paid," clears the Cart, and links to order tracking.

**Extensions**

- 2a/3a. Customer declines the warning or a confirmation: checkout halts; Cart unchanged.
- 4a. Stock or price changed since the item was added: checkout halts, System names the affected items and returns Customer to the Cart.
- 6a. Payment declined: System shows an error and leaves the Cart intact for a retry.

**Constraint:** Steps 2 and 3 must both complete before payment is attempted.

### UC-06: Disclose a Candy's Design Flaw

**Actor:** Customer (viewer) · **Supporting:** Site Administrator (author) · **Supports:** UC-03
**Precondition:** The Candy item has a Flaw recorded.
**Success guarantee:** Every detail view shows a flaw for that item.

1. Administrator records a Flaw when creating or editing a Candy item.
2. System stores it as a required attribute.
3. System renders the Flaw alongside the description on the detail view.

**Extensions**

- 2a. Saved with no Flaw: System rejects the save and prompts for one.

**Constraint:** Required at the data-model level, not only in the form, so it can never be silently omitted.

### UC-07: Warn of Sugar Intake and Other Risks

**Actor:** Customer · **Supports:** UC-05
**Precondition:** Customer has begun checkout.
**Success guarantee:** Customer has been shown a health warning and explicitly acknowledged it before payment.

1. System determines the warning content for the Cart's items (e.g. aggregate sugar, allergens).
2. System shows it as a distinct checkout step.
3. Customer acknowledges.
4. System records the acknowledgment and proceeds to UC-08.

**Extensions**

- 3a. No acknowledgment: checkout cannot proceed.

**Constraint:** Must appear before any payment fields, and must not be dismissible by accident — no self-vanishing toast.

### UC-08: Triple-Confirm Purchase Intent

**Actor:** Customer · **Supports:** UC-05
**Precondition:** Customer has acknowledged the health warning.
**Success guarantee:** Customer has confirmed the exact Cart contents three times before payment is charged.

1. System shows a first confirmation summarizing the Cart and total.
2. Customer confirms.
3. System shows a second, differently worded confirmation.
4. Customer confirms.
5. System shows a third confirmation immediately before charging.
6. Customer confirms; System charges payment.

**Extensions**

- 2a/4a/6a. Customer declines or leaves at any step: checkout halts there; Cart unchanged, no payment attempted.

**Constraint:** Each confirmation must be a distinct, deliberate action — not three clicks on an unchanged button.

### UC-09: Register or Log In by an Alternative Method

**Actor:** Customer
**Precondition:** Customer is not authenticated.
**Success guarantee:** Customer holds an authenticated account created without Google.

1. Customer selects a non-Google sign-in or sign-up option.
2. Customer supplies credentials or completes that provider's flow.
3. System creates and verifies the account.
4. System starts a session equivalent in capability to UC-02.

**Extensions**

- 2a. Email already registered under another method: System offers to link, or prompts login with the existing method.
- 3a. Email not verified: the account stays restricted until it is.

**Constraint:** Uses the same session and account model as UC-02, so later use cases need not distinguish login method.

## 5. Open Issues

- **Guest checkout** — undecided. UC-04 and UC-05 both change if it is supported (anonymous cart, checkout without an account).
- **Authentication timing** — is login required to browse, or only to check out?
- **Payment processor** — not selected (UC-05). Partial fulfillment on a failed re-validation is also undecided.
- **Flaw field structure** — free text, or category plus description (UC-06)?
- **Warning content** — fixed text or derived from per-item sugar/allergen data, and is the acknowledgment logged (UC-07)?
- **Confirmation layout** — three screens or three distinct controls on one (UC-08)?
- **Alternative login methods** — which are in scope for launch (UC-09)?
- **Catalog paging** — pagination or infinite scroll for a large catalog (UC-01)?
- **UC-02 vs. [ADR 0002](adr/0002-middleware.md)** — Google login is a Must have here, but ADR 0002 chooses Django's built-in session auth and defers django-allauth. One of the two needs to change.
