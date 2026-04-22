from pathlib import Path

from infra.scheduler import ScheduledTrigger, SchedulerService


def test_scheduler_registers_and_dispatches_low_risk_trigger():
    scheduler = SchedulerService()
    scheduler.register_target("pending_review_check", lambda payload: {"checked": payload.get("limit", 0)})
    trigger = scheduler.register_trigger(
        ScheduledTrigger(
            trigger_type="interval",
            cron_or_interval="PT15M",
            target_capability="pending_review_check",
            payload={"limit": 5},
        )
    )

    result = scheduler.dispatch(trigger.id)

    assert result.status == "dispatched"
    assert result.target_capability == "pending_review_check"
    assert result.detail["checked"] == 5


def test_scheduler_persists_and_reloads_triggers(tmp_path: Path):
    scheduler = SchedulerService()
    scheduler.register_target("pending_review_check", lambda payload: {"checked": payload.get("limit", 0)})
    trigger = scheduler.register_trigger(
        ScheduledTrigger(
            id="sched_test_1",
            trigger_type="interval",
            cron_or_interval="PT15M",
            target_capability="pending_review_check",
            payload={"limit": 3},
        )
    )
    scheduler.dispatch(trigger.id)
    file_path = tmp_path / "scheduler.json"
    scheduler.save_to_file(file_path)

    restored = SchedulerService()
    loaded = restored.load_from_file(file_path)

    assert loaded[0].id == "sched_test_1"
    assert loaded[0].dispatch_count == 1
    assert loaded[0].last_dispatched_at is not None
