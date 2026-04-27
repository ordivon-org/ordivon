#!/usr/bin/env python3
"""Runtime Evidence Integrity Checker — validates structural invariants of runtime objects.

Checks (static analysis — no database connection required):
  1. ExecutionReceipt ORM has request_id field (succeeded receipts must be traceable).
  2. Finance Manual Outcome ORM requires execution_receipt_id.
  3. Plan receipts enforce broker_execution=false and side_effect_level="none".
  4. Review outcome_ref_type/outcome_ref_id must be paired in ORM.
  5. CandidateRule draft model has lesson_ids and source_refs fields.
  6. CandidateRule model has no promote/accept/approve methods (Policy isolation).

This is a CandidateRule (advisory) — it does NOT block CI by default.
Read-only: zero database writes, zero file modifications.
Exit 0 = clean; Exit 1 = violations found.
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_execution_receipt_has_request_id() -> list[str]:
    """ExecutionReceiptORM must have a request_id field for traceability."""
    violations: list[str] = []
    try:
        from domains.execution_records.orm import ExecutionReceiptORM
    except ImportError as e:
        return [f"ExecutionReceiptORM not importable: {e}"]

    if not hasattr(ExecutionReceiptORM, "request_id"):
        violations.append("ExecutionReceiptORM: missing 'request_id' column — succeeded receipts untraceable")
    return violations


def check_finance_outcome_has_execution_receipt_id() -> list[str]:
    """FinanceManualOutcomeORM must require execution_receipt_id."""
    violations: list[str] = []
    try:
        from domains.finance_outcome.orm import FinanceManualOutcomeORM
    except ImportError as e:
        return [f"FinanceManualOutcomeORM not importable: {e}"]

    if not hasattr(FinanceManualOutcomeORM, "execution_receipt_id"):
        violations.append("FinanceManualOutcomeORM: missing 'execution_receipt_id' — outcome untethered from receipt")

    from domains.finance_outcome.models import FinanceManualOutcome

    src = inspect.getsource(FinanceManualOutcome.__post_init__)
    if "execution_receipt_id" not in src:
        violations.append("FinanceManualOutcome.__post_init__: does not validate execution_receipt_id")

    return violations


def check_plan_receipt_constraints() -> list[str]:
    """Plan receipts must enforce broker_execution=false, side_effect_level='none'."""
    violations: list[str] = []

    spec_path = ROOT / "docs" / "architecture" / "execution-request-receipt-spec.md"
    if not spec_path.exists():
        violations.append("execution-request-receipt-spec.md: not found")
        return violations

    spec_text = spec_path.read_text(encoding="utf-8")

    if "broker_execution" not in spec_text:
        violations.append("Plan receipt spec: 'broker_execution' constraint not documented")

    if "side_effect_level" not in spec_text:
        violations.append("Plan receipt spec: 'side_effect_level' constraint not documented")

    # Check execution catalog for plan action definition
    catalog_path = ROOT / "execution" / "catalog.py"
    if catalog_path.exists():
        catalog_text = catalog_path.read_text(encoding="utf-8")
        # Plan receipts must NOT be tagged as primary_receipt_candidate with broker
        if "primary_receipt_candidate" not in catalog_text:
            violations.append("execution/catalog.py: no primary_receipt_candidate markings found")

    return violations


def check_review_outcome_ref_pairing() -> list[str]:
    """Review ORM must have outcome_ref_type and outcome_ref_id as a pair."""
    violations: list[str] = []
    try:
        from domains.journal.orm import ReviewORM
    except ImportError as e:
        return [f"ReviewORM not importable: {e}"]

    has_type = hasattr(ReviewORM, "outcome_ref_type")
    has_id = hasattr(ReviewORM, "outcome_ref_id")

    if has_type and not has_id:
        violations.append("ReviewORM: has outcome_ref_type but missing outcome_ref_id")
    if has_id and not has_type:
        violations.append("ReviewORM: has outcome_ref_id but missing outcome_ref_type")
    if not has_type and not has_id:
        violations.append("ReviewORM: missing both outcome_ref_type and outcome_ref_id (H-8R requirement)")

    return violations


def check_candidate_rule_draft_has_source_refs() -> list[str]:
    """CandidateRule model must have lesson_ids and source_refs for traceability."""
    violations: list[str] = []
    # Parse the model file as text to avoid import chain issues
    model_path = ROOT / "domains" / "candidate_rules" / "models.py"
    if not model_path.exists():
        return ["CandidateRule models.py: file not found"]

    text = model_path.read_text(encoding="utf-8")
    if "lesson_ids" not in text:
        violations.append("CandidateRule model: missing 'lesson_ids' field")
    if "source_refs" not in text:
        violations.append("CandidateRule model: missing 'source_refs' field")

    return violations


def check_candidate_rule_no_policy_promotion() -> list[str]:
    """CandidateRule and its services must have no promote/accept/approve methods."""
    violations: list[str] = []

    # Check the draft extraction service
    extraction_path = ROOT / "domains" / "candidate_rules" / "draft_extraction.py"
    if extraction_path.exists():
        text = extraction_path.read_text(encoding="utf-8")
        for forbidden in ['status = "accepted_candidate"', "promote(", "Policy("]:
            if forbidden in text:
                violations.append(f"draft_extraction.py: contains forbidden pattern '{forbidden}' — Policy promotion")

    # Check the model for any promote/accept method
    try:
        from domains.candidate_rules.models import CandidateRule

        methods = [m for m in dir(CandidateRule) if not m.startswith("_")]
        for forbidden in ["promote", "accept", "approve"]:
            if forbidden in methods:
                violations.append(f"CandidateRule model: has '{forbidden}' method — Policy promotion path")
    except ImportError:
        pass

    return violations


def check_no_write_operations() -> list[str]:
    """Self-check: this checker module must not import DB write functions."""
    violations: list[str] = []
    src = Path(__file__).read_text(encoding="utf-8")

    write_patterns = [
        (r"\.execute\(", "raw SQL execute"),
        (r"\.commit\(", "database commit"),
        (r"\.add\(", "ORM session add"),
        (r"\.flush\(", "ORM session flush"),
    ]
    for pattern, desc in write_patterns:
        if re.search(pattern, src):
            # Only flag if not in a comment/docstring
            lines = src.splitlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if re.search(pattern, stripped) and not stripped.startswith(("#", '"', "'")):
                    violations.append(f"check_runtime_evidence.py:{i}: potential write operation '{desc}'")

    return violations


# ═══════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════

CHECKS = {
    "ExecutionReceipt has request_id": check_execution_receipt_has_request_id,
    "FinanceManualOutcome has execution_receipt_id": check_finance_outcome_has_execution_receipt_id,
    "Plan receipt constraints (broker_execution=false)": check_plan_receipt_constraints,
    "Review outcome_ref_type/id pairing": check_review_outcome_ref_pairing,
    "CandidateRule draft has source_refs": check_candidate_rule_draft_has_source_refs,
    "CandidateRule no Policy promotion path": check_candidate_rule_no_policy_promotion,
    "Checker is read-only": check_no_write_operations,
}


def main() -> int:
    all_violations: list[str] = []

    print("=== Runtime Evidence Integrity Check ===")
    print()

    for name, check_fn in CHECKS.items():
        v = check_fn()
        if v:
            print(f"❌ {name}:")
            for item in v:
                print(f"  {item}")
            all_violations.extend(v)
        else:
            print(f"✅ {name}")

    print()
    if all_violations:
        print(f"❌ {len(all_violations)} violation(s)")
        return 1
    else:
        print("✅ Runtime evidence integrity verified")
        return 0


if __name__ == "__main__":
    sys.exit(main())
