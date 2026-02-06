"""
Run FastAPI app against SQLite. Patches app.db.base to use SQLite, then starts uvicorn.
Run from backend/:  python -m scripts.run_sqlite
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Patch app.db.base to SQLite before any app code imports it
import app.db.base_sqlite as base_sqlite
sys.modules["app.db.base"] = base_sqlite

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
