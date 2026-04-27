"""Coding Pack architecture boundary tests — verify Pack isolation from Core.

Rules:
  1. governance/ must not import packs.coding
  2. packs/coding must not import governance internals
     (public contracts like GovernanceDecision are acceptable if needed)
  3. packs/coding must not import broker/order/trade
  4. packs/coding must not import ExecutionRequest/ExecutionReceipt
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_governance_does_not_import_packs_coding():
    """governance/ must never import packs.coding."""
    governance_dir = ROOT / "governance"
    violations = []
    for py_file in governance_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        text = py_file.read_text(encoding="utf-8")
        import_lines = [l for l in text.splitlines() if l.strip().startswith(("from ", "import "))]
        for line in import_lines:
            if "packs.coding" in line:
                violations.append(f"{py_file.relative_to(ROOT)}: {line.strip()}")
    assert violations == [], "governance must not import packs.coding:\n" + "\n".join(violations)


def test_packs_coding_does_not_import_broker_order_trade():
    """packs/coding must not import broker/order/trade modules."""
    coding_dir = ROOT / "packs" / "coding"
    forbidden = ["broker", "place_order", "execute_trade", "ExecutionRequest", "ExecutionReceipt"]
    violations = []
    for py_file in coding_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        text = py_file.read_text(encoding="utf-8")
        import_lines = [l for l in text.splitlines() if l.strip().startswith(("from ", "import "))]
        for line in import_lines:
            for word in forbidden:
                if word in line:
                    violations.append(f"{py_file.relative_to(ROOT)}: {line.strip()}")
                    break
    assert violations == [], "packs/coding must not import broker/order/trade:\n" + "\n".join(violations)


def test_packs_coding_does_not_import_governance_internals():
    """packs/coding may import public contracts but not internal implementation."""
    coding_dir = ROOT / "packs" / "coding"
    # These governance modules are internal implementation — forbidden
    forbidden_internals = [
        "governance.risk_engine",
        "governance.audit.auditor",
        "governance.approval",
    ]
    violations = []
    for py_file in coding_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        text = py_file.read_text(encoding="utf-8")
        import_lines = [l for l in text.splitlines() if l.strip().startswith(("from ", "import "))]
        for line in import_lines:
            for forbidden in forbidden_internals:
                if forbidden in line:
                    violations.append(f"{py_file.relative_to(ROOT)}: {line.strip()}")
    assert violations == [], "packs/coding must not import governance internals:\n" + "\n".join(violations)
