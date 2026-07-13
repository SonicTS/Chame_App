from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Set, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import sqlite3

DB_FILENAME = "kassensystem.db"

Base= declarative_base()        # exported for model modules
SessionLocal = None             # will be rebound once engine exists

def get_session(apply_migrations: bool = True):
    """Return a new SQLAlchemy Session, creating the engine the first time."""
    global _engine, SessionLocal

    if _engine is None:                   # first call → create engine lazily
        _engine = _create_engine_once(apply_migrations)
        Base.metadata.create_all(_engine)      # idempotent
        SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

    return SessionLocal()


def get_database_storage_diagnostics() -> dict:
    preferred_path = _get_preferred_database_path()
    resolved_path = resolve_database_path()
    search_roots = _get_database_search_roots()
    app_private_root = os.environ.get("APP_PRIVATE_ROOT")
    app_private_root_path = Path(app_private_root) if app_private_root else None
    candidate_paths: List[Path] = []

    for root in search_roots:
        candidate_paths.extend(_collect_database_candidates(root, preferred_path))

    all_paths: List[Path] = []
    for path in [preferred_path, resolved_path, *candidate_paths]:
        if path not in all_paths:
            all_paths.append(path)

    candidates = []
    for path in all_paths:
        exists = path.exists()
        size = path.stat().st_size if exists and path.is_file() else 0
        modified_at = path.stat().st_mtime if exists and path.is_file() else None
        is_valid = _is_valid_sqlite_database(path) if exists else False
        candidates.append({
            "path": str(path),
            "exists": exists,
            "size_bytes": size,
            "modified_at": modified_at,
            "is_valid_sqlite": is_valid,
            "is_preferred_path": path == preferred_path,
            "is_resolved_path": path == resolved_path,
        })

    return {
        "private_storage": os.environ.get("PRIVATE_STORAGE"),
        "home": os.environ.get("HOME"),
        "app_private_root": app_private_root,
        "preferred_database_path": str(preferred_path),
        "resolved_database_path": str(resolved_path),
        "resolved_database_exists": resolved_path.exists(),
        "resolved_database_valid": _is_valid_sqlite_database(resolved_path) if resolved_path.exists() else False,
        "search_roots": [str(path) for path in search_roots],
        "candidates": candidates,
        "top_level_directories": _get_top_level_directory_sizes(app_private_root_path),
        "large_files": _get_large_files(app_private_root_path),
        "sqlite_like_files": _get_sqlite_like_files(app_private_root_path),
    }



def reset_database():
    """Reset the database engine and session to None to force fresh creation."""
    global _engine, SessionLocal
    _engine = None
    SessionLocal = None
    print("DEBUG: Database engine and session reset to None")

# ── Internal helpers ─────────────────────────────────────────────────-
_engine: Optional[object] = None           # keeps the singleton engine


def _get_preferred_database_path() -> Path:
    private_dir = os.environ.get("PRIVATE_STORAGE")
    home_dir = os.environ.get("HOME")

    if private_dir:
        return Path(private_dir) / DB_FILENAME
    if home_dir:
        return Path(home_dir) / DB_FILENAME
    return Path(DB_FILENAME)


def resolve_database_path() -> Path:
    preferred_path = _get_preferred_database_path()

    legacy_path = _find_legacy_database_path(preferred_path)
    if legacy_path:
        print("Using legacy SQLite path:", legacy_path)
        return legacy_path

    return preferred_path


def _find_legacy_database_path(preferred_path: Path) -> Optional[Path]:
    if preferred_path.exists() and preferred_path.stat().st_size > 0 and not _is_valid_sqlite_database(preferred_path):
        return None

    candidate_paths: List[Path] = []
    search_roots = _get_database_search_roots()
    for root in search_roots:
        candidate_paths.extend(_collect_database_candidates(root, preferred_path))

    preferred_valid = _is_valid_sqlite_database(preferred_path)
    preferred_score = _score_database_candidate(preferred_path) if preferred_valid else None

    if not candidate_paths:
        return None

    candidate_paths = [path for path in candidate_paths if _is_valid_sqlite_database(path)]
    if not candidate_paths:
        return None

    candidate_paths.sort(key=_score_database_candidate, reverse=True)
    best_candidate = candidate_paths[0]
    best_score = _score_database_candidate(best_candidate)

    if best_candidate.stat().st_size <= 0:
        return None

    if preferred_valid and preferred_score is not None and preferred_score >= best_score:
        return None

    return best_candidate


def _get_database_search_roots() -> List[Path]:
    roots: List[Path] = []
    private_dir = os.environ.get("PRIVATE_STORAGE")
    home_dir = os.environ.get("HOME")
    app_private_root = os.environ.get("APP_PRIVATE_ROOT")
    has_explicit_storage_root = bool(private_dir or home_dir)

    for raw_path in [private_dir, home_dir]:
        if not raw_path:
            continue
        path = Path(raw_path)
        roots.append(path)

    if app_private_root:
        roots.append(Path(app_private_root))

    if not has_explicit_storage_root:
        roots.append(Path.cwd())
        if Path.cwd().parent != Path.cwd():
            roots.append(Path.cwd().parent)

    unique_roots: List[Path] = []
    seen: Set[str] = set()
    for root in roots:
        root_str = str(root)
        if root_str in seen or not root.exists():
            continue
        seen.add(root_str)
        unique_roots.append(root)
    return unique_roots


def _collect_database_candidates(root: Path, preferred_path: Path, max_depth: int = 3) -> List[Path]:
    candidates: List[Path] = []
    for current_root, dirs, files in os.walk(root):
        current_path = Path(current_root)
        if _is_excluded_candidate_path(current_path):
            dirs[:] = []
            continue
        depth = len(current_path.relative_to(root).parts) if current_path != root else 0
        if depth >= max_depth:
            dirs[:] = []
        if DB_FILENAME in files:
            candidate = current_path / DB_FILENAME
            if candidate == preferred_path or _is_excluded_candidate_path(candidate):
                continue
            candidates.append(candidate)
    return candidates


def _is_excluded_candidate_path(path: Path) -> bool:
    normalized_parts = [part.lower() for part in path.parts]
    for index in range(len(normalized_parts) - 1):
        if normalized_parts[index] == "chaquopy" and normalized_parts[index + 1] == "assetfinder":
            return True
    return False


def _get_top_level_directory_sizes(root: Optional[Path]) -> List[dict]:
    if root is None or not root.exists() or not root.is_dir():
        return []

    results = []
    for child in root.iterdir():
        try:
            size_bytes = _calculate_path_size(child)
        except OSError:
            continue
        results.append({
            "path": str(child),
            "name": child.name,
            "is_dir": child.is_dir(),
            "size_bytes": size_bytes,
        })

    results.sort(key=lambda item: item["size_bytes"], reverse=True)
    return results[:12]


def _get_large_files(root: Optional[Path]) -> List[dict]:
    if root is None or not root.exists() or not root.is_dir():
        return []

    files = []
    for current_root, dirs, filenames in os.walk(root):
        current_path = Path(current_root)
        if _is_excluded_candidate_path(current_path):
            dirs[:] = []
            continue
        for filename in filenames:
            file_path = current_path / filename
            try:
                stat = file_path.stat()
            except OSError:
                continue
            files.append({
                "path": str(file_path),
                "name": filename,
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
            })

    files.sort(key=lambda item: item["size_bytes"], reverse=True)
    return files[:20]


def _get_sqlite_like_files(root: Optional[Path]) -> List[dict]:
    if root is None or not root.exists() or not root.is_dir():
        return []

    sqlite_files = []
    for current_root, dirs, filenames in os.walk(root):
        current_path = Path(current_root)
        if _is_excluded_candidate_path(current_path):
            dirs[:] = []
            continue
        for filename in filenames:
            file_path = current_path / filename
            lower_name = filename.lower()
            if not (
                lower_name.endswith(".db")
                or lower_name.endswith(".sqlite")
                or lower_name.endswith(".sqlite3")
                or DB_FILENAME in lower_name
            ):
                continue
            try:
                stat = file_path.stat()
            except OSError:
                continue
            sqlite_files.append({
                "path": str(file_path),
                "name": filename,
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "is_valid_sqlite": _is_valid_sqlite_database(file_path),
            })

    sqlite_files.sort(key=lambda item: item["size_bytes"], reverse=True)
    return sqlite_files[:20]


def _calculate_path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size

    total_size = 0
    for current_root, dirs, filenames in os.walk(path):
        current_path = Path(current_root)
        if _is_excluded_candidate_path(current_path):
            dirs[:] = []
            continue
        for filename in filenames:
            file_path = current_path / filename
            try:
                total_size += file_path.stat().st_size
            except OSError:
                continue
    return total_size


def _is_valid_sqlite_database(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return False
        with sqlite3.connect(str(path)) as conn:
            conn.execute("PRAGMA schema_version")
        return True
    except sqlite3.DatabaseError:
        return False
    except OSError:
        return False


def _score_database_candidate(path: Path) -> Tuple[int, int, int, float]:
    """Score a database by how much real business data it appears to contain."""
    try:
        if not _is_valid_sqlite_database(path):
            return (-1, -1, 0, 0.0)

        with sqlite3.connect(str(path)) as conn:
            cursor = conn.cursor()
            table_names = {
                row[0]
                for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                if row[0] and not str(row[0]).startswith("sqlite_")
            }

            counts = {}
            for table_name in [
                "users",
                "products",
                "ingredients",
                "sales",
                "transactions",
                "stock_history",
                "bank_transactions",
                "toast_round",
                "pfand_history",
            ]:
                if table_name not in table_names:
                    counts[table_name] = 0
                    continue
                counts[table_name] = cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]

        adjusted_counts = {
            **counts,
            "users": max(counts.get("users", 0) - 1, 0),
        }
        meaningful_rows = sum(adjusted_counts.values())
        populated_tables = sum(1 for count in adjusted_counts.values() if count > 0)
        return (
            populated_tables,
            meaningful_rows,
            path.stat().st_size,
            path.stat().st_mtime,
        )
    except (OSError, sqlite3.DatabaseError):
        return (-1, -1, 0, 0.0)

def _create_engine_once(apply_migrations: bool = True):
    """Build engine after env-vars are ready, ensure directory exists."""
    db_path = resolve_database_path()
    print("SQLite path:", db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if this is a new database before creating it
    database_is_new = not db_path.exists()
    
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
    
    # Create tables with current schema
    Base.metadata.create_all(bind=engine)
    
    # Handle migrations based on whether this is a new or existing database
    try:
        from .simple_migrations import SimpleMigrations
        
        migrations = SimpleMigrations(engine)
        
        if database_is_new:
            print("🆕 New database detected - marking all migrations as applied")
            migrations.set_fresh_database_flag()
            migrations.mark_all_migrations_applied()
            print("✅ New database initialized with all migrations marked as applied")
        elif apply_migrations:
            print("🔄 Existing database detected - checking for pending migrations")
            success = migrations.run_migrations(create_backup=True)
            
            if success:
                print("✅ Database migrations completed successfully")
            else:
                print("❌ Database migrations failed - check logs for details")
                
    except ImportError:
        print("⚠️ SimpleMigrations not available - skipping migration handling")
    except Exception as e:
        print(f"⚠️ Migration handling failed: {e}")
        # Don't raise - allow the application to continue with the database
    
    return engine