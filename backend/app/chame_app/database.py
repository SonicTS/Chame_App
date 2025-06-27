from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

Base= declarative_base()        # exported for model modules
SessionLocal = None             # will be rebound once engine exists

def get_session():
    """Return a new SQLAlchemy Session, creating the engine the first time."""
    global _engine, SessionLocal

    if _engine is None:                   # first call → create engine lazily
        _engine = _create_engine_once()
        Base.metadata.create_all(_engine)      # idempotent
        SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

    return SessionLocal()

def reset_database():
    """Reset the database engine and session to None to force fresh creation."""
    global _engine, SessionLocal
    _engine = None
    SessionLocal = None
    print("DEBUG: Database engine and session reset to None")

# ── Internal helpers ─────────────────────────────────────────────────-
_engine: Optional[object] = None           # keeps the singleton engine

def _create_engine_once():
    """Build engine after env-vars are ready, ensure directory exists."""
    # print("[DEBUG] os.name:", os.name)
    # print("[DEBUG] All environment variables:")
    # for k, v in os.environ.items():
    #     print(f"    {k}={v}")
    private_dir = os.environ.get("PRIVATE_STORAGE")
    home_dir = os.environ.get("HOME")
    if private_dir:
        db_path = Path(private_dir) / "kassensystem.db"
    elif home_dir:
        db_path = Path(home_dir) / "kassensystem.db"
    else:
        db_path = Path("kassensystem.db")
    print("SQLite path:", db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if not db_path.exists():
            db_path.touch(exist_ok=True)
    except Exception as e:
        print(f"Failed to create DB file: {db_path}, error: {e}")
        raise
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA user_version")
    print("DB ready:", db_path.exists())   # should print True
    Base.metadata.create_all(bind=engine)
    return engine