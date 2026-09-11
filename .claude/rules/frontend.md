# Frontend Engineering Rules

Open this for frontend and UI work (components, styles, browser-facing state).

---

## Existing Design System

Before creating UI primitives, inspect the existing design system.

Reuse existing:

- buttons
- inputs
- modals
- dialogs
- cards
- tables
- menus
- typography
- layout primitives
- form components

Do not create duplicate primitives.

---

## Component Design

Keep components focused.

Prefer composition over giant components with many unrelated responsibilities.

Follow existing component boundaries.

Do not introduce a new component architecture for an isolated feature.

---

## State

Use the repository's existing state-management pattern.

Before introducing local/global state, determine:

- where the source of truth belongs
- whether the state can be derived
- whether server state already provides the value
- whether existing hooks/utilities solve the problem

Do not introduce a state-management dependency for a small isolated requirement.

---

## Data Fetching

Follow the existing data-fetching architecture.

Consider:

- loading
- success
- empty
- error
- retry
- stale data
- cancellation
- optimistic updates where relevant

Do not create ad-hoc fetch behavior when the application already has a standard mechanism.

---

## Accessibility

Preserve or improve:

- semantic HTML
- labels
- accessible names
- keyboard navigation
- focus behavior
- focus restoration
- error announcements
- disabled states
- appropriate ARIA usage

Do not use ARIA to compensate for avoidable semantic HTML problems.

---

## Responsive Behavior

For meaningful UI changes, consider:

- mobile
- tablet
- desktop
- long content
- empty states
- narrow containers
- keyboard interaction

Do not assume desktop-only behavior unless the product explicitly is desktop-only.

---

## UI Verification

After significant UI work:

1. run relevant tests
2. run typecheck
3. run lint/build
4. start the application if practical
5. inspect the actual rendered UI
6. test important interactions

Compilation does not prove UI correctness.

---

## Visual Consistency

Match existing:

- spacing
- typography
- colors
- borders
- shadows
- interaction states
- motion
- responsive behavior

Do not invent a second design language.

---

## Performance

Avoid unnecessary:

- rerenders
- expensive computations
- network requests
- large client bundles
- event listeners
- DOM work

Do not optimize prematurely.

Measure or identify a concrete reason before introducing complex optimization.
