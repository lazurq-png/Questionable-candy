"""Orders without payment: UC-05 steps 4 and 7 (night-2026-09-17 plan T6).

`Order.objects.place` is tested directly for what can only happen in the
moment between confirming and placing -- a price, stock or publication change
-- and through the view for what the customer sees.
"""
import uuid
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.models import ProtectedError
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from shop.checkout import SESSION_KEY, order_snapshot, snapshot_fingerprint
from shop.cart import Line
from shop.models import Candy, Order, OrderChanged, OrderItem
from tests.factories.candy_factory import CandyFactory
from tests.integration.test_checkout_confirm import confirm
from tests.integration.test_checkout_warning import acknowledge, add, browser

pytestmark = pytest.mark.django_db

ACKNOWLEDGED = datetime(2026, 9, 17, 20, 0, tzinfo=dt_timezone.utc)
CONFIRMED = datetime(2026, 9, 17, 20, 5, tzinfo=dt_timezone.utc)


@pytest.fixture(name="ada")
def fixture_ada():
    """A customer."""
    return get_user_model().objects.create_user(username="ada", password="x")


@pytest.fixture(name="candies")
def fixture_candies():
    """Two candies in stock."""
    return (
        CandyFactory(name="Toffee", price=Decimal("3.00"), stock=5),
        CandyFactory(name="Drops", price=Decimal("5.00"), stock=2),
    )


def snapshot_of(*pairs):
    """What the confirmation page would have shown for (candy, quantity) pairs."""
    lines = [Line(candy, quantity) for candy, quantity in pairs]
    return order_snapshot(lines, sum((line.total for line in lines), Decimal("0.00")))


def place(user, snapshot, token=None):
    """Place with fixed acknowledgment and confirmation times, from a new page unless `token`."""
    return Order.objects.place(user, snapshot, ACKNOWLEDGED, CONFIRMED, token or uuid.uuid4())


# --- Order.objects.place --------------------------------------------------------

def test_placing_records_the_order_its_lines_at_confirmed_prices_and_reduces_stock(ada, candies):
    """UC-05 step 7: a pending order, price snapshots, and stock taken."""
    toffee, drops = candies

    order = place(ada, snapshot_of((toffee, 2), (drops, 2)))

    assert order.user == ada
    assert order.status == Order.Status.PENDING
    assert order.total_amount == Decimal("16.00")
    assert order.warning_acknowledged_at == ACKNOWLEDGED
    assert order.purchase_confirmed_at == CONFIRMED
    assert order.paid_at is None
    items = {item.candy.name: item for item in order.items.all()}
    assert (items["Toffee"].quantity, items["Toffee"].unit_price, items["Toffee"].subtotal) == (
        2, Decimal("3.00"), Decimal("6.00"))
    assert (items["Drops"].quantity, items["Drops"].subtotal) == (2, Decimal("10.00"))
    assert Candy.objects.get(pk=toffee.pk).stock == 3
    assert Candy.objects.get(pk=drops.pk).stock == 0


def test_placing_locks_the_candies_it_checks(ada, candies):
    """The re-check and the stock reduction happen under a row lock.

    Two customers placing at once is not reproduced here; this shows the lock
    is requested, which is what makes the check and the reduction one step.
    """
    with CaptureQueriesContext(connection) as queries:
        place(ada, snapshot_of((candies[0], 1)))

    locking = [q["sql"] for q in queries.captured_queries if "FOR UPDATE" in q["sql"]]
    assert len(locking) == 1
    assert '"shop_candy"' in locking[0]


def test_the_same_confirmation_page_placed_twice_is_one_order(ada, candies):
    """The second placing returns the first order, even though its stock is now gone."""
    _, drops = candies  # stock 2
    snapshot = snapshot_of((drops, 2))
    token = uuid.uuid4()

    first = place(ada, snapshot, token)
    second = place(ada, snapshot, token)

    assert second == first
    assert Order.objects.count() == 1
    assert Candy.objects.get(pk=drops.pk).stock == 0


def test_two_confirmation_pages_for_the_same_cart_are_two_orders(ada, candies):
    """Ordering the same thing again later is a new order, not a duplicate."""
    toffee, _ = candies
    snapshot = snapshot_of((toffee, 1))

    place(ada, snapshot)
    place(ada, snapshot)

    assert Order.objects.count() == 2
    assert Candy.objects.get(pk=toffee.pk).stock == 3


def test_the_database_refuses_two_orders_with_one_confirmation_token(ada, candies):
    """The token is unique below place(), too."""
    token = place(ada, snapshot_of((candies[0], 1))).confirmation_token

    with pytest.raises(IntegrityError), transaction.atomic():
        Order.objects.create(user=ada, total_amount=Decimal("1.00"), confirmation_token=token)


def test_a_later_price_change_does_not_change_a_placed_order(ada, candies):
    """The unit price is a snapshot (data-model section 3.7)."""
    toffee, _ = candies
    order = place(ada, snapshot_of((toffee, 1)))

    Candy.objects.filter(pk=toffee.pk).update(price=Decimal("9.99"))

    assert order.items.get().unit_price == Decimal("3.00")


@pytest.mark.parametrize("change", [
    {"price": Decimal("3.50")},
    {"stock": 1},
    {"is_published": False},
], ids=["price", "stock", "unpublished"])
def test_anything_changed_since_confirming_stops_the_order_with_nothing_written(ada, candies, change):
    """UC-05 step 4 and ext. 4a: the affected candy is named; no order, stock untouched."""
    toffee, drops = candies
    snapshot = snapshot_of((toffee, 2), (drops, 1))
    Candy.objects.filter(pk=toffee.pk).update(**change)

    with pytest.raises(OrderChanged) as changed:
        place(ada, snapshot)

    assert changed.value.candies == ["Toffee"]
    assert not Order.objects.exists()
    assert not OrderItem.objects.exists()
    assert Candy.objects.get(pk=drops.pk).stock == 2


def test_a_candy_deleted_since_confirming_stops_the_order(ada, candies):
    """Deleted rather than withdrawn: there is no name left to give."""
    toffee, drops = candies
    snapshot = snapshot_of((toffee, 1), (drops, 1))
    Candy.objects.filter(pk=drops.pk).delete()

    with pytest.raises(OrderChanged) as changed:
        place(ada, snapshot)

    assert changed.value.candies == ["a candy that is no longer sold"]
    assert not Order.objects.exists()


def test_a_snapshot_whose_lines_do_not_add_up_to_its_total_is_refused(ada, candies):
    """A programming error, not a customer's change: nothing is written."""
    snapshot = {**snapshot_of((candies[0], 1)), "total": "99.00"}

    with pytest.raises(ValueError):
        place(ada, snapshot)

    assert not Order.objects.exists()


def test_the_database_refuses_an_item_whose_subtotal_is_not_quantity_times_price(ada, candies):
    """The stored subtotal (data-model section 3.7) can never disagree with its parts."""
    order = place(ada, snapshot_of((candies[0], 1)))

    with pytest.raises(IntegrityError), transaction.atomic():
        OrderItem.objects.create(order=order, candy=candies[1], quantity=2, unit_price=Decimal("5.00"),
                                 subtotal=Decimal("9.00"))


def test_the_database_refuses_an_item_of_zero(ada, candies):
    """PositiveIntegerField allows 0; the check constraint does not."""
    order = place(ada, snapshot_of((candies[0], 1)))

    with pytest.raises(IntegrityError), transaction.atomic():
        OrderItem.objects.create(order=order, candy=candies[1], quantity=0, unit_price=Decimal("5.00"),
                                 subtotal=Decimal("0.00"))


def test_an_ordered_candy_and_a_customer_with_orders_cannot_be_deleted(ada, candies):
    """An order is a record of what was bought, and by whom."""
    place(ada, snapshot_of((candies[0], 1)))

    with pytest.raises(ProtectedError):
        candies[0].delete()
    with pytest.raises(ProtectedError):
        ada.delete()


# --- Through checkout ------------------------------------------------------------

@pytest.fixture(name="confirming")
def fixture_confirming(ada, candies):
    """Ada with 2 Toffee and 1 Drops ($11.00), the warning acknowledged, the confirmation page open."""
    client = browser(ada)
    add(client, candies[0], times=2)
    add(client, candies[1])
    acknowledge(client)
    client.get(reverse("checkout_confirm"))
    return client


def test_placing_through_checkout_empties_the_cart_and_shows_the_receipt(confirming):
    """UC-05 step 7: paid is not possible yet, and the receipt says nothing was charged."""
    acknowledged_at = confirming.session[SESSION_KEY]["warning"]["at"]

    response = confirm(confirming)

    order = Order.objects.get()
    assert response["Location"] == reverse("order_received", args=[order.pk])
    assert order.warning_acknowledged_at == datetime.fromisoformat(acknowledged_at)
    assert order.purchase_confirmed_at >= order.warning_acknowledged_at
    assert confirming.session["shoppingcart"] == {}
    assert SESSION_KEY not in confirming.session
    receipt = confirming.get(response["Location"]).content.decode()
    assert f"Order #{order.pk} received" in receipt
    assert "Payment isn't connected yet, so nothing has been charged." in receipt
    assert receipt.count('data-testid="order-line"') == 2
    assert '<span data-testid="order-total">$11.00</span>' in receipt
    assert '<span data-testid="order-status">Pending</span>' in receipt


def test_submitting_the_confirmation_twice_places_one_order(confirming):
    """One after the other: the second submit finds an empty cart."""
    first = confirm(confirming)
    resubmitted = {"csrfmiddlewaretoken": confirming.token, "checked_order": "on",
                   "typed_total": "11.00", "place_order": "yes", "shown": "x", "token": "x"}

    second = confirming.post(reverse("checkout_confirm"), resubmitted)

    assert first.status_code == 302
    assert second["Location"] == reverse("shoppingcart")
    assert Order.objects.count() == 1


def test_a_double_click_whose_two_submits_both_see_the_full_cart_places_one_order(confirming, candies):
    """The race a double-click makes: the second request loaded the session before
    the first saved it, so it still holds the full cart and the same page's token.
    Reproduced by putting that session back before submitting again.
    """
    session = confirming.session
    before = {"shoppingcart": dict(session["shoppingcart"]), SESSION_KEY: dict(session[SESSION_KEY])}
    data = {"csrfmiddlewaretoken": confirming.token, **{
        "checked_order": "on", "typed_total": "11.00", "place_order": "yes",
        "shown": snapshot_fingerprint(before[SESSION_KEY]["showing"]), "token": before[SESSION_KEY]["token"],
    }}

    first = confirming.post(reverse("checkout_confirm"), data)
    session = confirming.session
    session.update(before)
    session.save()
    second = confirming.post(reverse("checkout_confirm"), data)

    order = Order.objects.get()
    assert first["Location"] == second["Location"] == reverse("order_received", args=[order.pk])
    assert Candy.objects.get(pk=candies[0].pk).stock == 3  # 5 - 2, once
    assert Candy.objects.get(pk=candies[1].pk).stock == 1  # 2 - 1, once


def test_a_change_in_the_moment_before_placing_keeps_the_cart_and_names_the_candy(confirming, monkeypatch):
    """UC-05 ext. 4a through the view: the race place() guards against, simulated."""
    def changed(*args, **kwargs):
        raise OrderChanged(["Toffee"])
    monkeypatch.setattr(Order.objects, "place", changed)
    cart_before = dict(confirming.session["shoppingcart"])

    response = confirm(confirming)

    assert response["Location"] == reverse("shoppingcart")
    assert confirming.session["shoppingcart"] == cart_before
    page = confirming.get(response["Location"]).content.decode()
    assert "Your order was not placed, because Toffee changed just now." in page


def test_a_receipt_is_only_for_the_customer_who_placed_the_order(ada, candies):
    """Another customer's order number is not found; anonymous visitors log in first."""
    order = place(ada, snapshot_of((candies[0], 1)))
    url = reverse("order_received", args=[order.pk])
    bob = get_user_model().objects.create_user(username="bob", password="x")

    assert browser(bob).get(url).status_code == 404
    assert browser().get(url)["Location"] == f'{reverse("accounts:login")}?next={url}'
    assert browser(ada).get(url).status_code == 200


# --- Admin -----------------------------------------------------------------------

def test_orders_are_visible_but_read_only_in_the_admin(admin_client, ada, candies):
    """A placed order is a record: listed and viewable, never added, edited or deleted."""
    order = place(ada, snapshot_of((candies[0], 2)))

    assert admin_client.get(reverse("admin:shop_order_changelist")).status_code == 200
    detail = admin_client.get(reverse("admin:shop_order_change", args=[order.pk]))
    assert detail.status_code == 200
    assert "Toffee" in detail.content.decode()
    assert 'name="total_amount"' not in detail.content.decode()
    assert admin_client.get(reverse("admin:shop_order_add")).status_code == 403
    assert admin_client.post(reverse("admin:shop_order_change", args=[order.pk]),
                             {"status": "paid"}).status_code == 403
    assert admin_client.post(reverse("admin:shop_order_delete", args=[order.pk]),
                             {"post": "yes"}).status_code == 403
    assert Order.objects.get().status == Order.Status.PENDING
