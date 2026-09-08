# Candy Ordering Website

Requirements Specification — Use Cases (Cockburn fully\-dressed format)

|  |  |
| --- | --- |
| **Status** | Draft |
| **Version** | 0\.1 |
| **Date** | 2026\-09\-08 |
| **System** | Candy Ordering Website |
| **Architecture** | Frontend: Django Templates \+ Tailwind CSS \+ HTMX \+ Alpine.js · Backend: Django \+ Django REST Framework · Auth: django\-allauth (social/federated) · Database: PostgreSQL |

## 1\. Introduction

### 1\.1 Purpose

This document specifies the functional requirements for the Candy Ordering Website as a set of use cases, following Alistair Cockburn's fully\-dressed use case format. It is intended to give developers, reviewers, and the site owner a shared, unambiguous description of what the system must do, independent of implementation detail.

### 1\.2 Scope

The scope covers the customer\-facing ordering flow — browsing, viewing, cart management, checkout, and payment — along with the mandatory content and safeguard behaviors the site owner has specified (product "flaw" disclosure, a health/safety warning, and a triple\-confirmation purchase gate). Administrative back\-office tooling beyond Candy record entry is out of scope for this revision.

### 1\.3 Actors

| Actor | Role |
| --- | --- |
| Customer | Primary actor for all customer\-facing use cases; browses, orders, and pays for candy. |
| Site Administrator | Maintains Candy catalog data, including required fields such as the product Flaw. |
| Google (OAuth Provider) | Supporting actor; authenticates Customers via django\-allauth's Google integration. |
| Payment Processor | Supporting actor; authorizes and settles payment for a placed Order. |

## 2\. Feature Prioritization

| Priority | Feature (as specified) | Use Case |
| --- | --- | --- |
| Must have | Show candy in a professional interface | UC\-01 |
| Must have | Log in with a Google account | UC\-02 |
| Must have | View a candy's description on click/tap | UC\-03 |
| Must have | Add, edit, and remove candy in a digital shopping cart | UC\-04 |
| Must have | Place an order and pay for candy | UC\-05 |
| Should have | Every candy must disclose a significant design/feature flaw | UC\-06 |
| Should have | Warn about sugar intake or other risks at checkout | UC\-07 |
| Should have | Triple\-confirm the customer wants to pay before charging | UC\-08 |
| Could have | Register or log in by a method other than Google | UC\-09 |

## 3\. Use Case Specifications

### 3\.1 UC\-01: Browse Candy Catalog

**Scope:** Candy Ordering Website
**Level:** User Goal
**Primary Actor:** Customer

**Stakeholders and Interests:**

- **Customer** — wants to browse the available candy quickly and pleasantly, on any device.
- **Site Owner** — wants the catalog to look professional and to showcase items in a way that encourages browsing.

**Preconditions:** At least one Candy item is published in the catalog.

**Success Guarantee:** The Customer is shown a mobile\-first, professionally styled listing of available candy.

**Main Success Scenario:**

1. Customer navigates to the site's catalog page.
2. System retrieves the published Candy items via the Django REST Framework API.
3. System renders the catalog as a mobile\-first grid using Tailwind CSS.
4. Customer browses the listing.

**Extensions:**

- **2a.** No candy is currently published: System shows a friendly "nothing available right now" state instead of an empty page.

**Special Requirements:** Layout must be mobile\-first; catalog filtering or sorting, where offered, should update via HTMX partials rather than a full page reload.

**Technology and Data Variations List:** Catalog data is served through the DRF API so the same data can later serve a native mobile client without change.

**Frequency of Occurrence:** Very high — the entry point to every other use case.

**Open Issues:** Pagination or infinite\-scroll strategy for a large catalog is not yet decided.

### 3\.2 UC\-02: Log In with Google

**Scope:** Candy Ordering Website
**Level:** User Goal
**Primary Actor:** Customer
**Supporting Actor:** Google (OAuth 2.0 provider)

**Stakeholders and Interests:**

- **Customer** — wants a fast, low\-friction login without creating a new password.
- **Site Owner** — wants verified identities with minimal account\-recovery support burden.

**Preconditions:** Customer is not currently authenticated; django\-allauth is configured with a Google OAuth application.

**Success Guarantee:** Customer holds an authenticated session backed by a local User record.

**Main Success Scenario:**

1. Customer selects "Log in with Google."
2. System (django\-allauth) redirects Customer to Google's consent screen.
3. Customer authenticates with Google and grants consent.
4. Google redirects back with an authorization code.
5. System exchanges the code for identity information and creates or matches a local User account.
6. System starts an authenticated session and returns Customer to their original destination.

**Extensions:**

- **3a.** Customer cancels or declines consent: System returns to the login page; no session is created.
- **5a.** The Google email matches an existing local account created another way: System links the identities per django\-allauth's account\-linking rules.

**Special Requirements:** Must use OAuth 2.0 / OpenID Connect; session cookies must be secure and HTTPS\-only.

**Technology and Data Variations List:** Implemented as a django\-allauth social\-account provider, so additional providers (UC\-09) can be added without restructuring this flow.

**Frequency of Occurrence:** High — a prerequisite for checkout unless guest checkout is later approved.

**Open Issues:** Is authentication required before browsing, or only before checkout?

### 3\.3 UC\-03: View Candy Description

**Scope:** Candy Ordering Website
**Level:** Subfunction (supports UC\-01)
**Primary Actor:** Customer

**Stakeholders and Interests:**

- **Customer** — wants enough detail to decide whether to buy.
- **Site Owner** — needs the mandated Flaw disclosure (UC\-06) shown alongside the description.

**Preconditions:** Customer is viewing the Candy catalog (UC\-01).

**Success Guarantee:** Customer sees the full detail view for the selected Candy item, including its disclosed flaw.

**Main Success Scenario:**

1. Customer clicks or taps a Candy item in the catalog.
2. System requests the item's detail data from the DRF API.
3. System renders the Candy Detail view as an HTMX partial, including name, description, price, and Flaw.
4. Customer reads the detail and may return to the catalog or add the item to the Cart.

**Extensions:**

- **2a.** The item no longer exists or is unpublished: System shows a "no longer available" message and returns Customer to the catalog.

**Special Requirements:** Must render as an HTMX partial swap, not a full page reload; must be legible on mobile.

**Technology and Data Variations List:** None beyond UC\-01.

**Frequency of Occurrence:** Very high.

**Open Issues:** None.

### 3\.4 UC\-04: Manage Shopping Cart

**Scope:** Candy Ordering Website
**Level:** User Goal
**Primary Actor:** Customer

**Stakeholders and Interests:**

- **Customer** — wants an accurate cart that's easy to adjust.
- **Site Owner** — wants stock and pricing kept accurate right up to checkout.

**Preconditions:** Customer is viewing the catalog or a Candy detail page.

**Success Guarantee:** The Cart accurately reflects the Customer's chosen items, quantities, and current totals.

**Main Success Scenario:**

1. Customer adds a Candy item to the Cart from the catalog or detail view.
2. System validates current stock via the DRF API.
3. System updates the Cart line item and returns an HTMX partial reflecting the change (e.g. item badge, cart drawer).
4. Customer repeats step 1, or edits a quantity, or removes an item — each producing the same validate\-and\-update cycle.
5. Customer opens the Cart page at any time to review all items and the running total.

**Extensions:**

- **2a.** Requested quantity exceeds available stock: System caps the quantity to what's available, or rejects the addition, and informs the Customer in the returned partial.
- **4a.** Customer removes the last item: System shows an empty\-cart state.

**Special Requirements:** All Cart mutations must be HTMX partial updates, consistent with the site's server\-rendered architecture.

**Technology and Data Variations List:** Cart state is persisted server\-side and exposed via the DRF API, so a future mobile client could reuse it.

**Frequency of Occurrence:** Very high.

**Open Issues:** Does the Cart persist across devices for a logged\-in Customer? Is an anonymous/guest cart supported?

### 3\.5 UC\-05: Place Order and Pay

**Scope:** Candy Ordering Website
**Level:** User Goal
**Primary Actor:** Customer
**Supporting Actor:** Payment Processor

**Stakeholders and Interests:**

- **Customer** — wants a fast, trustworthy checkout.
- **Site Owner** — wants no overselling and valid payment before fulfillment.
- **Payment Processor** — wants a valid, authorized transaction.

**Preconditions:** Cart contains at least one available item; Customer is authenticated (UC\-02 or UC\-09), or guest checkout is permitted.

**Success Guarantee:** A paid Order exists, the Cart is cleared, and the Customer can track the order.

**Main Success Scenario:**

1. Customer proceeds to checkout from the Cart.
2. System displays the health/safety warning (UC\-07) and requires acknowledgment.
3. System runs the triple\-confirmation flow (UC\-08).
4. System re\-validates stock and current pricing for every Cart item via the DRF API.
5. Customer submits payment details.
6. System processes payment through the configured Payment Processor.
7. System creates the Order with status "Paid," clears the Cart, and returns an HTMX partial confirmation with a link to order tracking.

**Extensions:**

- **4a.** An item's stock or price changed since it was added to the Cart: System halts checkout, identifies the affected item(s), and returns the Customer to the Cart to resolve before retrying.
- **6a.** Payment is declined or fails: System shows an error, leaves the Cart intact, and lets the Customer retry.
- **2a/3a.** Customer declines the warning or does not complete the triple confirmation: Checkout halts; Cart is unchanged.

**Special Requirements:** Payment must occur over HTTPS; the health\-warning (UC\-07) and triple\-confirmation (UC\-08) gates must both complete before payment is attempted.

**Technology and Data Variations List:** Order and checkout data are exposed via the DRF API so a future mobile client can reuse the same checkout flow.

**Frequency of Occurrence:** High — the site's core conversion event.

**Open Issues:** Which payment processor is used? Is partial fulfillment allowed if only some Cart items pass step 4?

### 3\.6 UC\-06: Disclose a Candy's Design Flaw

**Scope:** Candy Ordering Website
**Level:** Subfunction (supports UC\-03)
**Primary Actor:** Customer (viewer)
**Supporting Actor:** Site Administrator (content author)

**Stakeholders and Interests:**

- **Customer** — expects transparent, if satirical, information about each product.
- **Site Owner** — wants the site's professional\-with\-a\-dash\-of\-satire tone applied consistently.

**Preconditions:** The Candy item has a Flaw recorded in its catalog data.

**Success Guarantee:** Every Candy Detail view includes a clearly presented flaw or downside for that item.

**Main Success Scenario:**

1. Administrator records a Flaw (a design, taste, or other significant downside) when creating or editing a Candy item.
2. System stores the Flaw as a required attribute of the Candy record.
3. When a Customer views the Candy Detail page (UC\-03), System renders the Flaw prominently alongside the description.

**Extensions:**

- **2a.** Administrator attempts to save a Candy item with no Flaw specified: System rejects the save and prompts for one.

**Special Requirements:** The Flaw field must be enforced as required at the data\-model level (not just a UI convention), so it can never be silently omitted.

**Technology and Data Variations List:** None.

**Frequency of Occurrence:** Very high — renders on every product view.

**Open Issues:** Should the Flaw be free text, or a structured field (e.g. category plus description)?

### 3\.7 UC\-07: Warn of Sugar Intake and Other Risks at Checkout

**Scope:** Candy Ordering Website
**Level:** Subfunction (supports UC\-05)
**Primary Actor:** Customer

**Stakeholders and Interests:**

- **Customer** — wants awareness of sugar or other health considerations before purchasing.
- **Site Owner** — wants to act responsibly and limit liability.

**Preconditions:** Customer has begun checkout (UC\-05, step 2).

**Success Guarantee:** Customer has been shown a health/safety warning and has explicitly acknowledged it before payment proceeds.

**Main Success Scenario:**

1. System determines the relevant warning content for the items in the Cart (e.g. aggregate sugar content, other risk notes).
2. System displays the warning as a distinct step in the checkout flow.
3. Customer explicitly acknowledges the warning.
4. System records the acknowledgment and allows checkout to proceed to UC\-08.

**Extensions:**

- **3a.** Customer does not acknowledge the warning: Checkout cannot proceed past this step.

**Special Requirements:** The warning must be clearly legible and non\-dismissible\-by\-accident (not a toast that vanishes on its own), and must appear before any payment fields are shown.

**Technology and Data Variations List:** None.

**Frequency of Occurrence:** High — every checkout.

**Open Issues:** Is the acknowledgment logged for compliance purposes? Is the warning fixed text, or driven by per\-item data (e.g. allergy/sugar fields)?

### 3\.8 UC\-08: Triple\-Confirm Purchase Intent

**Scope:** Candy Ordering Website
**Level:** Subfunction (supports UC\-05)
**Primary Actor:** Customer

**Stakeholders and Interests:**

- **Customer** — wants protection from an accidental purchase.
- **Site Owner** — wants fewer erroneous orders, chargebacks, and support requests.

**Preconditions:** Customer has acknowledged the health warning (UC\-07).

**Success Guarantee:** Customer has confirmed intent to purchase the exact Cart contents three separate times before payment is charged.

**Main Success Scenario:**

1. System presents a first confirmation summarizing the Cart contents and total.
2. Customer confirms.
3. System presents a second, distinctly worded confirmation ("Are you sure you want to purchase these items?").
4. Customer confirms.
5. System presents a third and final confirmation immediately before charging payment.
6. Customer confirms, and System proceeds to charge payment (UC\-05, step 6).

**Extensions:**

- **2a/4a/6a.** Customer declines or navigates away at any confirmation step: Checkout halts at that step; the Cart is unchanged and no payment is attempted.

**Special Requirements:** Each confirmation must be a distinct, deliberate action — not three clicks on an unchanged button — for the safeguard to be meaningful.

**Technology and Data Variations List:** None.

**Frequency of Occurrence:** High — every checkout.

**Open Issues:** Should the three confirmations be three separate screens, or three distinct controls on one screen?

### 3\.9 UC\-09: Register or Log In by an Alternative Method

**Scope:** Candy Ordering Website
**Level:** User Goal
**Primary Actor:** Customer

**Stakeholders and Interests:**

- **Customer** — wants a login option if they don't use or trust a Google account.
- **Site Owner** — wants a broader, more accessible sign\-up funnel.

**Preconditions:** Customer is not currently authenticated.

**Success Guarantee:** Customer holds an authenticated account created by a method other than Google (e.g. email/password, or another federated provider).

**Main Success Scenario:**

1. Customer selects a non\-Google sign\-in or sign\-up option.
2. Customer supplies the required credentials, or completes that provider's OAuth flow.
3. System (django\-allauth) creates and verifies the account.
4. System starts an authenticated session, equivalent in capability to UC\-02.

**Extensions:**

- **2a.** The email address is already registered under a different method: System offers to link accounts or prompts login with the existing method.
- **3a.** Email verification is not completed: The account remains restricted until verification succeeds.

**Special Requirements:** Must use the same django\-allauth session/account model as UC\-02, so downstream use cases (Cart, Checkout) need not distinguish login method.

**Technology and Data Variations List:** django\-allauth already supports multiple social providers and local accounts, so this extends UC\-02's existing provider configuration rather than requiring new architecture.

**Frequency of Occurrence:** Low to medium — a secondary path.

**Open Issues:** Which alternative methods are actually in scope for launch (plain email/password only, or additional OAuth providers)? Confirmed as a "could have," not required for initial launch.

## 4\. Traceability Matrix

| Use Case | Feature | Priority | Depends On |
| --- | --- | --- | --- |
| UC\-01 | Browse Candy Catalog | Must have | — |
| UC\-02 | Log In with Google | Must have | — |
| UC\-03 | View Candy Description | Must have | UC\-01 |
| UC\-04 | Manage Shopping Cart | Must have | UC\-01, UC\-03 |
| UC\-05 | Place Order and Pay | Must have | UC\-04, UC\-07, UC\-08 |
| UC\-06 | Disclose a Candy's Design Flaw | Should have | UC\-03 |
| UC\-07 | Warn of Sugar Intake and Other Risks | Should have | UC\-05 |
| UC\-08 | Triple\-Confirm Purchase Intent | Should have | UC\-05, UC\-07 |
| UC\-09 | Register or Log In by an Alternative Method | Could have | UC\-02 |

## 5\. Assumptions and Open Issues

- Guest checkout (ordering without an account) is not yet decided; several use cases above assume it may or may not be supported.
- The specific Payment Processor for UC\-05 has not been selected.
- The structure of the Flaw field (UC\-06) and the source of warning content (UC\-07) are open content\-modeling questions, not just UI questions.
- The full requirements set assumes the architecture already decided elsewhere: Django Templates \+ Tailwind CSS \+ HTMX \+ Alpine.js on the frontend, Django \+ Django REST Framework as an API\-first backend, django\-allauth for social/federated login, and PostgreSQL as the database.
