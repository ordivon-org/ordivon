"""
Phase 5 Smoke Test: Recommendation → Review → Observability 全闭环验证
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pfios.core.db.session import get_db_connection, init_db
from pfios.orchestrator.recommendation_tracker import RecommendationTracker
from pfios.orchestrator.review_engine import ReviewEngine
from pfios.observability.usage_tracker import UsageTracker
from pfios.domain.recommendation.models import LifecycleStatus
from pfios.domain.recommendation.state_machine import can_transition


def main():
    print("=" * 60)
    print("Phase 5 Smoke Test: Recommendation → Review → Observability")
    print("=" * 60)

    # 0. Init DB
    init_db()
    print("\n[OK] Database initialized")

    # ─── 1. Recommendation Tracker ──────────────────────
    print("\n--- Test 1: Auto-generate recommendation ---")
    reco_id = RecommendationTracker.auto_generate_if_needed(
        analysis_result={
            "action_plan": {"action": "accumulate"},
            "decision": "allow",
            "thesis": {"confidence": 0.82, "symbol": "ETH/USDT"},
            "metadata": {"symbol": "ETH/USDT"},
        },
        report_id="rpt_test_001",
        audit_id="aud_test_001",
    )
    assert reco_id is not None, "Should have generated a recommendation"
    print(f"  Generated: {reco_id}")

    # Verify it's queryable
    reco = RecommendationTracker.get_by_id(reco_id)
    assert reco is not None
    assert reco["lifecycle_status"] == "generated"
    print(f"  Status: {reco['lifecycle_status']}")

    # Should NOT generate for 'observe' (not in whitelist)
    none_id = RecommendationTracker.auto_generate_if_needed(
        analysis_result={"action_plan": {"action": "observe"}, "decision": "allow", "thesis": {"confidence": 0.9}},
        report_id="rpt_test_002",
    )
    assert none_id is None, "Should NOT generate for 'observe'"
    print("  Correctly skipped 'observe' action")

    # Should NOT generate for blocked decisions
    none_id2 = RecommendationTracker.auto_generate_if_needed(
        analysis_result={"action_plan": {"action": "accumulate"}, "decision": "block", "thesis": {"confidence": 0.9}},
        report_id="rpt_test_003",
    )
    assert none_id2 is None, "Should NOT generate for blocked decisions"
    print("  Correctly skipped blocked decision")
    print("[PASS] Test 1")

    # ─── 2. State Machine Transitions ───────────────────
    print("\n--- Test 2: State machine transitions ---")

    # generated → adopted
    RecommendationTracker.transition(reco_id, LifecycleStatus.ADOPTED, user_note="Looks good, adopting")
    reco = RecommendationTracker.get_by_id(reco_id)
    assert reco["lifecycle_status"] == "adopted"
    assert reco["adopted"] == True
    print(f"  generated → adopted: OK (adopted={reco['adopted']})")

    # adopted → tracking
    RecommendationTracker.transition(reco_id, LifecycleStatus.TRACKING)
    reco = RecommendationTracker.get_by_id(reco_id)
    assert reco["lifecycle_status"] == "tracking"
    print(f"  adopted → tracking: OK")

    # tracking → due_review
    RecommendationTracker.transition(reco_id, LifecycleStatus.DUE_REVIEW)
    reco = RecommendationTracker.get_by_id(reco_id)
    assert reco["lifecycle_status"] == "due_review"
    print(f"  tracking → due_review: OK")

    # Illegal transition: due_review → adopted (should fail)
    try:
        RecommendationTracker.transition(reco_id, LifecycleStatus.ADOPTED)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  due_review → adopted: Correctly blocked ({e})")

    # due_review → reviewed
    RecommendationTracker.transition(reco_id, LifecycleStatus.REVIEWED)
    reco = RecommendationTracker.get_by_id(reco_id)
    assert reco["lifecycle_status"] == "reviewed"
    assert reco["review_status"] == "reviewed"
    print(f"  due_review → reviewed: OK (review_status={reco['review_status']})")

    # reviewed → archived
    RecommendationTracker.transition(reco_id, LifecycleStatus.ARCHIVED)
    reco = RecommendationTracker.get_by_id(reco_id)
    assert reco["lifecycle_status"] == "archived"
    print(f"  reviewed → archived: OK (terminal state)")
    print("[PASS] Test 2")

    # ─── 3. Review Engine ──────────────────────────────
    print("\n--- Test 3: Review engine ---")

    # Generate a new reco for review testing
    reco_id2 = RecommendationTracker.auto_generate_if_needed(
        analysis_result={
            "action_plan": {"action": "reduce"},
            "decision": "warn",
            "thesis": {"confidence": 0.65, "symbol": "BTC/USDT"},
            "metadata": {"symbol": "BTC/USDT"},
        },
        report_id="rpt_test_004",
    )
    RecommendationTracker.transition(reco_id2, LifecycleStatus.ADOPTED)

    # Generate skeleton
    skeleton = ReviewEngine.generate_skeleton("rpt_test_004", reco_id2)
    assert skeleton["symbol"] == "BTC/USDT"
    assert skeleton["linked_recommendation_id"] == reco_id2
    print(f"  Skeleton generated for {skeleton['symbol']}")

    # Submit review
    skeleton["actual_outcome"] = "Price dropped 3% as expected"
    skeleton["deviation"] = "Timing was off by 2 days"
    skeleton["mistake_tags"] = "timing"
    skeleton["lessons"] = [
        {"lesson_type": "timing", "lesson_text": "Should have waited for confirmation candle"},
        {"lesson_type": "risk", "lesson_text": "Position size was appropriate"},
    ]
    skeleton["new_rule_candidate"] = "Wait for 4h close above resistance before entry"

    review_id = ReviewEngine.submit_review(skeleton)
    print(f"  Review submitted: {review_id}")

    # Verify recommendation's review_status was updated
    reco2 = RecommendationTracker.get_by_id(reco_id2)
    assert reco2["review_status"] == "reviewed"
    print(f"  Recommendation review_status auto-updated to: {reco2['review_status']}")

    # Query recent reviews
    recent = ReviewEngine.get_recent_reviews(limit=5)
    assert len(recent) >= 1
    print(f"  Recent reviews count: {len(recent)}")
    print("[PASS] Test 3")

    # ─── 4. Usage Tracker / Observability ──────────────
    print("\n--- Test 4: Usage tracker ---")

    # Sync daily usage
    usage = UsageTracker.sync_daily_usage()
    print(f"  Daily usage: runs={usage['runs']} recos={usage['recos']} reviews={usage['reviews']} blocks={usage['blocks']}")

    # Report issues
    issue_p1 = UsageTracker.report_issue("P1", "dashboard", "Chart rendering slow on mobile")
    issue_p2 = UsageTracker.report_issue("P2", "recommendation", "Missing tooltip on confidence score")
    print(f"  Issues reported: P1={issue_p1}, P2={issue_p2}")

    # Resolve one
    UsageTracker.resolve_issue(issue_p2, "fixed")
    open_issues = UsageTracker.get_open_issues()
    assert any(i["issue_id"] == issue_p1 for i in open_issues), "P1 should still be open"
    assert not any(i["issue_id"] == issue_p2 for i in open_issues), "P2 should be resolved"
    print(f"  Open issues after resolve: {len(open_issues)}")

    # Weekly summary
    summary = UsageTracker.weekly_validation_summary()
    print(f"  Weekly: days={summary['days_used']} go_no_go={summary['go_no_go']}")
    print(f"  P0={summary['open_p0_count']} P1={summary['open_p1_count']}")
    if summary["key_lessons"]:
        for lesson in summary["key_lessons"]:
            print(f"    → {lesson}")
    print("[PASS] Test 4")

    # ─── 5. Actionable queries ─────────────────────────
    print("\n--- Test 5: Actionable queries ---")
    actionable = RecommendationTracker.get_actionable()
    print(f"  Actionable recommendations: {len(actionable)}")
    pending_reviews = ReviewEngine.get_pending_reviews()
    print(f"  Pending reviews: {len(pending_reviews)}")
    print("[PASS] Test 5")

    print("\n" + "=" * 60)
    print("Phase 5 Smoke Test Completed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
