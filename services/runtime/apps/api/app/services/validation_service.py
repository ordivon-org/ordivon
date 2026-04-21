"""Compatibility service facade for validation-period workflows."""

from capabilities.boundary import ActionContext
from capabilities.validation import ValidationCapability


class ValidationService:
    _capability = ValidationCapability()

    @classmethod
    def get_summary(cls, usage_service, issue_repo):
        return cls._capability.get_summary(usage_service, issue_repo)

    @classmethod
    def sync_usage(cls, usage_service, action_context: ActionContext):
        return cls._capability.sync_usage(usage_service, action_context)

    @classmethod
    def report_issue(cls, issue_service, severity: str, area: str, description: str, action_context: ActionContext):
        return cls._capability.report_issue(
            issue_service=issue_service,
            severity=severity,
            area=area,
            description=description,
            action_context=action_context,
        )
