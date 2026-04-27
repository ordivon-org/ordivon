"""ExecutionReceipt detail_json round-trip invariant tests.

Verifies that dict data stored in the detail field survives a
full create_receipt → get_receipt round-trip without corruption,
including nested structures.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from domains.execution_records.models import ExecutionReceipt
from domains.execution_records.repository import ExecutionRecordRepository
from shared.utils.serialization import from_json_text
from state.db.base import Base


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def _make_receipt(detail: dict) -> ExecutionReceipt:
    return ExecutionReceipt(
        request_id="exreq_test123",
        action_id="test_action",
        status="succeeded",
        detail=detail,
    )


# ── Test 1: plan metadata detail survives round-trip ──────────────────────


def test_plan_metadata_detail_round_trip(db: Session):
    """Create ExecutionReceipt with plan metadata, persist, read back; detail matches."""
    repo = ExecutionRecordRepository(db)

    plan_meta = {
        "receipt_kind": "plan",
        "broker_execution": False,
        "side_effect_level": "none",
        "decision_intake_id": "di_abc123",
        "governance_status": "execute",
    }

    receipt = _make_receipt(plan_meta)
    row = repo.create_receipt(receipt)

    # Read back via get_receipt
    reloaded = repo.get_receipt(row.id)

    assert reloaded is not None
    detail = from_json_text(reloaded.detail_json, {})

    assert detail == plan_meta
    assert detail["receipt_kind"] == "plan"
    assert detail["broker_execution"] is False
    assert detail["side_effect_level"] == "none"
    assert detail["decision_intake_id"] == "di_abc123"
    assert detail["governance_status"] == "execute"


# ── Test 2: nested structures survive round-trip ──────────────────────────


def test_nested_detail_survives_round_trip(db: Session):
    """Nested dict, list, float, bool in detail survive full round-trip."""
    repo = ExecutionRecordRepository(db)

    nested = {
        "strategy": {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "indicators": ["EMA200", "RSI14", "MACD"],
            "thresholds": {
                "confidence_min": 0.65,
                "max_loss_ratio": 0.02,
            },
        },
        "steps": [
            {"name": "validate", "passed": True, "score": 0.92},
            {"name": "approve", "passed": True, "score": 0.88},
        ],
        "tags": ["automated", "low_risk"],
        "null_value": None,
        "float_value": 3.14159,
        "int_value": 42,
        "bool_value": False,
    }

    receipt = _make_receipt(nested)
    row = repo.create_receipt(receipt)

    reloaded = repo.get_receipt(row.id)

    assert reloaded is not None
    detail = from_json_text(reloaded.detail_json, {})

    assert detail == nested

    # Drill into specific nested values
    assert detail["strategy"]["symbol"] == "BTC/USDT"
    assert detail["strategy"]["indicators"][0] == "EMA200"
    assert detail["strategy"]["thresholds"]["confidence_min"] == 0.65
    assert detail["steps"][0]["name"] == "validate"
    assert detail["steps"][0]["passed"] is True
    assert detail["steps"][0]["score"] == 0.92
    assert detail["steps"][1]["name"] == "approve"
    assert detail["tags"] == ["automated", "low_risk"]
    assert detail["null_value"] is None
    assert detail["float_value"] == 3.14159
    assert detail["int_value"] == 42
    assert detail["bool_value"] is False
