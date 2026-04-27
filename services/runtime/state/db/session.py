from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.config.settings import settings

engine = create_engine(settings.db_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_connection(read_only: bool = True):
    """Raw DPAPI connection (compatibility helper)."""
    return engine.connect() if not read_only else engine.connect()  # SQLite handles this internally
