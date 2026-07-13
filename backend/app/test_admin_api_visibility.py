import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chame_app.database import reset_database
from chame_app.database_instance import Database
import services.admin_api as api


def test_admin_api_hides_god_linked_records_for_non_god_viewers(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_STORAGE", str(tmp_path))
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("APP_PRIVATE_ROOT", raising=False)
    reset_database()
    api._database = None
    api.logout()

    db = Database(apply_migrations=False)
    db.add_user(username="auditor", password="abcdefgh", salesman_id=1, role="admin", balance=25.0)
    auditor = db.get_user_by_username("auditor")
    god_user = db.get_user_by_username("god")

    db.deposit_cash(user_id=auditor.user_id, amount=5.0, salesman_id=god_user.user_id)
    db.deposit_cash(user_id=god_user.user_id, amount=3.0, salesman_id=auditor.user_id)

    api.login("auditor", "abcdefgh")
    visible_users = api.get_all_users()
    visible_transactions = api.get_filtered_transaction()

    assert all(user["role"] != "god" for user in visible_users)
    assert all(user["user_id"] != god_user.user_id for user in visible_users)
    assert all(transaction["user_id"] != god_user.user_id for transaction in visible_transactions)
    assert all(
        transaction.get("user", {}).get("role") != "god"
        for transaction in visible_transactions
        if isinstance(transaction.get("user"), dict)
    )

    api.login("god", "god_password")
    god_visible_users = api.get_all_users()
    god_visible_transactions = api.get_filtered_transaction()

    assert any(user["user_id"] == god_user.user_id for user in god_visible_users)
    assert any(transaction["user_id"] == god_user.user_id for transaction in god_visible_transactions)

    api.logout()
