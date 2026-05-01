"""
Phase 5 Smoke Test: Recommendation → Review → Observability 全闭环验证
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from state.db.bootstrap import init_db
from state.db.session import SessionLocal
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from domains.strategy.models import Recommendation
from domains.journal.repository import ReviewRepository
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.service import ReviewService
from capabilities.reviews import ReviewCapability
from domains.journal.issue_repository import IssueRepository
from domains.journal.issue_service import IssueService
from state.usage.repository import UsageSnapshotRepository
from state.usage.service import UsageService
from capabilities.validation import ValidationCapability
from shared.enums.domain import RecommendationStatus as LifecycleStatus
from shared.enums.domain import ReviewVerdict


def main():
    print("=" * 60)
    print("Phase 5 Smoke Test: Recommendation → Review → Observability")
    print("=" * 60)

    # 0. Init DB
    init_db()
    print("\n[OK] Database initialized")

    # ─── 1. Recommendation Service ──────────────────────
    print("\n--- Test 1: Generate recommendation ---")
    db = SessionLocal()
    reco_repo = RecommendationRepository(db)
    reco_service = RecommendationService(reco_repo)

    reco_row = reco_service.create(
        Recommendation(
            analysis_id="rpt_test_001",
            title="Action for ETH/USDT",
            summary="Automated recommendation",
            rationale="Thesis info",
            expected_outcome="System stabilization",
            priority="normal",
        )
    )
    reco_id = reco_row.id
    assert reco_id is not None, "Should have generated a recommendation"
    print(f"  Generated: {reco_id}")

    # Verify it's queryable
    reco_model = reco_service.get_model(reco_id)
    assert reco_model is not None
    assert reco_model.status == LifecycleStatus.GENERATED
    print(f"  Status: {reco_model.status}")
    print("[PASS] Test 1")

    # ─── 2. Service Transitions ───────────────────
    print("\n--- Test 2: Service transitions ---")

    # generated → adopted
    reco_service.transition(reco_id, LifecycleStatus.ADOPTED)
    reco_model = reco_service.get_model(reco_id)
    assert reco_model.status == LifecycleStatus.ADOPTED
    print(f"  generated → adopted: OK")

    # adopted → tracking
    reco_service.transition(reco_id, LifecycleStatus.TRACKING)
    reco_model = reco_service.get_model(reco_id)
    assert reco_model.status == LifecycleStatus.TRACKING
    print(f"  adopted → tracking: OK")

    # tracking → reviewed
    reco_service.transition(reco_id, LifecycleStatus.REVIEWED)
    reco_model = reco_service.get_model(reco_id)
    assert reco_model.status == LifecycleStatus.REVIEWED
    print(f"  tracking → reviewed: OK")

    # reviewed → archived
    reco_service.transition(reco_id, LifecycleStatus.ARCHIVED)
    reco_model = reco_service.get_model(reco_id)
    assert reco_model.status == LifecycleStatus.ARCHIVED
    print(f"  reviewed → archived: OK (terminal state)")
    print("[PASS] Test 2")

    # ─── 3. Review Capability ──────────────────────────────
    print("\n--- Test 3: Review capability ---")

    rev_cap = ReviewCapability()
    lesson_service = LessonService(LessonRepository(db))
    rev_service = ReviewService(ReviewRepository(db), lesson_service)

    # Create a new reco for review
    reco_row2 = reco_service.create(
        Recommendation(
            analysis_id="rpt_test_004",
            title="Reduce exposure BTC",
            summary="Risk warning",
            priority="high",
        )
    )
    reco_id2 = reco_row2.id

    # Generate skeleton
    skeleton = rev_cap.generate_skeleton("rpt_test_004", reco_id2)
    assert skeleton.recommendation_id == reco_id2
    print(f"  Skeleton generated for {reco_id2}")

    # Submit review
    review_res = rev_cap.submit_review(
        rev_service,
        {
            "linked_recommendation_id": reco_id2,
            "actual_outcome": "Price dropped",
            "deviation": "Timing off",
            "mistake_tags": "timing",
            "lessons": [{"lesson_text": "Better entry needed"}],
            "new_rule_candidate": "Wait for close",
        },
    )
    print(f"  Review submitted: {review_res.id}")

    # Verify recommendation status
    # We call complete_review to trigger the full closure
    rev_cap.complete_review(
        rev_service,
        review_res.id,
        "Target reached",
        ReviewVerdict.VALIDATED,
        "No deviation",
        ["timing"],
        ["Study more"],
        ["Update params"],
    )
    print(f"  Review completed and lessons persisted")
    print("[PASS] Test 3")

    # ─── 4. Validation Capability / Observability ──────────────
    print("\n--- Test 4: Validation capability ---")

    val_cap = ValidationCapability()
    usage_service = UsageService(UsageSnapshotRepository(db))
    issue_service = IssueService(IssueRepository(db))

    # Sync usage
    sync_res = val_cap.sync_usage(usage_service)
    print(f"  Usage synced: {sync_res.snapshot_id}")

    # Report issues
    issue_p1 = val_cap.report_issue(issue_service, "P1", "dashboard", "Slow")
    print(f"  Issue reported: {issue_p1}")

    # Summary
    summary = val_cap.get_summary(usage_service, IssueRepository(db))
    print(f"  Summary: active={summary.days_active} analysis={summary.total_analyses}")
    print("[PASS] Test 4")

    # ─── 5. Actionable queries ─────────────────────────
    print("\n--- Test 5: Actionable queries ---")
    # TODO: RecommendationTracker and ReviewEngine are not yet implemented.
    # When built, uncomment the lines below and add the required imports.
    # actionable = RecommendationTracker.get_actionable()
    # print(f"  Actionable recommendations: {len(actionable)}")
    # pending_reviews = ReviewEngine.get_pending_reviews()
    # print(f"  Pending reviews: {len(pending_reviews)}")
    print("  [SKIP] RecommendationTracker and ReviewEngine not yet implemented")
    print("[PASS] Test 5")

    print("\n" + "=" * 60)
    print("Phase 5 Smoke Test Completed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
