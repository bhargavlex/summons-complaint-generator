"""
Create a test session in SQLite and run preview generation. Patches app.db.base to SQLite.
Run from backend/:  python -m scripts.test_preview_sqlite
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Patch app.db.base to SQLite before any app code imports it
import app.db.base_sqlite as base_sqlite
sys.modules["app.db.base"] = base_sqlite

# Now run the real test_preview main (it will use SQLite via the patch)
from scripts.test_preview import main

if __name__ == "__main__":
    main()
