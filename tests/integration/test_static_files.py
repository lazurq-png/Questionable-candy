"""Static files as a deploy serves them: collected, hashed, and served by WhiteNoise.

With DEBUG on -- which includes this suite -- Django serves the apps' static
files itself and WhiteNoise is not installed (settings.py). So this test sets
up what render.yaml's build command and DEBUG=False give production:
collectstatic into STATIC_ROOT with hashed names, and WhiteNoise in front.
"""

import re

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db

PRODUCTION_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}


@pytest.fixture(name="deployed_static")
def fixture_deployed_static(settings, tmp_path):
    """Production's storage and WhiteNoise, with collectstatic run into a temporary STATIC_ROOT."""
    settings.STATIC_ROOT = tmp_path / "staticfiles"
    settings.STORAGES = PRODUCTION_STORAGES
    settings.MIDDLEWARE = [
        settings.MIDDLEWARE[0],
        "whitenoise.middleware.WhiteNoiseMiddleware",
        *settings.MIDDLEWARE[1:],
    ]
    call_command("collectstatic", interactive=False, verbosity=0)
    return settings.STATIC_ROOT


def test_the_page_links_hashed_files_that_whitenoise_serves(deployed_static):
    """The stylesheet the page asks for exists, is served, and may be cached for good."""
    page = Client().get(reverse("candy_list")).content.decode()
    stylesheet = re.search(r'href="(/static/shop/site\.[0-9a-f]{12}\.css)"', page)
    assert stylesheet, "base.html should link site.css under its hashed name"

    response = Client().get(stylesheet.group(1))

    assert response.status_code == 200
    assert "max-age=315360000" in response.headers["Cache-Control"]
    assert (deployed_static / "staticfiles.json").exists()
