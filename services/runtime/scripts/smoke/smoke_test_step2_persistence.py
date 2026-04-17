from pfios.core.db.bootstrap import init_db
from pfios.core.db.session import SessionLocal
from pfios.domain.analysis.models import AnalysisRequest
from pfios.domain.analysis.orm import AnalysisORM
from pfios.domain.audit.orm import AuditEventORM
from pfios.orchestrator.engine import PFIOSOrchestrator


def main():
    print("[START] Step 2 persistence smoke test")
    init_db()

    orchestrator = PFIOSOrchestrator()
    result = orchestrator.execute_analyze(
        AnalysisRequest(
            query="Analyze BTC market structure",
            symbol="BTC-USDT",
            timeframe="4h",
        )
    )

    db = SessionLocal()
    try:
        analysis_count = db.query(AnalysisORM).count()
        audit_count = db.query(AuditEventORM).count()
    finally:
        db.close()

    print("[OK] Analysis returned:", result["analysis_id"])
    print("[OK] analyses count:", analysis_count)
    print("[OK] audit events count:", audit_count)

    assert analysis_count >= 1
    assert audit_count >= 1

    print("[WIN] Step 2 persistence smoke test passed.")


if __name__ == "__main__":
    main()
