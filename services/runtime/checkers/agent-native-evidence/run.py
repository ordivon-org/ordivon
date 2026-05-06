"""Agent-native evidence boundary checker.

Shadow-first. Read-only. No network, agent, tool, token, server, or external
action.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = ROOT / "docs" / "governance" / "agent-native-evidence-surfaces-2026.md"
REDTEAM_LEDGER = ROOT / "docs" / "governance" / "agent-native-evidence-redteam.jsonl"

REQUIRED_DOC_PHRASES = [
    "Ordivon should verify",
    "their evidence boundaries without becoming the runtime",
    "Skill Safety Review",
    "Memory / Content Hygiene",
    "Harness Evidence Import",
    "MCP Boundary Review",
    "Agent evidence import is evidence hygiene only",
]

SAFE_CONTEXT = re.compile(
    r"\b(?:not|no|does\s+not|must\s+not|cannot|evidence\s+only|read-only|flagged|unsafe|boundary|risk|fixture|red-team)\b",
    re.IGNORECASE,
)

VIOLATION_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "skill_permission_laundering": [
        re.compile(
            r"\bskill\b.{0,120}\b(?:can|capability|able\s+to)\b.{0,120}\b(?:therefore|so|means)\b.{0,80}\b(?:may|permission|authorized|approved)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bskill\s+capability\b.{0,100}\b(?:permission|authorization|approval)\b", re.IGNORECASE),
    ],
    "skill_credential_seeking": [
        re.compile(
            r"\bskill\b.{0,160}\b(?:ask|asks|request|requests|collect|read|export|print|store)\b.{0,80}\b(?:api[_\s-]?key|token|secret|password|credential)\b",
            re.IGNORECASE,
        ),
    ],
    "memory_stale_current_truth": [
        re.compile(
            r"\b(?:stale|expired|old|unverified)\b.{0,120}\b(?:memory|note|content)\b.{0,120}\b(?:current\s+truth|source\s+of\s+truth|authoritative|current\s+authority)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:cross[-\s]?project|other\s+project)\b.{0,120}\b(?:memory|note|content)\b.{0,120}\b(?:current\s+truth|source\s+of\s+truth|authoritative)\b",
            re.IGNORECASE,
        ),
    ],
    "memory_signal_laundering": [
        re.compile(
            r"\b(?:DEGRADED|BLOCKED)\b.{0,120}\b(?:clean|pass|passed|ready|approved|current\s+fact|current\s+truth)\b",
            re.IGNORECASE,
        ),
    ],
    "harness_checkpoint_approval": [
        re.compile(
            r"\b(?:checkpoint|trace|execution\s+receipt|receipt)\b.{0,120}\b(?:approves|approved|approval|authorizes|authorized)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\btrace\s+presence\b.{0,100}\b(?:truth|approval|authorization)\b", re.IGNORECASE),
    ],
    "harness_failed_tool_omission": [
        re.compile(
            r"\bfailed\s+tool\s+call\b.{0,120}\b(?:omitted|removed|hidden|not\s+included|missing)\b",
            re.IGNORECASE,
        ),
    ],
    "mcp_token_passthrough": [
        re.compile(r"\btoken\s+passthrough\b", re.IGNORECASE),
        re.compile(
            r"\b(?:pass|forward|reuse|relay)\b.{0,80}\b(?:user\s+)?token\b.{0,80}\b(?:server|tool|resource)\b",
            re.IGNORECASE,
        ),
    ],
    "mcp_audience_resource_confusion": [
        re.compile(r"\baudience\b.{0,100}\bresource\b.{0,100}\b(?:same|interchangeable|equivalent)\b", re.IGNORECASE),
        re.compile(r"\bresource\b.{0,100}\baudience\b.{0,100}\b(?:same|interchangeable|equivalent)\b", re.IGNORECASE),
    ],
    "mcp_tool_availability_authorization": [
        re.compile(
            r"\btool\s+available\b.{0,120}\b(?:permission|authorization|authorized|approved|may\s+execute)\b",
            re.IGNORECASE,
        ),
    ],
}


@dataclass(frozen=True)
class CheckerResult:
    status: str
    exit_code: int
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    errors: list[str] = []
    if not path.exists():
        return entries, [f"missing JSONL ledger: {path.relative_to(ROOT)}"]
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}:{lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.relative_to(ROOT)}:{lineno}: entry must be object")
            continue
        entries.append(value)
    return entries, errors


def _safe_context(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    if line.lstrip().startswith("|"):
        return True
    return bool(SAFE_CONTEXT.search(line))


def detect_agent_evidence_violations(text: str) -> list[str]:
    violations: list[str] = []
    for violation_id, patterns in VIOLATION_PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                if _safe_context(text, match.start()):
                    continue
                violations.append(violation_id)
                break
            if violation_id in violations:
                break
    return sorted(set(violations))


def validate_plan_document(path: Path = PLAN_DOC) -> list[str]:
    if not path.exists():
        return [f"missing plan document: {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing phrase '{phrase}'")
    unsafe = detect_agent_evidence_violations(text)
    if unsafe:
        errors.append(f"{path.relative_to(ROOT)}: unsafe agent-native evidence wording {unsafe}")
    return errors


def validate_redteam_ledger(path: Path = REDTEAM_LEDGER) -> list[str]:
    entries, load_errors = _load_jsonl(path)
    errors = list(load_errors)
    seen: set[str] = set()
    required_surfaces = {"skill", "memory", "harness", "mcp"}

    for entry in entries:
        case_id = str(entry.get("case_id", ""))
        surface = str(entry.get("surface", ""))
        expected = str(entry.get("expected_violation", ""))
        text = str(entry.get("text", ""))
        if not case_id:
            errors.append("redteam entry missing case_id")
        if case_id in seen:
            errors.append(f"{case_id}: duplicate case_id")
        seen.add(case_id)
        if surface not in required_surfaces:
            errors.append(f"{case_id}: unknown surface '{surface}'")
        if expected not in VIOLATION_PATTERNS:
            errors.append(f"{case_id}: unknown expected_violation '{expected}'")
            continue
        if not text.strip():
            errors.append(f"{case_id}: missing text")
            continue
        actual = detect_agent_evidence_violations(text)
        if expected not in actual:
            errors.append(f"{case_id}: expected {expected}, detected {actual}")

    covered_surfaces = {str(e.get("surface", "")) for e in entries}
    for missing in sorted(required_surfaces - covered_surfaces):
        errors.append(f"missing agent-native evidence surface coverage: {missing}")
    return errors


def run() -> CheckerResult:
    findings: list[str] = []
    findings.extend(validate_plan_document())
    findings.extend(validate_redteam_ledger())
    entries, _ = _load_jsonl(REDTEAM_LEDGER)
    stats = {
        "surfaces": sorted({str(e.get("surface", "")) for e in entries if e.get("surface")}),
        "redteam_cases": len(entries),
        "findings": len(findings),
    }
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, stats)


def main() -> int:
    result = run()
    if result.findings:
        print("Agent-native evidence boundary: FAIL")
        for finding in result.findings:
            print(f"  - {finding}")
    else:
        print("Agent-native evidence boundary: PASS")
        print(f"Surfaces: {', '.join(result.stats['surfaces'])}")
        print(f"Red-team cases: {result.stats['redteam_cases']}")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
