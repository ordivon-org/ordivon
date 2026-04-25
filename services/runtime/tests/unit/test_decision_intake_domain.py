from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def test_valid_intake_persists_as_validated_with_governance_not_started():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        service = DecisionIntakeService(DecisionIntakeRepository(db))

        intake = service.record_intake(
            pack_id="finance",
            intake_type="controlled_decision",
            payload={"symbol": "BTC/USDT"},
            validation_errors=[],
        )

        assert intake.status == "validated"
        assert intake.governance_status == "not_started"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_invalid_intake_persists_with_structured_validation_errors():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        service = DecisionIntakeService(DecisionIntakeRepository(db))

        intake = service.record_intake(
            pack_id="finance",
            intake_type="controlled_decision",
            payload={"symbol": "BTC/USDT"},
            validation_errors=[
                {"field": "thesis", "code": "required", "message": "thesis is required before governance."}
            ],
        )

        assert intake.status == "invalid"
        assert intake.governance_status == "not_started"
        assert intake.validation_errors[0]["field"] == "thesis"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
