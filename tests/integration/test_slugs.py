"""Slug URLs and unique names (night-2026-09-17 plan T7).

The detail page moved to /candy/<slug>/; /candy/<pk>/ redirects so links that
were already shared keep working.
"""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.text import slugify

from shop.admin import CandyAdmin
from shop.management.commands.seed_candy import CANDIES
from shop.models import Candy
from tests.factories.candy_factory import CandyFactory

pytestmark = pytest.mark.django_db

POPUP = {"HX-Request": "true", "HX-Target": "candy-popup-contents"}


def by_pk(candy):
    """The candy's old number URL."""
    return reverse("candy_detail_by_pk", args=[candy.pk])


# --- The slug a candy gets ------------------------------------------------------

def test_a_new_candy_gets_its_slug_from_its_name():
    """Saving fills the slug, and the candy knows its own URL."""
    candy = Candy.objects.create(name="Maple Fudge Squares", price=Decimal("1.00"), flaw="Crumbles.")

    assert candy.slug == "maple-fudge-squares"
    assert candy.get_absolute_url() == "/candy/maple-fudge-squares/"


def test_two_names_that_slugify_alike_get_different_slugs():
    """The second gets a numbered slug, so both stay reachable."""
    first = Candy.objects.create(name="Sour Bricks", price=Decimal("1.00"), flaw="Hard.")
    second = Candy.objects.create(name="Sour-Bricks", price=Decimal("1.00"), flaw="Hard.")

    assert (first.slug, second.slug) == ("sour-bricks", "sour-bricks-2")


def test_a_slug_given_by_hand_is_kept():
    """An administrator's own slug is not overwritten."""
    candy = Candy.objects.create(name="Toffee", slug="chosen-by-hand", price=Decimal("1.00"), flaw="Sticks.")

    assert Candy.objects.get(pk=candy.pk).slug == "chosen-by-hand"


def test_renaming_a_candy_keeps_its_slug():
    """A shared link must not break because the name was tidied up."""
    candy = Candy.objects.create(name="Toffee", price=Decimal("1.00"), flaw="Sticks.")

    candy.name = "Buttery Toffee"
    candy.save()

    assert Candy.objects.get(pk=candy.pk).slug == "toffee"


def test_the_database_refuses_two_candies_of_one_name():
    """data-model section 3.3: names are unique."""
    CandyFactory(name="Sour Bricks")

    with pytest.raises(IntegrityError), transaction.atomic():
        Candy.objects.create(name="Sour Bricks", price=Decimal("1.00"), flaw="Hard.")


def test_the_database_refuses_two_candies_of_one_slug():
    """Two candies at one address could not both be shown."""
    CandyFactory(name="Sour Bricks")

    with pytest.raises(IntegrityError), transaction.atomic():
        Candy.objects.create(name="Something else", slug="sour-bricks", price=Decimal("1.00"), flaw="Hard.")


def test_every_seeded_candy_has_the_slug_of_its_name():
    """The seed's 22 candies get theirs from the same rules."""
    call_command("seed_candy", stdout=StringIO())

    assert Candy.objects.count() == len(CANDIES)
    for candy in Candy.objects.all():
        assert candy.slug == slugify(candy.name)


# --- The URLs -------------------------------------------------------------------

def test_the_detail_page_is_at_the_slug(client):
    """UC-03 at the new address."""
    candy = CandyFactory(name="Hollow Humbug", description="Looks solid. Is not.")

    response = client.get(f"/candy/{candy.slug}/")

    assert response.status_code == 200
    assert "Looks solid. Is not." in response.content.decode()


def test_the_old_number_url_redirects_permanently_to_the_slug(client):
    """Links shared before the move keep working, and say where the page went."""
    candy = CandyFactory(name="Hollow Humbug")

    response = client.get(by_pk(candy))

    assert response.status_code == 301
    assert response["Location"] == f"/candy/{candy.slug}/"


def test_the_popup_can_be_fetched_by_slug(client):
    """The detail popup's own request, by slug."""
    candy = CandyFactory(name="Hollow Humbug", description="Looks solid. Is not.")

    response = client.get(f"/candy/{candy.slug}/", headers=POPUP)

    assert response.status_code == 200
    content = response.content.decode()
    assert "<html" not in content
    assert "Looks solid. Is not." in content


@pytest.mark.parametrize("hide", ["unpublish", "delete"])
def test_a_candy_that_is_gone_answers_the_same_at_both_addresses_without_revealing_its_slug(client, hide):
    """UC-03 ext. 2a. A redirect would hand out the slug of a withdrawn candy."""
    candy = CandyFactory(name="Withdrawn Toffee")
    slug, url = candy.slug, by_pk(candy)
    if hide == "unpublish":
        Candy.objects.filter(pk=candy.pk).update(is_published=False)
    else:
        Candy.objects.filter(pk=candy.pk).delete()

    by_number = client.get(url)
    by_slug = client.get(f"/candy/{slug}/")

    assert by_number.status_code == by_slug.status_code == 404
    assert "no longer available" in by_number.content.decode()
    assert slug not in by_number.content.decode()
    assert "Location" not in by_number


def test_the_catalog_links_each_candy_by_slug(client):
    """Both the href and the popup's hx-get."""
    candy = CandyFactory(name="Hollow Humbug")

    content = client.get(reverse("candy_list")).content.decode()

    assert f'href="/candy/{candy.slug}/"' in content
    assert f'hx-get="/candy/{candy.slug}/"' in content
    assert f'href="/candy/{candy.pk}/"' not in content


# --- The admin -------------------------------------------------------------------

def test_the_admin_fills_the_slug_in_from_the_name(admin_client):
    """prepopulated_fields, which the admin's own JavaScript acts on.

    The page is checked for the element that carries that configuration, not
    for the words "slug" and "name", which the fields' own inputs contain
    whether or not anything prepopulates them.
    """
    assert CandyAdmin.prepopulated_fields == {"slug": ("name",)}

    content = admin_client.get(reverse("admin:shop_candy_add")).content.decode()

    assert 'id="django-admin-prepopulated-fields-constants"' in content
    assert "#id_slug" in content


def test_an_administrator_may_leave_the_slug_blank(admin_client):
    """Saved without JavaScript, the slug still comes from the name."""
    response = admin_client.post(reverse("admin:shop_candy_add"), {
        "name": "Ginger Snap Drops", "slug": "", "flaw": "Too hot.", "description": "", "flavor": "",
        "price": "1.00", "stock": "1", "is_published": "on", "image": "", "_save": "Save",
    })

    assert response.status_code == 302
    assert Candy.objects.get(name="Ginger Snap Drops").slug == "ginger-snap-drops"


def test_the_admin_refuses_a_slug_of_digits_alone(admin_client):
    """It would be read as the old number URL and never reach the candy."""
    response = admin_client.post(reverse("admin:shop_candy_add"), {
        "name": "Ginger Snap Drops", "slug": "12345", "flaw": "Too hot.", "description": "", "flavor": "",
        "price": "1.00", "stock": "1", "is_published": "on", "image": "", "_save": "Save",
    })

    assert response.status_code == 200
    assert "A slug needs a letter or a dash" in response.content.decode()
    assert not Candy.objects.exists()


def test_the_database_refuses_a_slug_of_digits_alone():
    """The form rejects one, but objects.create and update do not go through it."""
    with pytest.raises(IntegrityError), transaction.atomic():
        Candy.objects.create(name="Numbered", slug="12345", price=Decimal("1.00"), flaw="Odd.")

    candy = CandyFactory(name="Numbered Toffee")
    with pytest.raises(IntegrityError), transaction.atomic():
        Candy.objects.filter(pk=candy.pk).update(slug="12345")


def test_an_existing_candys_slug_cannot_be_changed_in_the_admin(admin_client):
    """/candy/<pk>/ answers a cacheable 301 to the slug, so the slug is set once."""
    candy = CandyFactory(name="Hollow Humbug")

    page = admin_client.get(reverse("admin:shop_candy_change", args=[candy.pk])).content.decode()
    response = admin_client.post(reverse("admin:shop_candy_change", args=[candy.pk]), {
        "name": "Hollow Humbug", "slug": "renamed", "flaw": "Hollow.", "description": "", "flavor": "",
        "price": "1.00", "stock": "1", "is_published": "on", "image": "", "_save": "Save",
    })

    assert 'name="slug"' not in page  # shown, not editable
    assert candy.slug in page
    assert response.status_code == 302
    assert Candy.objects.get(pk=candy.pk).slug == "hollow-humbug"
