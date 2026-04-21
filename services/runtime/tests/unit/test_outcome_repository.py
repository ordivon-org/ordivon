from domains.strategy.outcome_models import OutcomeSnapshot
from domains.strategy.outcome_repository import OutcomeRepository
from state.db.bootstrap import init_db
from state.db.session import SessionLocal
from shared.enums.domain import OutcomeState


def test_outcome_repository_create_and_list_for_recommendation():
    init_db()
    db = SessionLocal()

    try:
        repo = OutcomeRepository(db)
        repo.create(
            OutcomeSnapshot(
                recommendation_id="reco-123",
                outcome_state=OutcomeState.SATISFIED,
                observed_metrics={"pnl_pct": 0.12},
                evidence_refs=["report://1"],
                trigger_reason="profit_target_hit",
            )
        )

        rows = repo.list_for_recommendation("reco-123")

        assert rows
        assert rows[0].recommendation_id == "reco-123"
        assert rows[0].outcome_state == OutcomeState.SATISFIED.value
    finally:
        db.close()
