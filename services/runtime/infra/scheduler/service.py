from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infra.scheduler.models import ScheduledTrigger
from infra.scheduler.repository import SchedulerRepository
from shared.observability import increment_counter, span
from shared.time.clock import utc_now
from shared.utils.serialization import from_json_text, to_json_text


@dataclass(frozen=True, slots=True)
class SchedulerDispatchResult:
    trigger_id: str
    target_capability: str
    status: str
    detail: dict[str, Any]


class SchedulerService:
    """Infrastructure-owned trigger registration and dispatch."""

    def __init__(self) -> None:
        self._triggers: dict[str, ScheduledTrigger] = {}
        self._targets: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]] = {}

    def register_target(
        self,
        capability_name: str,
        handler: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> None:
        self._targets[capability_name] = handler

    def register_trigger(self, trigger: ScheduledTrigger) -> ScheduledTrigger:
        self._triggers[trigger.id] = trigger
        return trigger

    def list_triggers(self) -> tuple[ScheduledTrigger, ...]:
        return tuple(self._triggers.values())

    def dispatch(self, trigger_id: str) -> SchedulerDispatchResult:
        trigger = self._triggers[trigger_id]
        with span(
            "scheduler.dispatch",
            attributes={
                "scheduler.trigger_id": trigger.id,
                "scheduler.target_capability": trigger.target_capability,
            },
        ):
            if not trigger.is_enabled:
                increment_counter("scheduler_dispatch_total", attributes={"status": "disabled"})
                return SchedulerDispatchResult(
                    trigger_id=trigger.id,
                    target_capability=trigger.target_capability,
                    status="disabled",
                    detail={"reason": "trigger_disabled"},
                )

            handler = self._targets.get(trigger.target_capability)
            if handler is None:
                increment_counter("scheduler_dispatch_total", attributes={"status": "unavailable"})
                increment_counter("scheduler_dispatch_failures_total", attributes={"reason": "target_not_registered"})
                return SchedulerDispatchResult(
                    trigger_id=trigger.id,
                    target_capability=trigger.target_capability,
                    status="unavailable",
                    detail={"reason": "target_not_registered"},
                )

            detail = handler(dict(trigger.payload)) or {}
            self._triggers[trigger.id] = ScheduledTrigger(
                id=trigger.id,
                trigger_type=trigger.trigger_type,
                cron_or_interval=trigger.cron_or_interval,
                target_capability=trigger.target_capability,
                payload=dict(trigger.payload),
                is_enabled=trigger.is_enabled,
                last_dispatched_at=utc_now().isoformat(),
                dispatch_count=trigger.dispatch_count + 1,
            )
            increment_counter("scheduler_dispatch_total", attributes={"status": "dispatched"})
            return SchedulerDispatchResult(
                trigger_id=trigger.id,
                target_capability=trigger.target_capability,
                status="dispatched",
                detail=detail,
            )

    def dispatch_enabled(self) -> tuple[SchedulerDispatchResult, ...]:
        results: list[SchedulerDispatchResult] = []
        for trigger in self._triggers.values():
            if trigger.is_enabled:
                results.append(self.dispatch(trigger.id))
        return tuple(results)

    def save_to_file(self, path: str | Path) -> Path:
        target = Path(path)
        payload = [
            {
                "id": trigger.id,
                "trigger_type": trigger.trigger_type,
                "cron_or_interval": trigger.cron_or_interval,
                "target_capability": trigger.target_capability,
                "payload": dict(trigger.payload),
                "is_enabled": trigger.is_enabled,
                "last_dispatched_at": trigger.last_dispatched_at,
                "dispatch_count": trigger.dispatch_count,
            }
            for trigger in self._triggers.values()
        ]
        target.write_text(to_json_text(payload), encoding="utf-8")
        return target

    def load_from_file(self, path: str | Path) -> tuple[ScheduledTrigger, ...]:
        source = Path(path)
        if not source.exists():
            return ()
        payload = from_json_text(source.read_text(encoding="utf-8"), [])
        loaded: list[ScheduledTrigger] = []
        for raw in payload:
            trigger = ScheduledTrigger(
                id=str(raw["id"]),
                trigger_type=str(raw.get("trigger_type", "interval")),
                cron_or_interval=str(raw.get("cron_or_interval", "")),
                target_capability=str(raw.get("target_capability", "")),
                payload=dict(raw.get("payload", {})),
                is_enabled=bool(raw.get("is_enabled", True)),
                last_dispatched_at=raw.get("last_dispatched_at"),
                dispatch_count=int(raw.get("dispatch_count", 0) or 0),
            )
            self._triggers[trigger.id] = trigger
            loaded.append(trigger)
        return tuple(loaded)

    def save_to_repository(self, db) -> tuple[ScheduledTrigger, ...]:
        repository = SchedulerRepository(db)
        for trigger in self._triggers.values():
            repository.upsert(trigger)
        return self.list_triggers()

    def load_from_repository(self, db) -> tuple[ScheduledTrigger, ...]:
        repository = SchedulerRepository(db)
        loaded: list[ScheduledTrigger] = []
        for row in repository.list_all():
            trigger = repository.to_model(row)
            self._triggers[trigger.id] = trigger
            loaded.append(trigger)
        return tuple(loaded)
