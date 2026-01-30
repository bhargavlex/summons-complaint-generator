"""
SQLite database base – use via scripts/init_db_sqlite.py and scripts/run_sqlite.py.
Does not replace or import from app.db.base.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite DB file next to backend root when running from backend/
SQLITE_URL = "sqlite:///./summons.db"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
