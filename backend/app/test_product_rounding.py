import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chame_app.database import reset_database
from chame_app.database_instance import Database
from models.transaction_table import Transaction
import services.admin_api as api


def test_purchase_rounding_difference_is_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_STORAGE", str(tmp_path))
    monkeypatch.delenv("HOME", raising=False)
    reset_database()
    api._database = None

    db = Database(apply_migrations=False)
    db.add_ingredient(
        name="Round Bread",
        price_per_package=1.0,
        stock_quantity=10,
        number_ingredients=10,
        pfand=0.0,
    )
    ingredient = db.get_all_ingredients()[0]
    db.add_product(
        name="Rounded Toast",
        ingredients=[(ingredient, 1)],
        price_per_unit=2.31,
        category="toast",
        toaster_space=1,
    )
    db.add_user(username="buyer", password="", salesman_id=1, role="user", balance=10.0)

    buyer = db.get_user_by_username("buyer")
    god_user = db.get_user_by_username("god")
    product = next(product for product in db.get_all_products() if product.name == "Rounded Toast")

    sale = db.make_purchase(buyer.user_id, product.product_id, 1, salesman_id=1)

    refreshed_buyer = db.get_user_by_id(buyer.user_id)
    refreshed_god_user = db.get_user_by_id(god_user.user_id)
    bank = db.get_bank()
    session = db.get_session()
    try:
        rounding_transaction = (
            session.query(Transaction)
            .filter(Transaction.user_id == god_user.user_id)
            .order_by(Transaction.transaction_id.desc())
            .first()
        )
    finally:
        session.close()

    assert math.isclose(product.get_display_price_per_unit(), 2.31)
    assert math.isclose(product.get_checkout_price_per_unit(), 2.31)
    assert math.isclose(product.get_rounding_difference_per_unit(), 0.0)
    assert math.isclose(sale.total_price, 2.31)
    assert math.isclose(refreshed_buyer.balance, 7.69)
    assert math.isclose(refreshed_god_user.balance, 0.0)
    assert math.isclose(bank.customer_funds, 7.69)
    assert math.isclose(bank.revenue_total, 2.31)
    assert rounding_transaction is None


def test_purchase_with_one_decimal_price_uses_visible_total_when_rounding_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_STORAGE", str(tmp_path))
    monkeypatch.delenv("HOME", raising=False)
    reset_database()
    api._database = None

    db = Database(apply_migrations=False)
    db.add_ingredient(
        name="Whole Bread",
        price_per_package=1.0,
        stock_quantity=10,
        number_ingredients=10,
        pfand=0.0,
    )
    ingredient = db.get_all_ingredients()[0]
    db.add_product(
        name="Simple Toast",
        ingredients=[(ingredient, 1)],
        price_per_unit=1.4,
        category="toast",
        toaster_space=1,
    )
    db.add_user(username="buyer", password="", salesman_id=1, role="user", balance=10.0)

    buyer = db.get_user_by_username("buyer")
    god_user = db.get_user_by_username("god")
    product = next(product for product in db.get_all_products() if product.name == "Simple Toast")

    sale = db.make_purchase(buyer.user_id, product.product_id, 1, salesman_id=1)

    refreshed_buyer = db.get_user_by_id(buyer.user_id)
    refreshed_god_user = db.get_user_by_id(god_user.user_id)

    assert math.isclose(product.get_display_price_per_unit(), 1.4)
    assert math.isclose(sale.total_price, 1.4)
    assert math.isclose(refreshed_buyer.balance, 8.6)
    assert math.isclose(refreshed_god_user.balance, 0.0)