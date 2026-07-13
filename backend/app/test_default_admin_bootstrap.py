import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chame_app.database import reset_database
from chame_app.database_instance import Database
from models.user_table import User


def test_recreates_default_admin_when_all_admins_are_inactive(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_STORAGE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("APP_PRIVATE_ROOT", str(tmp_path))

    reset_database()
    db = Database(apply_migrations=False)

    session = db.get_session()
    admin_user = User.active_only(session.query(User)).filter_by(role="admin").first()
    god_user = User.active_only(session.query(User)).filter_by(role="god").first()
    assert admin_user is not None
    assert god_user is not None

    admin_user.soft_delete("test")
    god_user.soft_delete("test")
    session.commit()
    session.close()

    reset_database()
    db = Database(apply_migrations=False)

    session = db.get_session()
    active_admins = User.active_only(session.query(User)).filter_by(role="admin").all()
    all_admins = session.query(User).filter_by(role="admin").all()

    assert len(active_admins) == 1
    assert active_admins[0].name == "admin"
    assert len(all_admins) == 2

    session.close()


def test_does_not_recreate_default_admin_when_active_god_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_STORAGE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("APP_PRIVATE_ROOT", str(tmp_path))

    reset_database()
    db = Database(apply_migrations=False)

    session = db.get_session()
    admin_user = User.active_only(session.query(User)).filter_by(role="admin").first()
    god_user = User.active_only(session.query(User)).filter_by(role="god").first()
    assert admin_user is not None
    assert god_user is not None

    admin_user.soft_delete("test")
    session.commit()
    session.close()

    reset_database()
    db = Database(apply_migrations=False)

    session = db.get_session()
    active_admins = User.active_only(session.query(User)).filter_by(role="admin").all()
    active_god = User.active_only(session.query(User)).filter_by(role="god").first()

    assert len(active_admins) == 0
    assert active_god is not None

    session.close()