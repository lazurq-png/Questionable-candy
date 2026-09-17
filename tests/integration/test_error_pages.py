"""The error pages a customer sees with DEBUG off: 404, 500 and the CSRF 403.

DEBUG is set off explicitly in each test rather than trusted to be off, because
with it on Django shows its debug pages and none of these templates is used.
"""
import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _template_names(response):
    return [template.name for template in response.templates]


def test_an_unknown_url_shows_the_404_page(client, settings):
    """A URL nothing matches gets the site's own page, with a way back."""
    settings.DEBUG = False

    response = client.get("/no-such-page/")

    assert response.status_code == 404
    assert "404.html" in _template_names(response)
    content = response.content.decode()
    assert "This page melted away" in content
    assert f'href="{reverse("candy_list")}"' in content


@pytest.mark.urls("tests.integration.error_urls")
def test_an_unhandled_error_shows_the_500_page_without_touching_the_database(
    settings, django_assert_num_queries
):
    """The 500 page must render when whatever failed was the database.

    Asserting zero queries is what holds it to that: a tag or include added to
    500.html that reads the database would fail here, rather than failing the
    one time the page is needed.
    """
    settings.DEBUG = False
    failing_client = Client(raise_request_exception=False)

    with django_assert_num_queries(0):
        response = failing_client.get("/boom/")

    assert response.status_code == 500
    content = response.content.decode()
    assert "Our candy machine jammed" in content
    assert f'href="{reverse("candy_list")}"' in content


def test_a_post_that_fails_the_csrf_check_shows_the_stale_form_page(settings):
    """A plain form post with no token -- a page left open too long, say.

    Django's own failure page explains the check to a developer, and its
    `reason` is not something a customer can act on, so it must not appear.
    """
    settings.DEBUG = False
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post(reverse("add_to_shoppingcart", args=[1]))

    assert response.status_code == 403
    assert "403_csrf.html" in _template_names(response)
    content = response.content.decode()
    assert "That form went stale" in content
    assert "Reload the page and try again" in content
    assert "CSRF cookie not set" not in content
    assert f'href="{reverse("candy_list")}"' in content
