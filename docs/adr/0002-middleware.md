---
status: "proposed"
date: "2026-09-10"
decision-makers: "Martin Larsson"
---

# 0002. Choosing the middleware layer for authentication, session and cart handling

## Context and Problem Statement

Between incoming requests and the Django views sits the middleware stack responsible for session handling, CSRF protection, and authenticating the User model against protected actions like Order candy and Track order. The site also needs the current Cart attached to every request so cart state is available across pages. Which middleware components and authentication mechanism should handle this on a mobile-first site where users expect minimal friction (e.g. typing on small keyboards)?

## Decision Drivers

- Test what Django provides out of the box before adding dependencies
- Fast and simple for phone users
- Secure

## Considered Options

- Django built-in session-based authentication (SessionMiddleware + AuthenticationMiddleware)
- Token-based authentication with djangorestframework-simplejwt
- Social/federated login via django-allauth
- Passwordless authentication via one-time codes (email or SMS OTP / magic link)

## Decision Outcome

Chosen option: "Django built-in session-based authentication (SessionMiddleware + AuthenticationMiddleware)", because it is what Django ships with and it gives working auth, admin and CSRF protection with no third-party dependency. django-allauth extends `django.contrib.auth` rather than replacing it, so it can be added later without redoing this.

### Confirmation

Nothing enforces it currently, but there could be a use for adding CI jobs to enforce framework at a later stage.

## Pros and Cons of the Options

### Django built-in session-based authentication (SessionMiddleware + AuthenticationMiddleware)

- Good, because it ships with Django, requires no extra dependencies, and integrates directly with the Django admin and CSRF protection
- Good, because sessions work naturally with a server-rendered, template-based frontend
- Neutral, because it assumes cookie support, which is standard on mobile browsers but requires care if a native mobile app is added later
- Bad, because it does not natively support stateless API clients (e.g. a future mobile app) without additional token-based auth alongside it
- Bad, because it leaves customers typing a password on a mobile keyboard

### Token-based authentication with djangorestframework-simplejwt

- Good, because it is stateless and works well if the frontend is a SPA or a future native mobile app consuming a REST API
- Good, because tokens can carry expiry and scope, useful for controlling access to order-tracking endpoints
- Bad, because it adds complexity (token refresh flows, secure storage on the client) that is unnecessary if the frontend stays server-rendered
- Bad, because CSRF protection patterns differ from session-based auth, requiring extra care to avoid security gaps

### Social/federated login via django-allauth

- Good, because it removes the friction of typing a password on a mobile keyboard by letting customers sign in with an existing Google/Facebook/Apple account
- Good, because it handles email verification and password-reset flows out of the box
- Bad, because it introduces a dependency on third-party identity providers, which can fail or change their APIs independently of this project
- Bad, because some customers may be hesitant to link a social account for a candy-ordering site, reducing signup conversion

### Passwordless authentication via one-time codes (email or SMS OTP / magic link)

- Good, because it minimizes typing on mobile devices, improving the signup/login conversion for a mobile-first audience
- Good, because it avoids storing and managing passwords entirely, reducing certain security risks
- Bad, because it depends on reliable, timely email/SMS delivery, which introduces an external service dependency and potential delivery delays
- Bad, because it requires custom middleware/views to implement, as it is not a built-in Django feature

## More Information

django-allauth is deferred, not rejected — it is the likely addition if password entry on mobile proves to be a problem.
