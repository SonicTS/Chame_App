from pathlib import Path
import os

def get_sqlite_url():
    private_dir = os.environ.get("PRIVATE_STORAGE")
    home_dir = os.environ.get("HOME")
    if private_dir:
        db_path = Path(private_dir) / "kassensystem.db"
    elif home_dir:
        db_path = Path(home_dir) / "kassensystem.db"
    else:
        db_path = Path("kassensystem.db")
    return f"sqlite:///{db_path.resolve()}"
