from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pfios.core.config.settings import settings

engine = create_engine(settings.db_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
