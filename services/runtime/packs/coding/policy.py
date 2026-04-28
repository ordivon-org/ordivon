"""Coding Pack discipline policy — validates coding decision intakes.

All gates return reasons with .severity (reject/escalate) per ADR-006
severity protocol.  Core RiskEngine never sees these reason types — it only
reads reason.severity and reason.message.
"""

from __future__ import annotations


# ── Reason types (ADR-006 severity protocol) ────────────────────────


class CodingRejectReason:
    """A hard rejection reason — the intake must be blocked."""

    def __init__(self, message: str) -> None:
        self.message = message
        self.severity = "reject"


class CodingEscalateReason:
    """An escalation reason — human review is required."""

    def __init__(self, message: str) -> None:
        self.message = message
        self.severity = "escalate"


# ── Forbidden file paths ────────────────────────────────────────────

_FORBIDDEN_PATH_PATTERNS: tuple[str, ...] = (
    ".env",
    "secrets",
    "private_key",
    "private key",
    "state/db/migrations/runner.py",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "pnpm-lock.yaml",
)


# ── Policy ───────────────────────────────────────────────────────────


class CodingDisciplinePolicy:
    """Validates coding decision intakes against discipline rules.

    Gate structure (per PFIOS governance model):
      Gate 1 — task_description must be present
      Gate 2 — file_paths must be non-empty
      Gate 3 — no forbidden file paths
      Gate 4 — high impact → escalate
      Gate 5 — missing test_plan → escalate
    """

    def validate_fields(self, payload: dict) -> list[CodingRejectReason | CodingEscalateReason]:
        """Gate 1: field existence checks."""
        reasons: list[CodingRejectReason | CodingEscalateReason] = []

        task = (payload.get("task_description") or "").strip()
        if not task:
            reasons.append(CodingRejectReason("Missing required field: task_description."))

        file_paths = payload.get("file_paths")
        if not file_paths or (isinstance(file_paths, (list, tuple)) and len(file_paths) == 0):
            reasons.append(CodingRejectReason("Missing required field: file_paths."))

        return reasons

    def validate_numeric(self, payload: dict) -> list[CodingRejectReason]:
        """Gate 2: numeric/structural checks (no numeric fields in coding pack)."""
        return []

    def validate_limits(self, payload: dict) -> list[CodingRejectReason]:
        """Gate 3: forbidden file path checks."""
        reasons: list[CodingRejectReason] = []

        file_paths = payload.get("file_paths", [])
        if isinstance(file_paths, (list, tuple)):
            for fp in file_paths:
                fp_lower = str(fp).lower()
                for forbidden in _FORBIDDEN_PATH_PATTERNS:
                    if forbidden in fp_lower:
                        reasons.append(
                            CodingRejectReason(f"Forbidden file path: '{fp}' matches protected pattern '{forbidden}'.")
                        )
                        break  # one reason per file

        return reasons

    def validate_behavioral(self, payload: dict) -> list[CodingEscalateReason]:
        """Gates 4-5: impact level and test plan checks."""
        reasons: list[CodingEscalateReason] = []

        impact = (payload.get("estimated_impact") or "").strip().lower()
        if impact == "high":
            reasons.append(CodingEscalateReason("estimated_impact='high' — requires human review before code changes."))

        test_plan = payload.get("test_plan")
        if not test_plan or not str(test_plan).strip():
            reasons.append(
                CodingEscalateReason("Missing test_plan — code changes without a test plan require human review.")
            )

        return reasons
