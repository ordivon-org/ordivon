import json
from pfios.orchestrator.engine import PFIOSOrchestrator
from pfios.domain.analysis.models import AnalysisRequest
from pfios.core.db.session import SessionLocal
from pfios.domain.recommendation.repository import RecommendationRepository
from pfios.domain.usage.repository import UsageSnapshotRepository
from pfios.domain.audit.repository import AuditEventRepository
from pfios.domain.lessons.repository import LessonRepository


def main():
    print("[START] Step 3.5 Wiring Smoke Test")
    orch = PFIOSOrchestrator()
    db = SessionLocal()

    try:
        # 1. Run Analysis (This should trigger Recommendation, Usage, and 2 Audits)
        print("Running Analysis...")
        req = AnalysisRequest(
            query="Should I buy more NVDA?",
            symbol="NVDA",
            timeframe="daily",
        )
        report = orch.execute_analyze(req)
        # We need to extract the analysis_id from the report meta (it's in the repo to be sure)
        # For smoke test, we just check recent rows
        reco_repo = RecommendationRepository(db)
        usage_repo = UsageSnapshotRepository(db)
        audit_repo = AuditEventRepository(db)

        recent_recos = reco_repo.list_recent(limit=1)
        recent_usage = usage_repo.list_recent(limit=1)
        recent_audits = audit_repo.list_recent(limit=10)

        assert len(recent_recos) > 0, "No recommendation was generated in main chain!"
        reco_id = recent_recos[0].id  # Access ID while session is active
        assert len(recent_usage) > 0, "Usage snapshot was not updated in main chain!"

        audit_types = [a.event_type for a in recent_audits]
        assert "analysis_completed" in audit_types, "Analysis audit event missing!"
        assert "recommendation_generated" in audit_types, "Recommendation audit event missing!"

        print("[OK] Analysis -> Recommendation -> Usage -> Audit wiring confirmed.")

        # 2. Mock a Review Complete (This should trigger Lesson and Lesson Audit)
        from pfios.domain.review.service import ReviewService
        from pfios.domain.review.repository import ReviewRepository
        from pfios.domain.lessons.service import LessonService
        from pfios.domain.common.enums import ReviewVerdict
        from pfios.audit.auditor import RiskAuditor

        auditor = RiskAuditor()
        lesson_repo = LessonRepository(db)
        lesson_service = LessonService(lesson_repo)
        review_service = ReviewService(ReviewRepository(db), lesson_service, auditor)

        from pfios.domain.review.models import Review
        review = review_service.create(Review(recommendation_id=reco_id))

        print("Completing Review...")
        _, lessons = review_service.complete_review(
            review_id=review.id,
            observed_outcome="Bullish target met",
            verdict=ReviewVerdict.VALIDATED,
            variance_summary="Executed as planned",
            cause_tags=["data_gap"],
            lessons=["Wiring works perfectly"],
            followup_actions=[]
        )

        assert len(lessons) == 1
        
        # Use fresh session to see events from independent Auditor session
        verif_db = SessionLocal()
        try:
            verif_audit_repo = AuditEventRepository(verif_db)
            recent_audits_after = verif_audit_repo.list_recent(limit=20)
            audit_types_after = [a.event_type for a in recent_audits_after]
            assert "lesson_persisted" in audit_types_after, "Lesson audit event missing!"
        finally:
            verif_db.close()

        print("[OK] Review -> Lesson -> Audit wiring confirmed.")
        print("[WIN] Step 3.5 smoke test passed.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
