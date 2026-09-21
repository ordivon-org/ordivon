"""Chaoxing auto-sign assistant MVP core."""

from .engine import AutoSignEngine
from .ledger import ActivityLedger
from .models import (
    Activity,
    ActivityIdentity,
    ActivityKind,
    ActivityState,
    CourseIdentity,
    ExecutionMode,
    SignPlan,
)

__all__ = [
    "Activity",
    "ActivityIdentity",
    "ActivityKind",
    "ActivityLedger",
    "ActivityState",
    "AutoSignEngine",
    "CourseIdentity",
    "ExecutionMode",
    "SignPlan",
]
