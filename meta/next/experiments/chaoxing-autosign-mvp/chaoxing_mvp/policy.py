from __future__ import annotations

from .models import Activity, ActivityKind, ExecutionMode, SignPlan


class SignPlanner:
    """Classifies an activity into an execution path.

    Safe default: only a NORMAL activity without extra verification requirements is
    eligible for an automatic submission adapter. Presence-proofed or unknown flows
    require explicit user action / remain unsupported.
    """

    def plan(self, activity: Activity) -> SignPlan:
        if activity.status.lower() not in {"active", "pending", "open"}:
            return SignPlan(
                activity=activity.identity,
                mode=ExecutionMode.UNSUPPORTED,
                kind=activity.kind,
                reason=f"activity status is {activity.status!r}",
            )

        if activity.kind is ActivityKind.NORMAL and not activity.verification_requirements:
            return SignPlan(
                activity=activity.identity,
                mode=ExecutionMode.AUTO_ALLOWED,
                kind=activity.kind,
                reason="ordinary activity without additional verification requirements",
            )

        if activity.kind in {
            ActivityKind.LOCATION_REQUIRED,
            ActivityKind.QR_REQUIRED,
            ActivityKind.PHOTO_OR_FACE_REQUIRED,
            ActivityKind.GESTURE_OR_CODE_REQUIRED,
        }:
            return SignPlan(
                activity=activity.identity,
                mode=ExecutionMode.USER_VERIFICATION_REQUIRED,
                kind=activity.kind,
                reason="activity requires user-provided presence/verification context",
            )

        return SignPlan(
            activity=activity.identity,
            mode=ExecutionMode.UNSUPPORTED,
            kind=activity.kind,
            reason="unknown or unsupported activity kind",
        )
