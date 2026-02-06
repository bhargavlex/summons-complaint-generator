"""
Initialize SQLite database. Patches app.db.base to use SQLite, then runs init_db.
Run from backend/:  python -m scripts.init_db_sqlite
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Patch app.db.base to SQLite before any app code imports it
import app.db.base_sqlite as base_sqlite
sys.modules["app.db.base"] = base_sqlite

from app.db.init_db import init_db

if __name__ == "__main__":
    init_db()
