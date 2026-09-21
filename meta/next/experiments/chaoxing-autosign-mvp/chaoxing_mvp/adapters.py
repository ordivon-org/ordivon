from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .models import (
    ActionResult,
    Activity,
    ActivityIdentity,
    CourseIdentity,
    ParseOutcome,
    SemanticOutcome,
    TransportOutcome,
)


class ConsoleNotifier:
    def notify(self, title: str, message: str) -> None:
        print(f"[{title}] {message}")


class DisabledSubmissionAdapter:
    """Fail-closed default submission adapter.

    This preserves the full orchestration and state-machine boundary without shipping
    a presence-bypass or undocumented remote action implementation.
    """

    def submit(self, activity: Activity) -> ActionResult:
        return ActionResult(
            transport=TransportOutcome.UNKNOWN,
            parse=ParseOutcome.UNKNOWN,
            semantic=SemanticOutcome.UNKNOWN,
            detail="remote submission adapter is disabled",
        )

    def verify(self, activity: ActivityIdentity) -> bool | None:
        return None


@dataclass(slots=True)
class FakeSession:
    account_id: str = "demo-account"

    def ensure_domain_session(self) -> str:
        return self.account_id


@dataclass(slots=True)
class FakeDiscovery:
    courses: Sequence[CourseIdentity]
    activities_by_course: dict[str, Sequence[Activity]] = field(default_factory=dict)

    def list_courses(self, account_id: str) -> Sequence[CourseIdentity]:
        return [x for x in self.courses if x.account_id == account_id]

    def list_active_activities(self, course: CourseIdentity) -> Sequence[Activity]:
        return self.activities_by_course.get(course.key, ())


class FakeAcceptedSubmission:
    def __init__(self) -> None:
        self.submitted: set[str] = set()

    def submit(self, activity: Activity) -> ActionResult:
        self.submitted.add(activity.identity.key)
        return ActionResult(
            transport=TransportOutcome.OK,
            parse=ParseOutcome.OK,
            semantic=SemanticOutcome.ACCEPTED,
            detail="synthetic accepted result",
        )

    def verify(self, activity: ActivityIdentity) -> bool | None:
        return activity.key in self.submitted
