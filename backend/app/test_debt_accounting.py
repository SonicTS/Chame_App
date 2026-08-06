import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chame_app.database import reset_database
from chame_app.database_instance import Database


def setup_db(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_STORAGE", str(tmp_path))
    monkeypatch.delenv("HOME", raising=False)
    reset_database()
    # Ensure services use a fresh DB when needed
    db = Database(apply_migrations=False)
    return db


def test_debt_creation(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)

    # Create ingredient and product
    db.add_ingredient(name="Bread", price_per_package=1.0, stock_quantity=10, number_ingredients=10, pfand=0.0)
    ingredient = db.get_all_ingredients()[0]
    db.add_product(name="Toast", ingredients=[(ingredient, 1)], price_per_unit=5.0, category="toast", toaster_space=1)

    # Create a user with small balance but allowed_debt
    db.add_user(username="debtor", password="", salesman_id=1, role="user", balance=1.0, allowed_debt=5.0)
    user = db.get_user_by_username("debtor")
    product = next(p for p in db.get_all_products() if p.name == "Toast")

    # Make a purchase that exceeds balance but is within allowed_debt
    db.make_purchase(user.user_id, product.product_id, 1, salesman_id=1)

    # Reload user and bank
    updated_user = db.get_user_by_username("debtor")
    bank = db.get_bank().to_dict()

    # User balance should be negative by (total_cost - initial_balance)
    assert updated_user.balance < 0
    deficit = product.get_checkout_total_price(1) - 1.0
    assert pytest.approx(updated_user.balance, rel=1e-6) == 1.0 - product.get_checkout_total_price(1)

    # Bank should record the outstanding debt (debt_owed)
    assert bank.get('debt_owed', 0) >= pytest.approx(deficit - 1e-9)


def test_debt_repayment(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)

    # Create ingredient and product
    db.add_ingredient(name="Bread", price_per_package=1.0, stock_quantity=10, number_ingredients=10, pfand=0.0)
    ingredient = db.get_all_ingredients()[0]
    db.add_product(name="Toast", ingredients=[(ingredient, 1)], price_per_unit=5.0, category="toast", toaster_space=1)

    # Create a user with small balance but allowed_debt
    db.add_user(username="debtor2", password="", salesman_id=1, role="user", balance=1.0, allowed_debt=5.0)
    user = db.get_user_by_username("debtor2")
    product = next(p for p in db.get_all_products() if p.name == "Toast")

    # Cause debt
    db.make_purchase(user.user_id, product.product_id, 1, salesman_id=1)
    updated_user = db.get_user_by_username("debtor2")
    assert updated_user.balance < 0

    # Deposit to fully repay the debt
    db.deposit_cash(user.user_id, amount=abs(updated_user.balance), salesman_id=1)

    # After repayment, bank.debt_owed should be reduced (to 0) and user balance >= 0
    bank = db.get_bank().to_dict()
    refreshed_user = db.get_user_by_username("debtor2")
    assert refreshed_user.balance >= 0
    assert bank.get('debt_owed', 0) == pytest.approx(0.0)
