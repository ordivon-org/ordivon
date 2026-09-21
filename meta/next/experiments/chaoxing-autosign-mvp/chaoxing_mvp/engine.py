from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .ledger import ActivityLedger
from .models import (
    Activity,
    ActivityState,
    ExecutionMode,
    ParseOutcome,
    SemanticOutcome,
    TransportOutcome,
)
from .policy import SignPlanner
from .ports import Ports


@dataclass(slots=True)
class ScanStats:
    courses: int = 0
    activities_seen: int = 0
    activities_processed: int = 0
    confirmed: int = 0
    user_action_required: int = 0
    retryable_failures: int = 0
    terminal_failures: int = 0


class AutoSignEngine:
    def __init__(self, ports: Ports, ledger: ActivityLedger, planner: SignPlanner | None = None):
        self.ports = ports
        self.ledger = ledger
        self.planner = planner or SignPlanner()

    def scan_once(self) -> ScanStats:
        stats = ScanStats()
        account_id = self.ports.session.ensure_domain_session()
        courses = self.ports.discovery.list_courses(account_id)
        stats.courses = len(courses)

        for course in courses:
            for activity in self.ports.discovery.list_active_activities(course):
                stats.activities_seen += 1
                self.ledger.observe(activity)
                if self.ledger.recovery_required(activity.identity):
                    stats.activities_processed += 1
                    self._recover_uncertain(activity, stats)
                    continue
                if not self.ledger.should_process(activity.identity):
                    continue
                stats.activities_processed += 1
                self._process(activity, stats)

        return stats

    def _recover_uncertain(self, activity: Activity, stats: ScanStats) -> None:
        self.ledger.transition(
            activity.identity,
            ActivityState.VERIFYING,
            detail="recovering uncertain prior submission by verification",
        )
        verified = self.ports.submission.verify(activity.identity)
        if verified is True:
            self.ledger.transition(activity.identity, ActivityState.CONFIRMED_SUCCESS)
            stats.confirmed += 1
            self.ports.notifier.notify("Sign-in confirmed", activity.identity.key)
        elif verified is False:
            self.ledger.transition(
                activity.identity,
                ActivityState.FAILED_RETRYABLE,
                detail="recovery verification confirmed no successful submission",
            )
            stats.retryable_failures += 1
        else:
            self.ledger.transition(
                activity.identity,
                ActivityState.UNKNOWN,
                detail="recovery verification remains unknown; not resubmitting",
            )
            stats.retryable_failures += 1

    def _process(self, activity: Activity, stats: ScanStats) -> None:
        plan = self.planner.plan(activity)
        self.ledger.transition(
            activity.identity,
            ActivityState.CLASSIFIED,
            detail=f"{plan.mode.value}: {plan.reason}",
        )

        if plan.mode is ExecutionMode.USER_VERIFICATION_REQUIRED:
            self.ledger.transition(
                activity.identity,
                ActivityState.USER_ACTION_REQUIRED,
                detail=plan.reason,
            )
            stats.user_action_required += 1
            self.ports.notifier.notify(
                "Sign-in requires verification",
                f"{activity.identity.key}: {plan.reason}",
            )
            return

        if plan.mode is ExecutionMode.UNSUPPORTED:
            self.ledger.transition(
                activity.identity,
                ActivityState.FAILED_TERMINAL,
                detail=plan.reason,
            )
            stats.terminal_failures += 1
            self.ports.notifier.notify(
                "Unsupported sign-in activity",
                f"{activity.identity.key}: {plan.reason}",
            )
            return

        self.ledger.transition(activity.identity, ActivityState.READY, detail=plan.reason)
        self.ledger.transition(
            activity.identity,
            ActivityState.SUBMITTING,
            increment_attempt=True,
            detail="submission adapter invoked",
        )
        result = self.ports.submission.submit(activity)

        if result.transport is not TransportOutcome.OK:
            self.ledger.transition(
                activity.identity,
                ActivityState.FAILED_RETRYABLE,
                detail=f"transport={result.transport.value}; {result.detail}",
            )
            stats.retryable_failures += 1
            return

        if result.parse is not ParseOutcome.OK:
            self.ledger.transition(
                activity.identity,
                ActivityState.UNKNOWN,
                detail=result.detail or f"parse={result.parse.value}",
            )
            stats.retryable_failures += 1
            return

        if result.semantic is SemanticOutcome.REJECTED:
            self.ledger.transition(
                activity.identity,
                ActivityState.FAILED_TERMINAL,
                detail=result.detail or "semantic rejection",
            )
            stats.terminal_failures += 1
            return

        if not result.semantically_accepted:
            self.ledger.transition(
                activity.identity,
                ActivityState.UNKNOWN,
                detail=result.detail or "ambiguous result",
            )
            stats.retryable_failures += 1
            return

        self.ledger.transition(activity.identity, ActivityState.SUBMITTED, detail=result.detail)
        self.ledger.transition(activity.identity, ActivityState.VERIFYING)
        verified = self.ports.submission.verify(activity.identity)

        if verified is True:
            self.ledger.transition(activity.identity, ActivityState.CONFIRMED_SUCCESS)
            stats.confirmed += 1
            self.ports.notifier.notify("Sign-in confirmed", activity.identity.key)
        elif verified is False:
            self.ledger.transition(
                activity.identity,
                ActivityState.FAILED_TERMINAL,
                detail="remote verification confirmed failure",
            )
            stats.terminal_failures += 1
        else:
            self.ledger.transition(
                activity.identity,
                ActivityState.UNKNOWN,
                detail="submission accepted but remote confirmation is unknown",
            )
            stats.retryable_failures += 1
