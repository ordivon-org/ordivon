from orchestrator.runtime.engine import PFIOSOrchestrator
from state.db.session import SessionLocal


def get_orchestrator() -> PFIOSOrchestrator:
    return PFIOSOrchestrator()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
