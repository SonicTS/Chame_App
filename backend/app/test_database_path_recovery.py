import os
import sqlite3
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chame_app.database import resolve_database_path


def _create_sqlite_db(path: Path, statements: list[str]):
    with sqlite3.connect(path) as conn:
        for statement in statements:
            conn.execute(statement)


def test_resolve_database_path_prefers_legacy_existing_db(tmp_path, monkeypatch):
    app_root = tmp_path / "app_root"
    files_dir = app_root / "files"
    legacy_dir = app_root / "legacy"
    files_dir.mkdir(parents=True)
    legacy_dir.mkdir(parents=True)

    legacy_db = legacy_dir / "kassensystem.db"
    _create_sqlite_db(legacy_db, ["CREATE TABLE example (id INTEGER PRIMARY KEY)"])

    monkeypatch.setenv("PRIVATE_STORAGE", str(files_dir))
    monkeypatch.setenv("HOME", str(files_dir))
    monkeypatch.setenv("APP_PRIVATE_ROOT", str(app_root))

    resolved_path = resolve_database_path()

    assert resolved_path == legacy_db


def test_resolve_database_path_uses_preferred_when_present(tmp_path, monkeypatch):
    files_dir = tmp_path / "files"
    files_dir.mkdir(parents=True)
    preferred_db = files_dir / "kassensystem.db"
    preferred_db.write_bytes(b"preferred-db")

    monkeypatch.setenv("PRIVATE_STORAGE", str(files_dir))
    monkeypatch.setenv("HOME", str(files_dir))
    monkeypatch.setenv("APP_PRIVATE_ROOT", str(tmp_path))

    resolved_path = resolve_database_path()

    assert resolved_path == preferred_db


def test_resolve_database_path_ignores_chaquopy_assetfinder_database(tmp_path, monkeypatch):
    app_root = tmp_path / "app_root"
    files_dir = app_root / "files"
    asset_db_dir = files_dir / "chaquopy" / "AssetFinder" / "app"
    files_dir.mkdir(parents=True)
    asset_db_dir.mkdir(parents=True)

    asset_db = asset_db_dir / "kassensystem.db"
    _create_sqlite_db(asset_db, ["CREATE TABLE example (id INTEGER PRIMARY KEY)"])

    monkeypatch.setenv("PRIVATE_STORAGE", str(files_dir))
    monkeypatch.setenv("HOME", str(files_dir))
    monkeypatch.setenv("APP_PRIVATE_ROOT", str(app_root))

    resolved_path = resolve_database_path()

    assert resolved_path == files_dir / "kassensystem.db"


def test_resolve_database_path_prefers_richer_legacy_db_over_bootstrap_preferred(tmp_path, monkeypatch):
    app_root = tmp_path / "app_root"
    files_dir = app_root / "files"
    legacy_dir = app_root / "legacy"
    files_dir.mkdir(parents=True)
    legacy_dir.mkdir(parents=True)

    preferred_db = files_dir / "kassensystem.db"
    _create_sqlite_db(
        preferred_db,
        [
            "CREATE TABLE users (user_id INTEGER PRIMARY KEY, name TEXT)",
            "INSERT INTO users (user_id, name) VALUES (1, 'admin')",
        ],
    )

    legacy_db = legacy_dir / "kassensystem.db"
    _create_sqlite_db(
        legacy_db,
        [
            "CREATE TABLE users (user_id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE products (product_id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE sales (sale_id INTEGER PRIMARY KEY, product_id INTEGER)",
            "INSERT INTO users (user_id, name) VALUES (1, 'admin')",
            "INSERT INTO users (user_id, name) VALUES (2, 'alice')",
            "INSERT INTO products (product_id, name) VALUES (1, 'toast')",
            "INSERT INTO sales (sale_id, product_id) VALUES (1, 1)",
        ],
    )

    monkeypatch.setenv("PRIVATE_STORAGE", str(files_dir))
    monkeypatch.setenv("HOME", str(files_dir))
    monkeypatch.setenv("APP_PRIVATE_ROOT", str(app_root))

    resolved_path = resolve_database_path()

    assert resolved_path == legacy_db