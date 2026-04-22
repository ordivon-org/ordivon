from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from infra.scheduler import ScheduledTrigger, SchedulerService
from state.db.base import Base


def test_scheduler_dispatch_enabled_round_trips_through_repository():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        scheduler = SchedulerService()
        scheduler.register_target("dashboard_summary_refresh", lambda payload: {"refreshed": payload.get("scope")})
        scheduler.register_trigger(
            ScheduledTrigger(
                id="sched_dashboard_refresh",
                trigger_type="interval",
                cron_or_interval="PT10M",
                target_capability="dashboard_summary_refresh",
                payload={"scope": "dashboard"},
            )
        )
        scheduler.save_to_repository(db)
        db.commit()

        restored = SchedulerService()
        restored.register_target("dashboard_summary_refresh", lambda payload: {"refreshed": payload.get("scope")})
        restored.load_from_repository(db)
        results = restored.dispatch_enabled()
        restored.save_to_repository(db)
        db.commit()

        assert results[0].status == "dispatched"
        assert results[0].detail["refreshed"] == "dashboard"
        reloaded = restored.load_from_repository(db)
        assert reloaded[0].dispatch_count >= 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
