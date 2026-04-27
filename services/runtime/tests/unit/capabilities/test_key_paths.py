"""Capabilities key-path tests — governance pipeline for finance and coding decisions."""

from domains.decision_intake.models import DecisionIntake
from governance.risk_engine.engine import RiskEngine
from packs.coding.policy import CodingDisciplinePolicy
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy


# ═══════════════════════════════════════════════════════════════════════
# D3.1 — Finance decisions govern_intake key paths
# ═══════════════════════════════════════════════════════════════════════


def _finance_intake(**payload_overrides):
    payload = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC breaking above resistance with volume confirmation; invalidated if price closes below 200 EMA.",
        "stop_loss": "2%",
        "max_loss_usdt": 200,
        "position_size_usdt": 1000,
        "risk_unit_usdt": 200,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.7,
    }
    payload.update(payload_overrides)
    return DecisionIntake(
        id="intake-test-finance",
        pack_id="finance",
        intake_type="trading_decision",
        payload=payload,
        status="validated",
    )


def test_finance_valid_intake_executes():
    """Valid finance payload must execute through RiskEngine."""
    engine = RiskEngine()
    intake = _finance_intake()
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "execute"


def test_finance_missing_thesis_rejects():
    """Missing thesis must reject."""
    engine = RiskEngine()
    intake = _finance_intake(thesis="")
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "reject"
    assert any("thesis" in r.lower() for r in decision.reasons)


def test_finance_stressed_emotional_state_escalates():
    """stressed emotional_state must escalate."""
    engine = RiskEngine()
    intake = _finance_intake(emotional_state="stressed")
    decision = engine.validate_intake(intake, pack_policy=TradingDisciplinePolicy())
    assert decision.decision == "escalate"


# ═══════════════════════════════════════════════════════════════════════
# D3.2 — Coding decisions key paths
# ═══════════════════════════════════════════════════════════════════════


def _coding_intake(**payload_overrides):
    payload = {
        "task_description": "Add unit test for edge case",
        "file_paths": ["tests/unit/test_edge.py"],
        "estimated_impact": "low",
        "reasoning": "Missing coverage.",
        "test_plan": "pytest tests/unit/test_edge.py",
    }
    payload.update(payload_overrides)
    return DecisionIntake(
        id="intake-test-coding",
        pack_id="coding",
        intake_type="code_change",
        payload=payload,
        status="validated",
    )


def test_coding_valid_intake_executes():
    engine = RiskEngine()
    intake = _coding_intake()
    decision = engine.validate_intake(intake, pack_policy=CodingDisciplinePolicy())
    assert decision.decision == "execute"


def test_coding_missing_task_rejects():
    engine = RiskEngine()
    intake = _coding_intake(task_description="")
    decision = engine.validate_intake(intake, pack_policy=CodingDisciplinePolicy())
    assert decision.decision == "reject"


def test_coding_forbidden_file_rejects():
    engine = RiskEngine()
    intake = _coding_intake(file_paths=[".env"])
    decision = engine.validate_intake(intake, pack_policy=CodingDisciplinePolicy())
    assert decision.decision == "reject"


def test_coding_high_impact_escalates():
    engine = RiskEngine()
    intake = _coding_intake(estimated_impact="high")
    decision = engine.validate_intake(intake, pack_policy=CodingDisciplinePolicy())
    assert decision.decision == "escalate"


# ═══════════════════════════════════════════════════════════════════════
# D3.3 — Cross-Pack: RiskEngine is Pack-agnostic
# ═══════════════════════════════════════════════════════════════════════


def test_risk_engine_handles_both_packs():
    """Same RiskEngine instance validates both Finance and Coding intakes."""
    engine = RiskEngine()

    fin = engine.validate_intake(_finance_intake(), pack_policy=TradingDisciplinePolicy())
    assert fin.decision == "execute"

    cod = engine.validate_intake(_coding_intake(), pack_policy=CodingDisciplinePolicy())
    assert cod.decision == "execute"


# ═══════════════════════════════════════════════════════════════════════
# D3.4 — No broker/order/trade in capabilities paths
# ═══════════════════════════════════════════════════════════════════════


def test_capability_tests_no_broker_imports():
    """This test file must not import broker/order/trade."""
    import inspect

    source = inspect.getsource(inspect.getmodule(test_capability_tests_no_broker_imports))
    forbidden = ["broker", "place_order", "execute_trade"]
    import_lines = [l for l in source.splitlines() if l.strip().startswith(("from ", "import "))]
    for word in forbidden:
        assert word not in "\n".join(import_lines), f"Forbidden import: {word}"
