import math
import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chame_app.database import reset_database
from chame_app.database_instance import Database
import services.admin_api as api


def test_bank_metrics_are_derived_from_costs_revenue_and_balances(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_STORAGE", str(tmp_path))
    monkeypatch.delenv("HOME", raising=False)
    reset_database()
    api.database = None

    db = Database(apply_migrations=False)
    db.add_ingredient(
        name="Bread",
        price_per_package=1.0,
        stock_quantity=10,
        number_ingredients=10,
        pfand=0.0,
    )
    ingredient = db.get_all_ingredients()[0]
    db.add_product(
        name="Toast",
        ingredients=[(ingredient, 1)],
        price_per_unit=2.5,
        category="toast",
        toaster_space=1,
    )
    db.add_user(username="buyer", password="", salesman_id=1, role="user", balance=20.0)

    buyer = db.get_user_by_username("buyer")
    product = next(product for product in db.get_all_products() if product.name == "Toast")

    db.make_purchase(buyer.user_id, product.product_id, 1, salesman_id=1)
    bank = db.get_bank().to_dict()

    assert math.isclose(bank['revenue_total'], 2.5)
    assert math.isclose(bank['costs_total'], 10.0)
    assert math.isclose(bank['business_balance'], 2.5)
    assert math.isclose(bank['break_even_remaining'], 7.5)
    assert math.isclose(bank['break_even_covered_costs'], 2.5)
    assert math.isclose(bank['break_even_progress'], 0.25)
    assert bank['break_even_reached'] is False

    with pytest.raises(RuntimeError, match='Insufficient business balance'):
        db.withdraw_cash_from_bank(3.0, salesman_id=1)

    db.withdraw_cash_from_bank(2.0, salesman_id=1)
    updated_bank = db.get_bank().to_dict()

    assert math.isclose(updated_bank['total_balance'], 18.0)
    assert math.isclose(updated_bank['customer_funds'], 17.5)
    assert math.isclose(updated_bank['business_balance'], 0.5)
    assert math.isclose(updated_bank['costs_total'], 12.0)
    assert math.isclose(updated_bank['break_even_remaining'], 9.5)
    assert math.isclose(updated_bank['profit_total'], -9.5)