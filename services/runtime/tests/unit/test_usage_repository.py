from state.db.bootstrap import init_db
from state.db.session import SessionLocal
from state.usage.models import UsageSnapshot
from state.usage.repository import UsageSnapshotRepository


def test_usage_repository_create_and_list_recent():
    init_db()
    db = SessionLocal()

    try:
        repo = UsageSnapshotRepository(db)
        repo.create(
            UsageSnapshot(
                analyses_count=2,
                recommendations_generated_count=1,
                reviews_completed_count=1,
                metadata={"note": "usage-test"},
            )
        )

        rows = repo.list_recent(limit=5)

        assert rows
        assert rows[0].analyses_count >= 2
        assert rows[0].metadata_json is not None
    finally:
        db.close()
