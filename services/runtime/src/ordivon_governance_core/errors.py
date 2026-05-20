"""Governance errors — structured error types for governance operations."""

from __future__ import annotations


class GovernanceError(Exception):
    """Base governance error."""

    def __init__(self, message: str, error_code: str = "GOV_ERR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class RegistryWriteError(GovernanceError):
    """Registry write operation failed."""

    def __init__(self, message: str, path: str = ""):
        super().__init__(message, "REGISTRY_WRITE_ERR")
        self.path = path


class AdmissionError(GovernanceError):
    """Admission validation failed."""

    def __init__(self, message: str, errors: list[str] = None):
        super().__init__(message, "ADMISSION_ERR")
        self.errors = errors or []


class EvidenceIntegrityError(GovernanceError):
    """Evidence hash mismatch or missing evidence."""

    def __init__(self, message: str, evidence_id: str = ""):
        super().__init__(message, "EVIDENCE_INTEGRITY_ERR")
        self.evidence_id = evidence_id


class IdempotencyConflictError(GovernanceError):
    """Idempotent request with different input conflicts with prior result."""

    def __init__(self, message: str, submission_id: str = ""):
        super().__init__(message, "IDEMPOTENCY_CONFLICT")
        self.submission_id = submission_id


class CheckNotFoundError(GovernanceError):
    """A required governance check or checker was not found."""

    def __init__(self, message: str, check_id: str = ""):
        super().__init__(message, "CHECK_NOT_FOUND")
        self.check_id = check_id
