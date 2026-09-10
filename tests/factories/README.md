# Factories

Test data builders shared by the unit and integration stages — one factory per
model, composed rather than hard-coded so a schema change breaks one definition
instead of every fixture.

Covered by `factory_boy` (with Faker for realistic values). This is the reason
JSON fixtures were passed over: `Profile.allergies` and `Candy.allergens` use
`ArrayField`. See [ADR 0005](../../docs/adr/0005-testing.md).
