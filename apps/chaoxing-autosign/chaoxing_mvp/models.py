from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ActivityKind(str, Enum):
    NORMAL = "NORMAL"
    LOCATION_REQUIRED = "LOCATION_REQUIRED"
    QR_REQUIRED = "QR_REQUIRED"
    PHOTO_OR_FACE_REQUIRED = "PHOTO_OR_FACE_REQUIRED"
    GESTURE_OR_CODE_REQUIRED = "GESTURE_OR_CODE_REQUIRED"
    UNKNOWN = "UNKNOWN"


class ExecutionMode(str, Enum):
    AUTO_ALLOWED = "AUTO_ALLOWED"
    USER_VERIFICATION_REQUIRED = "USER_VERIFICATION_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


class ActivityState(str, Enum):
    DISCOVERED = "DISCOVERED"
    CLASSIFIED = "CLASSIFIED"
    READY = "READY"
    USER_ACTION_REQUIRED = "USER_ACTION_REQUIRED"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    VERIFYING = "VERIFYING"
    CONFIRMED_SUCCESS = "CONFIRMED_SUCCESS"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_TERMINAL = "FAILED_TERMINAL"
    UNKNOWN = "UNKNOWN"


class TransportOutcome(str, Enum):
    OK = "OK"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ParseOutcome(str, Enum):
    OK = "OK"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class SemanticOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class CourseIdentity:
    account_id: str
    course_id: str
    class_id: str
    course_name: str = ""
    teacher_name: str | None = None

    @property
    def key(self) -> str:
        return f"{self.account_id}:{self.course_id}:{self.class_id}"


@dataclass(frozen=True, slots=True)
class ActivityIdentity:
    account_id: str
    course_id: str
    class_id: str
    activity_id: str
    acquisition_surface: str

    @property
    def key(self) -> str:
        return ":".join(
            (
                self.account_id,
                self.course_id,
                self.class_id,
                self.activity_id,
            )
        )


@dataclass(slots=True)
class Activity:
    identity: ActivityIdentity
    kind: ActivityKind
    status: str = "active"
    start_time: str | None = None
    end_time: str | None = None
    verification_requirements: tuple[str, ...] = ()
    raw_fingerprint: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SignPlan:
    activity: ActivityIdentity
    mode: ExecutionMode
    kind: ActivityKind
    reason: str


@dataclass(frozen=True, slots=True)
class ActionResult:
    transport: TransportOutcome
    parse: ParseOutcome
    semantic: SemanticOutcome
    detail: str = ""

    @property
    def semantically_accepted(self) -> bool:
        return (
            self.transport is TransportOutcome.OK
            and self.parse is ParseOutcome.OK
            and self.semantic is SemanticOutcome.ACCEPTED
        )
