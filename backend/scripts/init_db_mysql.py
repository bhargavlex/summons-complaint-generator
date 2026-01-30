"""
Initialize MySQL database (for Docker / production).
Uses DATABASE_URL from environment; runs app.db.init_db.
Run from backend/ or from container:  python -m scripts.init_db_mysql
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.init_db import init_db

if __name__ == "__main__":
    init_db()
