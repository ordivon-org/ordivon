"""Governance result — unified output for all Ordivon governance tools."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional


STATUSES = ("PASS", "PASS_WITH_WARNINGS", "DEGRADED", "BLOCKING")
AUTHORITY_IMPACTS = ("none", "supporting_evidence", "current_status", "source_of_truth_candidate", "policy_candidate")
PROMOTION_IMPACTS = ("none", "p1", "p2", "p3_plus")


class GovernanceResult:
    """Unified result from a governance tool execution."""

    def __init__(
        self,
        tool: str,
        status: str = "PASS",
        run_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        summary: str = "",
        exit_code: int = 0,
        command: str = "",
        started_at: Optional[str] = None,
        duration_ms: int = 0,
    ):
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {STATUSES}")
        self.tool = tool
        self.status = status
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self.trace_id = trace_id or ""
        self.summary = summary
        self.exit_code = exit_code
        self.command = command
        self.started_at = started_at or datetime.now(timezone.utc).isoformat()
        self.duration_ms = duration_ms
        self.findings: list[dict] = []
        self.evidence: list[dict] = []
        self.known_gaps: list[dict] = []
        self.authority_impact = "none"
        self.promotion_impact = "none"

    def add_finding(
        self, finding_id: str, severity: str, description: str, affected_surface: str = "", evidence_ref: str = ""
    ):
        self.findings.append({
            "finding_id": finding_id,
            "severity": severity,
            "description": description,
            "affected_surface": affected_surface,
            "evidence_ref": evidence_ref,
        })
        if severity == "BLOCKING":
            self.status = "BLOCKING"
        elif severity == "DEGRADED" and self.status not in ("BLOCKING",):
            self.status = "DEGRADED"
        elif severity == "WARN" and self.status not in ("BLOCKING", "DEGRADED"):
            self.status = "PASS_WITH_WARNINGS"

    def add_evidence(self, evidence_id: str, path: str, sha256: str = "", command: str = ""):
        self.evidence.append({"evidence_id": evidence_id, "path": path, "sha256": sha256, "command": command})

    def add_gap(self, gap_id: str, description: str, severity: str = "WARN", resolution: str = ""):
        self.known_gaps.append({
            "gap_id": gap_id,
            "description": description,
            "severity": severity,
            "resolution": resolution,
        })
        if severity in ("WARN", "DEGRADED") and self.status == "PASS":
            self.status = "PASS_WITH_WARNINGS"

    def to_dict(self) -> dict:
        return {
            "tool": self.tool,
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "status": self.status,
            "summary": self.summary,
            "findings": self.findings,
            "evidence": self.evidence,
            "known_gaps": self.known_gaps,
            "authority_impact": self.authority_impact,
            "promotion_impact": self.promotion_impact,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "command": self.command,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def emit(self, output_json: bool = False):
        """Emit result to stdout. Use --json flag for structured output."""
        if output_json:
            print(self.to_json())
        else:
            print(f"[{self.tool}] {self.status}")
            if self.summary:
                print(f"  {self.summary}")
            for f in self.findings:
                print(f"  [{f['severity']}] {f['finding_id']}: {f['description']}")
            for g in self.known_gaps:
                print(f"  [{g['severity']}] {g['gap_id']}: {g['description']}")

    def exit(self) -> int:
        """Return appropriate exit code: 0 for PASS/PASS_WITH_WARNINGS, 1 otherwise."""
        return 0 if self.status in ("PASS", "PASS_WITH_WARNINGS") else 1
