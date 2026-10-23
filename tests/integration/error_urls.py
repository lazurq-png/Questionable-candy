"""The site's URLs plus one view that always fails, for the 500 page tests.

Used through ``@pytest.mark.urls`` only, so the failing view never exists in the
real URLconf. Not collected by pytest: the name does not match ``test_*.py``.
"""
from django.urls import include, path


def boom(request):
    """Fail the way an unexpected bug would."""
    raise RuntimeError("deliberate failure, to render the 500 page")


urlpatterns = [
    path("boom/", boom),
    path("", include("mysite.urls")),
]
