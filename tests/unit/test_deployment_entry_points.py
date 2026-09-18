"""What a deployment imports, and what it is told when configuration is missing.

`mysite/wsgi.py` and `mysite/asgi.py` are the objects a server loads; nothing in
the suite imported them, so a break there would first be seen by whoever
deployed it. The two `ImproperlyConfigured` guards in `mysite/settings.py` exist
to turn a missing environment variable into a sentence someone can act on, and
nothing checked that the sentence still appears (findings.md F3).

The guards are exercised through `test_settings.load_settings`, which runs
settings.py under a throwaway module name, so the settings this test run is
using are left alone.
"""
import pytest
from django.core.exceptions import ImproperlyConfigured

from tests.unit.test_settings import load_settings


def test_the_wsgi_application_can_be_imported():
    """What gunicorn, uWSGI or mod_wsgi loads."""
    from mysite import wsgi  # pylint: disable=import-outside-toplevel

    assert callable(wsgi.application)


def test_the_asgi_application_can_be_imported():
    """What uvicorn or daphne loads."""
    from mysite import asgi  # pylint: disable=import-outside-toplevel

    assert callable(asgi.application)


@pytest.mark.parametrize("variable", ["DJANGO_SECRET_KEY", "DATABASE_URL"])
def test_a_missing_setting_fails_at_import_saying_which_one_and_where_to_put_it(variable):
    """Without the variable, importing settings.py raises rather than limping on.

    The message is held to naming the variable and pointing at `.env`, not to
    its exact wording.
    """
    with pytest.raises(ImproperlyConfigured) as raised:
        load_settings(without=variable)

    message = str(raised.value)
    assert variable in message
    assert ".env" in message
