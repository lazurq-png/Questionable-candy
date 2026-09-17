"""How a candy's slug is made from its name (night-2026-09-17 plan T7).

No database: `unique_candy_slug` asks a callable whether a slug is taken, so
the rules can be checked on their own, and migration 0013 can hold a frozen
copy of them.
"""
from shop.models import unique_candy_slug

FREE = set()


def taken_in(taken):
    """A `taken` callable over a set of slugs."""
    return lambda slug: slug in taken


def test_a_slug_is_the_name_in_lower_case_with_dashes():
    """The plain case: a name becomes its slug."""
    assert unique_candy_slug("Strawberry Cloud Marshmallows", taken_in(FREE)) == "strawberry-cloud-marshmallows"


def test_a_taken_slug_gets_the_next_free_number():
    """Two different names can slugify alike: "Sour Bricks" and "Sour-Bricks"."""
    taken = {"sour-bricks", "sour-bricks-2"}

    assert unique_candy_slug("Sour Bricks", taken_in(taken)) == "sour-bricks-3"


def test_a_name_of_digits_alone_is_prefixed():
    """/candy/123/ is the old number URL, so a slug of digits could never be reached."""
    assert unique_candy_slug("123", taken_in(FREE)) == "candy-123"


def test_a_name_with_nothing_to_slugify_still_gets_a_slug():
    """Punctuation alone leaves nothing to slugify."""
    assert unique_candy_slug("!!!", taken_in(FREE)) == "candy"


def test_a_very_long_name_is_cut_to_fit_the_column():
    """The column holds 220; the base is cut to 200 to leave room for a suffix."""
    slug = unique_candy_slug("Toffee " * 60, taken_in(FREE))

    assert len(slug) <= 200
    assert slug.startswith("toffee-toffee")
