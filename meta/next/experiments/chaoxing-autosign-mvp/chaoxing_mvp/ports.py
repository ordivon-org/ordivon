from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, Sequence

from .models import ActionResult, Activity, ActivityIdentity, CourseIdentity


class SessionPort(Protocol):
    def ensure_domain_session(self) -> str:
        """Return the authenticated account identity or raise on failure."""


class DiscoveryPort(Protocol):
    def list_courses(self, account_id: str) -> Sequence[CourseIdentity]: ...

    def list_active_activities(self, course: CourseIdentity) -> Sequence[Activity]: ...


class SubmissionPort(Protocol):
    def submit(self, activity: Activity) -> ActionResult: ...

    def verify(self, activity: ActivityIdentity) -> bool | None:
        """True=confirmed, False=confirmed not successful, None=unknown."""


class NotifierPort(Protocol):
    def notify(self, title: str, message: str) -> None: ...


@dataclass(slots=True)
class Ports:
    session: SessionPort
    discovery: DiscoveryPort
    submission: SubmissionPort
    notifier: NotifierPort
