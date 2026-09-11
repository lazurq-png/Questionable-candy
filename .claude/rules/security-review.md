# Security Review

Open this when changes touch security-sensitive behavior.

---

## Authentication

Check:

- identity verification
- session lifecycle
- token validation
- expiration
- revocation
- password handling
- account recovery

Never expose authentication secrets.

---

## Authorization

Check:

- server-side authorization
- resource ownership
- tenant isolation
- role boundaries
- privilege escalation
- administrative operations
- object-level access

A user being authenticated does not imply authorization.

---

## Input

Treat external input as untrusted.

Check:

- validation
- normalization
- injection
- path traversal
- unsafe deserialization
- file handling
- URL handling
- command execution

---

## Network

For external requests, consider:

- SSRF
- allowlists
- redirects
- DNS rebinding where relevant
- timeouts
- authentication
- response validation

Do not trust a user-controlled URL merely because it appears syntactically valid.

---

## Secrets

Never place:

- passwords
- API keys
- private keys
- tokens
- production credentials

in source code, tests, logs, comments, or committed configuration.

Use the project's approved secret-management mechanism.

---

## Sensitive Data

Minimize exposure of:

- personal data
- financial data
- authentication data
- private application state

Check logging, API responses, analytics, and error messages.

---

## Payments

For financial operations, consider:

- authorization
- idempotency
- duplicate requests
- transaction boundaries
- amount integrity
- currency
- webhook verification
- replay attacks
- auditability

Never trust client-provided financial values without server-side verification.

---

## Cryptography

Use established, reviewed cryptographic libraries and project primitives.

Do not invent cryptographic algorithms.

Do not weaken cryptographic settings merely to simplify development.

---

## Security Verification

For security-sensitive changes:

1. inspect the trust boundary
2. identify attacker-controlled inputs
3. identify privileged operations
4. verify authorization
5. inspect error behavior
6. inspect logging
7. inspect tests
8. review dependency changes
9. perform adversarial review

Report concrete findings with evidence.
