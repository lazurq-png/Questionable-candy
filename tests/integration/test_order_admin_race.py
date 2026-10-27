"""Audit C4: the admin's stock check and a checkout, racing for real.

Two transactions on two connections, so the database's own locking decides
the outcome. That needs committed rows, so ``transactional_db`` -- requested by
name and first, with no ``django_db`` mark: a mark makes pytest-django set the
database up before any fixture, ahead of the async-safety opt-out in
tests/conftest.py, which the full run needs once Playwright's loop is alive.
"""
import threading

from django.db import connection
from django.urls import reverse

from shop.admin import OrderItemFormSet
from shop.models import Order, OrderChanged
from tests.integration.test_orders import (  # pylint: disable=unused-import
    fixture_ada, fixture_candies, order_form, place, snapshot_of, stock,
)


def test_a_checkout_in_the_moment_after_the_stock_check_waits_for_the_admins_save(
    transactional_db, admin_client, ada, candies, monkeypatch
):  # pylint: disable=unused-argument
    """Audit C4: two transactions really race, the admin's and a customer's.

    The admin's check passes on all 5 Toffee; a customer then places 1 before
    the admin saves. Without a lock the customer wins, the admin's save takes
    stock below zero, and the database's refusal is a 500. With the check's
    rows locked, the customer waits, finds the stock gone, and is told so.
    """
    toffee, _ = candies
    checked, placed = threading.Event(), threading.Event()
    outcome = {}
    check = OrderItemFormSet.clean

    def check_then_let_the_customer_in(formset):
        check(formset)
        checked.set()
        placed.wait(timeout=1)  # a customer who is not blocked finishes well within this

    def customer():
        checked.wait(timeout=10)
        try:
            place(ada, snapshot_of((toffee, 1)))
            outcome["customer"] = "placed"
        except OrderChanged as error:
            outcome["customer"] = error.candies
        finally:
            connection.close()
            placed.set()

    monkeypatch.setattr(OrderItemFormSet, "clean", check_then_let_the_customer_in)
    thread = threading.Thread(target=customer)
    thread.start()
    response = admin_client.post(reverse("admin:shop_order_add"), order_form(
        ada, [{"candy": toffee.pk, "quantity": 5, "unit_price": ""}]))
    thread.join(timeout=10)

    assert response.status_code == 302
    assert outcome["customer"] == ["Toffee"]
    assert stock(toffee) == 0
    assert Order.objects.get().items.get().quantity == 5
