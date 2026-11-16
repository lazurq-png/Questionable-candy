"""A customer can delete their own account, and read what the shop stores (audit 2026-11-10, S4).

The shop keeps allergies, which are health information, so leaving must be
possible without asking anyone. Deleting takes the customer's orders with it
(the owner's decision, 2026-11-10), returning unsent candy to stock.
"""

import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from shop.models import Order, OrderItem
from tests.factories.candy_factory import CandyFactory

pytestmark = pytest.mark.django_db

PASSWORD = "candy-Shop-2026!"
DELETE = "accounts:delete"


@pytest.fixture(name="visitor")
def fixture_visitor():
    """A browser-like client: CSRF enforced, token taken from a real page."""
    client = Client(enforce_csrf_checks=True)
    client.get(reverse("candy_list"))
    client.token = client.cookies["csrftoken"].value
    return client


def post(client, url, data=None):
    return client.post(url, {"csrfmiddlewaretoken": client.token, **(data or {})})


def make_user(username="ada", **fields):
    return get_user_model().objects.create_user(username=username, password=PASSWORD, **fields)


def log_in(client, username="ada"):
    response = post(client, reverse("accounts:login"), {"username": username, "password": PASSWORD})
    assert response.status_code == 302
    client.get(response["Location"])
    client.token = client.cookies["csrftoken"].value


def make_order(user, candy, quantity=2, status=Order.Status.PENDING):
    order = Order.objects.create(
        user=user, total_amount=candy.price * quantity, confirmation_token=uuid.uuid4(), status=status
    )
    OrderItem.objects.create(
        order=order, candy=candy, quantity=quantity, unit_price=candy.price, subtotal=candy.price * quantity
    )
    return order


def test_deleting_requires_login(visitor):
    response = visitor.get(reverse(DELETE))

    assert response.status_code == 302
    assert response["Location"] == f'{reverse("accounts:login")}?next={reverse(DELETE)}'


def test_the_page_says_what_goes_and_deletes_nothing_by_being_opened(visitor):
    ada = make_user()
    make_order(ada, CandyFactory(price=Decimal("2.50")))
    log_in(visitor)

    page = visitor.get(reverse(DELETE))

    assert "your 1 order" in page.content.decode()
    assert "no-store" in page.headers["Cache-Control"]
    assert get_user_model().objects.filter(username="ada").exists()


def test_the_right_password_deletes_the_account_and_signs_out(visitor):
    make_user(allergies=["milk"])
    bob = make_user("bob")
    log_in(visitor)

    response = post(visitor, reverse(DELETE), {"password": PASSWORD})

    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:deleted")
    assert list(get_user_model().objects.values_list("username", flat=True)) == [bob.username]
    landing = visitor.get(response["Location"])
    assert not landing.wsgi_request.user.is_authenticated
    assert "Your account and your orders were deleted." in landing.content.decode()


def test_a_wrong_password_deletes_nothing(visitor):
    make_user()
    log_in(visitor)

    response = post(visitor, reverse(DELETE), {"password": "not-the-password"})

    assert response.status_code == 200
    assert "That is not your password." in response.content.decode()
    assert get_user_model().objects.filter(username="ada").exists()


def test_the_customers_orders_go_too_and_unsent_candy_returns_to_stock(visitor):
    """Another customer's orders are untouched; a fulfilled order returns nothing."""
    ada = make_user()
    bob = make_user("bob")
    pending = CandyFactory(name="Sour Bricks", price=Decimal("2.00"), stock=3)
    sent = CandyFactory(name="Salt Coins", price=Decimal("1.00"), stock=4)
    make_order(ada, pending, quantity=2)
    make_order(ada, sent, quantity=1, status=Order.Status.FULFILLED)
    bobs = make_order(bob, pending, quantity=1)
    log_in(visitor)

    post(visitor, reverse(DELETE), {"password": PASSWORD})

    assert list(Order.objects.all()) == [bobs]
    pending.refresh_from_db()
    sent.refresh_from_db()
    assert pending.stock == 5
    assert sent.stock == 4


def test_a_staff_account_is_not_deleted_here(visitor):
    """It could be the last one able to sign in to the admin."""
    make_user(is_staff=True)
    log_in(visitor)

    response = post(visitor, reverse(DELETE), {"password": PASSWORD})

    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:profile")
    assert get_user_model().objects.filter(username="ada").exists()


def test_the_profile_links_to_deleting_and_to_the_privacy_page(visitor):
    make_user()
    log_in(visitor)

    page = visitor.get(reverse("accounts:profile")).content.decode()

    assert f'href="{reverse(DELETE)}"' in page
    assert f'href="{reverse("accounts:privacy")}"' in page


def test_the_privacy_page_is_open_to_everyone_and_names_what_is_stored(visitor):
    page = visitor.get(reverse("accounts:privacy"))

    assert page.status_code == 200
    content = page.content.decode()
    assert "Your allergies" in content
    assert "Delete my account" in content
    assert f'href="{reverse("accounts:privacy")}"' in visitor.get(reverse("accounts:signup")).content.decode()


def test_deleting_also_removes_the_login_records_kept_under_the_username(visitor):
    from axes.models import AccessAttempt, AccessLog

    make_user()
    log_in(visitor)
    AccessAttempt.objects.create(username="ada", ip_address="203.0.113.7", user_agent="x", failures_since_start=1)
    assert AccessLog.objects.filter(username="ada").exists()

    response = post(visitor, reverse(DELETE), {"password": PASSWORD})

    assert response.status_code == 302
    assert not AccessLog.objects.filter(username="ada").exists()
    assert not AccessAttempt.objects.filter(username="ada").exists()
