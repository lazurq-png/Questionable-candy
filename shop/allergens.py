"""The one allergen vocabulary: the EU's 14 major allergens.

Regulation (EU) No 1169/2011, Annex II, in its order. Both `Candy.allergens` and
`accounts.User.allergies` store the keys, so a customer's allergy and a candy's
allergen can be matched exactly (UC-07) -- free text would let "nuts" and
"tree nuts" miss each other.

A plain module rather than part of either app's models, so accounts can use it
without depending on the shop's models (docs/ai/night-2026-09-17/decisions.md).
"""

ALLERGENS = (
    ("gluten", "Cereals containing gluten"),
    ("crustaceans", "Crustaceans"),
    ("eggs", "Eggs"),
    ("fish", "Fish"),
    ("peanuts", "Peanuts"),
    ("soy", "Soybeans"),
    ("milk", "Milk"),
    ("tree-nuts", "Tree nuts"),
    ("celery", "Celery"),
    ("mustard", "Mustard"),
    ("sesame", "Sesame"),
    ("sulphites", "Sulphur dioxide and sulphites"),
    ("lupin", "Lupin"),
    ("molluscs", "Molluscs"),
)

# The column width for one key: room to spare over the longest (11 characters),
# so adding a key later need not alter the column.
KEY_LENGTH = 20


def names(keys):
    """The labels for `keys`, in the vocabulary's order, skipping unknown keys."""
    wanted = set(keys)
    return [label for key, label in ALLERGENS if key in wanted]
