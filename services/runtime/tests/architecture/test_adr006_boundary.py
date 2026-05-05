"""ADR-006 Architecture Boundary Test — verify Core is clean of Pack types.

After ADR-006 completion (Wave 3B):
  - governance/risk_engine/thesis_quality.py must NOT exist
  - governance/risk_engine/engine.py must NOT import RejectReason/EscalateReason
  - governance/risk_engine/engine.py must NOT contain finance field names
  - governance/risk_engine/engine.py must NOT import from packs.finance
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "governance_engine"


def test_thesis_quality_py_does_not_exist():
    """thesis_quality.py was deleted as dead code — constants duplicated in Pack."""
    thesis_path = GOVERNANCE / "risk_engine" / "thesis_quality.py"
    assert not thesis_path.exists(), (
        f"ADR-006 violation: {thesis_path} still exists. "
        f"It was deleted in Wave 3B — all logic and constants live in "
        f"packs/finance/trading_discipline_policy.py."
    )


def test_engine_py_does_not_import_pack_reason_types():
    """RiskEngine must not import RejectReason or EscalateReason from Pack."""
    engine_path = GOVERNANCE / "risk_engine" / "engine.py"
    assert engine_path.exists(), f"Target file missing: {engine_path}"
    content = engine_path.read_text()

    # Check only import lines — avoid false positives from comments/docstrings
    import_lines = [l for l in content.splitlines() if l.strip().startswith(("from ", "import "))]

    assert not any("from packs.finance" in l for l in import_lines), (
        "ADR-006 violation: engine.py imports from packs.finance. "
        "Core RiskEngine must not depend on Pack types. "
        "Use the .severity string protocol instead of isinstance checks."
    )

    assert not any("RejectReason" in l for l in import_lines), (
        "ADR-006 violation: engine.py imports RejectReason. Use reason.severity == 'reject' instead."
    )

    assert not any("EscalateReason" in l for l in import_lines), (
        "ADR-006 violation: engine.py imports EscalateReason. Use reason.severity == 'escalate' instead."
    )


def test_engine_py_does_not_contain_finance_field_names():
    """RiskEngine must not hardcode finance-domain field names."""
    engine_path = GOVERNANCE / "risk_engine" / "engine.py"
    assert engine_path.exists(), f"Target file missing: {engine_path}"
    content = engine_path.read_text()

    forbidden = [
        "stop_loss",
        "is_chasing",
        "is_revenge_trade",
        "max_loss_usdt",
        "position_size_usdt",
        "risk_unit_usdt",
    ]

    for field in forbidden:
        assert field not in content, (
            f"ADR-006 violation: engine.py contains finance field '{field}'. "
            f"All domain validation is delegated to pack_policy."
        )


def test_review_closure_does_not_hardcode_outcome_type():
    """Review closure must use outcome_ref_type generic refs, not hard FK."""
    reviews_path = ROOT / "capabilities" / "workflow" / "reviews.py"
    content = reviews_path.read_text()

    # outcome_ref_type is checked as a string, never hardcoded to a specific ORM class
    assert "FinanceManualOutcomeORM" not in content, (
        "Architecture violation: review closure hardcodes FinanceManualOutcomeORM. "
        "outcome_ref_type must be resolved generically, not via Pack-specific ORM import."
    )
