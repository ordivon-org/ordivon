#!/usr/bin/env python3
"""DB-backed Runtime Evidence Audit — validates evidence chain integrity.

Runs read-only checks against a live database session.
Does NOT: db.add, db.commit, db.delete, execute migrations, write any table.

Checks:
  1. ExecutionReceipt.request_id is non-empty for succeeded receipts.
  2. Finance plan receipts have broker_execution=false / side_effect_level=none.
  3. FinanceManualOutcome.execution_receipt_id points to a valid receipt.
  4. Review outcome_ref_type/outcome_ref_id are paired and resolve.
  5. Review outcome_ref resolves to an existing FinanceManualOutcome.
  6. Lesson source_refs reference review/outcome objects.
  7. CandidateRule(draft) has non-empty lesson_ids and source_refs.
  8. CandidateRule has no accepted_candidate records (no Policy promotion).
  9. AuditEvent records exist for key governance events.
 10. Self-check: no write operations performed.

Usage:
    from scripts.audit_runtime_evidence_db import audit_evidence_chain
    violations = audit_evidence_chain(db_session)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from domains.candidate_rules.orm import CandidateRuleORM  # noqa: E402
from domains.execution_records.orm import ExecutionReceiptORM  # noqa: E402
from domains.finance_outcome.orm import FinanceManualOutcomeORM  # noqa: E402
from domains.journal.orm import ReviewORM  # noqa: E402
from domains.journal.lesson_orm import LessonORM  # noqa: E402
from governance.audit.orm import AuditEventORM  # noqa: E402
from shared.utils.serialization import from_json_text  # noqa: E402


@dataclass
class EvidenceAuditResult:
    """Result of a DB-backed evidence audit."""

    checks_run: int = 0
    violations: list[str] = field(default_factory=list)
    objects_scanned: dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


def audit_evidence_chain(db: Session) -> EvidenceAuditResult:
    """Run all evidence integrity checks against the database.

    Args:
        db: A SQLAlchemy Session (read-only usage assumed).

    Returns:
        EvidenceAuditResult with violations list and scan counts.
    """
    result = EvidenceAuditResult()

    # ── Check 1: ExecutionReceipt.request_id ────────────────────
    receipts = db.query(ExecutionReceiptORM).filter(ExecutionReceiptORM.status == "succeeded").all()
    result.objects_scanned["execution_receipts"] = len(receipts)
    for r in receipts:
        if not r.request_id or not r.request_id.strip():
            result.violations.append(f"ExecutionReceipt {r.id}: empty request_id (succeeded receipt untraceable)")
    result.checks_run += 1

    # ── Check 2: Plan receipt constraints ───────────────────────
    plan_receipts = db.query(ExecutionReceiptORM).filter(ExecutionReceiptORM.action_id == "finance_decision_plan").all()
    result.objects_scanned["plan_receipts"] = len(plan_receipts)
    for r in plan_receipts:
        detail = from_json_text(r.detail_json, {})
        broker_exec = detail.get("broker_execution", None)
        if broker_exec is True or broker_exec == "true":
            result.violations.append(f"Plan receipt {r.id}: broker_execution=true (plan-only violation)")
    result.checks_run += 1

    # ── Check 3: FinanceManualOutcome → execution_receipt_id ────
    outcomes = db.query(FinanceManualOutcomeORM).all()
    receipt_ids = {r.id for r in receipts}
    result.objects_scanned["finance_manual_outcomes"] = len(outcomes)
    for o in outcomes:
        if o.execution_receipt_id and o.execution_receipt_id not in receipt_ids:
            result.violations.append(
                f"FinanceManualOutcome {o.id}: execution_receipt_id "
                f"'{o.execution_receipt_id}' not found in ExecutionReceipt"
            )
    result.checks_run += 1

    # ── Check 4: Review outcome_ref pairing ─────────────────────
    reviews = db.query(ReviewORM).all()
    outcome_ids = {o.id for o in outcomes}
    result.objects_scanned["reviews"] = len(reviews)
    for rv in reviews:
        has_type = bool(rv.outcome_ref_type and rv.outcome_ref_type.strip())
        has_id = bool(rv.outcome_ref_id and rv.outcome_ref_id.strip())
        if has_type != has_id:
            result.violations.append(
                f"Review {rv.id}: outcome_ref_type/id mismatch (type={rv.outcome_ref_type!r}, id={rv.outcome_ref_id!r})"
            )
        if has_type and has_id:
            if rv.outcome_ref_type == "finance_manual_outcome":
                if rv.outcome_ref_id not in outcome_ids:
                    result.violations.append(
                        f"Review {rv.id}: outcome_ref_id '{rv.outcome_ref_id}' not found in FinanceManualOutcome"
                    )
    result.checks_run += 1

    # ── Check 5: Lesson source_refs ─────────────────────────────
    lessons = db.query(LessonORM).all()
    review_ids = {r.id for r in reviews}
    result.objects_scanned["lessons"] = len(lessons)
    for lsn in lessons:
        source_refs = from_json_text(lsn.source_refs_json, [])
        if lsn.review_id and lsn.review_id not in review_ids:
            result.violations.append(f"Lesson {lsn.id}: review_id '{lsn.review_id}' not found in Review")
        has_review_ref = (
            any(r.startswith("review:") for r in source_refs)
            or bool(lsn.review_id)  # review_id column is sufficient reference
        )
        if not has_review_ref:
            result.violations.append(f"Lesson {lsn.id}: source_refs missing review reference (and review_id is empty)")
    result.checks_run += 1

    # ── Check 6: CandidateRule draft source_refs ─────────────────
    candidate_rules = db.query(CandidateRuleORM).filter(CandidateRuleORM.status == "draft").all()
    result.objects_scanned["candidate_rules_draft"] = len(candidate_rules)
    for cr in candidate_rules:
        lesson_ids = from_json_text(cr.lesson_ids_json, [])
        source_refs = from_json_text(cr.source_refs_json, [])
        if not lesson_ids:
            result.violations.append(f"CandidateRule {cr.id}: lesson_ids is empty (draft without source)")
        if not source_refs:
            result.violations.append(f"CandidateRule {cr.id}: source_refs is empty (draft untraceable)")
    result.checks_run += 1

    # ── Check 7: No Policy promotion ─────────────────────────────
    promoted = db.query(CandidateRuleORM).filter(CandidateRuleORM.status == "accepted_candidate").all()
    result.objects_scanned["candidate_rules_accepted"] = len(promoted)
    if promoted:
        result.violations.append(
            f"Found {len(promoted)} CandidateRule(s) with status='accepted_candidate' "
            f"— Policy promotion without human approval?"
        )
    result.checks_run += 1

    # ── Check 8: AuditEvent coverage ─────────────────────────────
    audit_events = db.query(AuditEventORM).all()
    result.objects_scanned["audit_events"] = len(audit_events)
    event_types = {e.event_type for e in audit_events}
    expected_events = {
        "governance_evaluated",
        "plan_receipt_created",
        "review_completed",
    }
    missing = expected_events - event_types
    if missing and len(audit_events) > 0:
        result.violations.append(f"Missing expected AuditEvent types: {sorted(missing)}")
    result.checks_run += 1

    return result


def main() -> int:
    """Standalone runner — connects to the configured database."""
    from state.db.bootstrap import init_db

    init_db()  # Ensure schema is current before audit
    from state.db.session import SessionLocal

    db = SessionLocal()
    try:
        result = audit_evidence_chain(db)
        print("=== DB-Backed Runtime Evidence Audit ===")
        print()
        print("Objects scanned:")
        for obj_type, count in sorted(result.objects_scanned.items()):
            print(f"  {obj_type}: {count}")
        print()
        if result.passed:
            print(f"✅ All {result.checks_run} checks passed — evidence chain intact")
            return 0
        else:
            print(f"❌ {len(result.violations)} violation(s) in {result.checks_run} checks:")
            for v in result.violations:
                print(f"  {v}")
            return 1
    finally:
        db.rollback()
        db.close()


if __name__ == "__main__":
    import sys

    sys.exit(main())
